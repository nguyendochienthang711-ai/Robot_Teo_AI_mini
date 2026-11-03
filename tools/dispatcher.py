"""
Dispatcher: Maps tool function names to implementation handlers and executes tool calls.
Enforces strict fail-closed validation, lazy loading, and security policies (TL-02, TL-04, TL-14, TL-15).

- run_tool(...)          -> ToolResult  (used by brain.py: honours speak/commit for direct TTS)
- execute_tool_call(...) -> str         (used by tests / MCP: commits immediately, returns text only)
"""

import importlib
import json
import logging
from typing import Any

from jsonschema import Draft202012Validator

from tools.guardrails import (
    check_tool_args_guardrail,
    describe_hitl_action,
    set_pending_action,
)
from tools.policy import (
    MAX_CALLS_PER_TURN,
    TOOL_SPECS,
    ToolResult,
    TurnContext,
    audit_log,
    risk_of,
)
from tools.schemas import TOOLS_SCHEMA

log = logging.getLogger("teo.dispatcher")

_VALIDATORS = {
    t["function"]["name"]: Draft202012Validator(t["function"]["parameters"])
    for t in TOOLS_SCHEMA
}

_REGISTRY = {
    "quan_ly_cong_viec": ("tools.secretary", "tool_quan_ly_cong_viec"),
    "dong_ho_tap_trung_pomodoro": ("tools.secretary", "tool_dong_ho_tap_trung_pomodoro"),
    "kiem_tra_suc_khoe_laptop": ("tools.system", "tool_kiem_tra_suc_khoe_laptop"),
    "doi_giong_noi_teo": ("tools.system", "tool_doi_giong_noi_teo"),
    "dieu_khien_co_the_teo": ("tools.system", "tool_dieu_khien_co_the_teo"),
    "di_chuyen_da_huong_omni": ("tools.system", "tool_di_chuyen_da_huong_omni"),
    "doc_va_tom_tat_tai_lieu": ("tools.documents", "tool_doc_va_tom_tat_tai_lieu"),
    "xu_ly_bo_nho_tam_clipboard": ("tools.documents", "tool_xu_ly_bo_nho_tam_clipboard"),
    "ghi_nho_thong_tin_dai_han": ("tools.documents", "tool_ghi_nho_thong_tin_dai_han"),
    "phat_nhac_va_dieu_khien_media": ("tools.media", "tool_phat_nhac_va_dieu_khien_media"),
    "nhin_man_hinh_laptop": ("tools.vision", "tool_nhin_man_hinh_laptop"),
    "tra_cuu_thong_tin_truc_tuyen": ("tools.search", "tool_tra_cuu_thong_tin_truc_tuyen"),
}


def _reject_constant(c: Any) -> None:
    raise ValueError(f"invalid JSON constant: {c}")


def _parse_args(args_json: str) -> dict:
    if not args_json or not args_json.strip():
        return {}
    args = json.loads(args_json, parse_constant=_reject_constant)
    if not isinstance(args, dict):
        raise ValueError("arguments must be a JSON object")
    return args


def _get_handler(name: str):
    if name not in _REGISTRY:
        return None
    mod_name, fn_name = _REGISTRY[name]
    mod = importlib.import_module(mod_name)
    return getattr(mod, fn_name)


def _fail(func_name: str, args: dict, ctx: TurnContext, text: str) -> ToolResult:
    audit_log(func_name, args, False, ctx.tainted, 0)
    return ToolResult(text=text, ok=False)


def run_tool(func_name: str, args_json: str, ctx: TurnContext | None = None) -> ToolResult:
    """Validate, apply policy, execute and audit a tool call. Returns a ToolResult."""
    if ctx is None:
        ctx = TurnContext()

    # Rate limiting per turn (TL-04)
    ctx.calls += 1
    if ctx.calls > MAX_CALLS_PER_TURN:
        return _fail(func_name, {}, ctx, "ERROR rate_limit: maximum tool calls per turn exceeded.")

    # Parse and reject invalid JSON / constants (TL-02)
    try:
        args = _parse_args(args_json)
    except ValueError as err:
        log.warning("JSON parse failure in %s: %s", func_name, err)
        return _fail(func_name, {}, ctx,
                     "ERROR invalid_arguments: arguments were not valid JSON. Ask the user or retry once.")

    if func_name not in _REGISTRY:
        return _fail(func_name, args, ctx, f"ERROR unknown_tool: {func_name} does not exist.")

    # Validate against JSON schema (TL-02, TL-16)
    validator = _VALIDATORS.get(func_name)
    if validator:
        errors = sorted(validator.iter_errors(args), key=lambda e: list(e.path))
        if errors:
            e = errors[0]
            field_path = "/".join(map(str, e.path)) or "root"
            log.warning("Schema validation error in %s at %s: %s", func_name, field_path, e.message)
            return _fail(func_name, args, ctx, f"ERROR invalid_arguments: {field_path}: {e.message}")

    # Rule & Regex Tool-Arguments Guardrail (blocks shell payloads in clipboard & memory poisoning)
    args_ok, args_reason = check_tool_args_guardrail(func_name, args)
    if not args_ok:
        return _fail(func_name, args, ctx, args_reason)

    # Policy: block side-effect tools after untrusted data in the same turn (TL-04)
    risk = risk_of(func_name, args)
    if ctx.tainted and risk in ("write", "destructive", "physical") and not ctx.confirmed:
        log.warning("Blocked %s (%s) in tainted turn without confirmation", func_name, risk)
        return _fail(func_name, args, ctx,
                     "ERROR security_policy: untrusted data was read in this turn. "
                     "Ask the user to confirm physically before this action.")

    # Human-in-the-Loop (HITL) gate for sensitive laptop data operations
    if ctx.require_hitl and not ctx.confirmed:
        hitl_desc = describe_hitl_action(func_name, args)
        if hitl_desc:
            set_pending_action(func_name, json.dumps(args, ensure_ascii=False), hitl_desc)
            log.info("HITL confirmation requested for %s: %s", func_name, hitl_desc)
            audit_log(func_name, args, True, ctx.tainted, 0)
            return ToolResult(
                text=(
                    f"PENDING_HITL_CONFIRMATION: Thao tác '{hitl_desc}' cần sếp cho phép. "
                    f"Hãy hỏi ngắn gọn: 'Sếp có đồng ý cho em {hitl_desc} không?' và chờ sếp trả lời OK hoặc Đồng ý."
                ),
                ok=True,
            )

    spec = TOOL_SPECS.get(func_name)
    try:
        raw = _get_handler(func_name)(args)
    except ImportError as e:
        log.exception("Tool %s unavailable", func_name)
        return _fail(func_name, args, ctx, f"ERROR tool_unavailable: missing dependency ({e.name}).")
    except Exception:
        log.exception("Tool execution error in %s", func_name)
        # Never leak raw python traceback to LLM / spoken output (TL-15)
        return _fail(func_name, args, ctx,
                     f"ERROR tool_failed: {func_name}. Tell the user briefly that it did not work.")

    result = raw if isinstance(raw, ToolResult) else ToolResult(text=str(raw))
    if not isinstance(raw, ToolResult):
        result.ok = not result.text.startswith("ERROR")
    if result.tainted or (spec and spec.untrusted_output and risk == "read"):
        result.tainted = True
        ctx.tainted = True

    audit_log(func_name, args, result.ok, ctx.tainted, len(result.text))
    return result


def execute_tool_call(func_name: str, args_json: str, ctx: TurnContext | None = None) -> str:
    """Text-only wrapper (tests, MCP). Without a TTS pipeline, pending commits run immediately."""
    result = run_tool(func_name, args_json, ctx)
    if result.commit:
        try:
            result.commit()
        except Exception:
            log.exception("Commit callback failed for %s", func_name)
    return result.text
