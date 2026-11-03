"""
Dispatcher: Maps tool function names to implementation handlers and executes tool calls.
Enforces strict fail-closed validation, lazy loading, and security policies (TL-02, TL-04, TL-14, TL-15).
"""

import importlib
import json
import logging
from typing import Any

from jsonschema import Draft202012Validator

from tools.policy import (
    MAX_CALLS_PER_TURN,
    TOOL_SPECS,
    ToolResult,
    TurnContext,
    audit_log,
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


def execute_tool_call(func_name: str, args_json: str, ctx: TurnContext | None = None) -> str:
    """Execute tool call with strict fail-closed validation, policy guardrails, and audit logging."""
    if ctx is None:
        ctx = TurnContext()

    # Rate limiting per turn (TL-04)
    ctx.calls += 1
    if ctx.calls > MAX_CALLS_PER_TURN:
        audit_log(func_name, {}, False, ctx.tainted, 0)
        return "ERROR rate_limit: maximum tool calls per turn exceeded."

    # Parse and reject invalid JSON / constants (TL-02)
    try:
        args = _parse_args(args_json)
    except ValueError as err:
        log.warning("JSON parse failure in %s: %s", func_name, err)
        audit_log(func_name, {}, False, ctx.tainted, 0)
        return "ERROR invalid_arguments: arguments were not valid JSON. Ask the user or retry once."

    # Validate against JSON schema (TL-02, TL-16)
    validator = _VALIDATORS.get(func_name)
    if validator:
        errors = sorted(validator.iter_errors(args), key=lambda e: list(e.path))
        if errors:
            e = errors[0]
            field_path = "/".join(map(str, e.path)) or "root"
            log.warning("Schema validation error in %s at %s: %s", func_name, field_path, e.message)
            audit_log(func_name, args, False, ctx.tainted, 0)
            return f"ERROR invalid_arguments: {field_path}: {e.message}"

    # Policy layer check for untrusted data / tainted turn (TL-04)
    spec = TOOL_SPECS.get(func_name)
    if ctx.tainted and spec and spec.risk in ("write", "destructive", "physical") and not ctx.confirmed:
        log.warning("Blocked action %s due to tainted context without confirmation", func_name)
        audit_log(func_name, args, False, ctx.tainted, 0)
        return "ERROR security_policy: untrusted data detected in this turn. Physical confirmation is required before executing this action."

    try:
        handler = _get_handler(func_name)
        if not handler:
            audit_log(func_name, args, False, ctx.tainted, 0)
            return f"ERROR unknown_tool: {func_name} does not exist."

        raw_result = handler(args)

        if isinstance(raw_result, ToolResult):
            if raw_result.tainted or (spec and spec.untrusted_output):
                ctx.tainted = True
            output_text = raw_result.text
            ok = raw_result.ok
        else:
            if spec and spec.untrusted_output:
                ctx.tainted = True
            output_text = str(raw_result)
            ok = not output_text.startswith("ERROR")

        audit_log(func_name, args, ok, ctx.tainted, len(output_text))
        return output_text

    except Exception as e:
        log.exception("Tool execution error in %s", func_name)
        audit_log(func_name, args, False, ctx.tainted, 0)
        # Never leak raw python traceback to LLM / spoken output (TL-15)
        return f"ERROR tool_failed: {func_name}. Tell the user briefly that it did not work."
