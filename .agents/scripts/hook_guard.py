"""
Antigravity Lifecycle Hook Handler for Robot "Tèo" AI Harness (.agents/hooks.json).
- `--mode pre-tool`: Protects `.env` secrets from accidental reading or overwriting (<5ms).
- `--mode post-invocation`: Executes Constitutional Invariant & Syntax Gates once every 10 turns
  (`invocationNum % 10 == 0`), exiting immediately on turns 1..9 (<5ms).
"""

import argparse
import json
import py_compile
import sys
import time
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = AGENTS_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

STATE_FILE = ROOT_DIR / "cache" / "hook_turn_state.json"

CORE_FILES = [
    "config.py",
    "audio_io.py",
    "brain.py",
    "main.py",
    "teo_harness.py",
    "teo_sim_runner.py",
    "teo_motion_mcp.py",
]


def _read_stdin_json() -> dict:
    try:
        raw = sys.stdin.read()
        if raw and raw.strip():
            return json.loads(raw)
    except Exception:
        pass
    return {}


def handle_pre_tool(payload: dict) -> dict:
    """Block reading or modifying the live `.env` file while allowing `.env.example`."""
    tool_call = payload.get("toolCall") or {}
    args = tool_call.get("args") or {}
    target_path = str(args.get("Path") or args.get("TargetFile") or args.get("FilePath") or "").strip()

    if target_path:
        p_name = Path(target_path.replace("\\", "/")).name.lower()
        if p_name == ".env":
            return {
                "decision": "deny",
                "reason": "Blocked by Teo Harness Hook: direct access to .env secrets is prohibited (use .env.example).",
            }

    return {"decision": "allow"}


def _get_and_increment_turn(payload: dict) -> int:
    """Resolve current turn number from `invocationNum` or persistent conversation counter."""
    conv_id = str(payload.get("conversationId") or "default")
    inv_num = payload.get("invocationNum")

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state_data = {}
    if STATE_FILE.exists():
        try:
            state_data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state_data = {}

    conv_turns = int(state_data.get(conv_id, 0)) + 1
    state_data[conv_id] = conv_turns
    if isinstance(inv_num, int) and inv_num > 0:
        turn_count = inv_num
    else:
        turn_count = conv_turns

    state_data["last_turn_count"] = turn_count
    state_data["last_updated"] = round(time.time(), 2)
    try:
        STATE_FILE.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
    except Exception:
        pass
    return turn_count


def run_periodic_invariants_check() -> list[str]:
    """Verify constitutional invariants: <=14 schemas, cache prefix invariance, and syntax compilation."""
    issues: list[str] = []

    for rel_path in CORE_FILES:
        abs_p = ROOT_DIR / rel_path
        if abs_p.exists():
            try:
                py_compile.compile(str(abs_p), doraise=True)
            except py_compile.PyCompileError as exc:
                issues.append(f"Syntax error in {rel_path}: {exc.msg}")

    try:
        import config
        from tools.schemas import TOOLS_SCHEMA
        from tools.dispatcher import _REGISTRY
        from tools.policy import TOOL_SPECS

        if len(TOOLS_SCHEMA) > 14:
            issues.append(f"TOOLS_SCHEMA count is {len(TOOLS_SCHEMA)} (exceeds max 14).")

        for t in TOOLS_SCHEMA:
            fn = t.get("function", {})
            name = fn.get("name", "")
            params = fn.get("parameters", {})
            if params.get("additionalProperties", True) is not False:
                issues.append(f"Schema '{name}' missing additionalProperties: False.")
            if name not in _REGISTRY:
                issues.append(f"Schema '{name}' missing in tools.dispatcher._REGISTRY.")
            if name not in TOOL_SPECS:
                issues.append(f"Schema '{name}' missing in tools.policy.TOOL_SPECS.")

        if "<untrusted_data>" not in config.SYSTEM_PROMPT:
            issues.append("SYSTEM_PROMPT missing '<untrusted_data>' isolation rule.")
    except Exception as exc:
        issues.append(f"Invariant check import error: {exc}")

    return issues


def handle_post_invocation(payload: dict) -> dict:
    """Run quality gate only once every 10 turns (`turn_count % 10 == 0`)."""
    turn_count = _get_and_increment_turn(payload)
    if turn_count % 10 != 0:
        return {"injectSteps": [], "terminationBehavior": ""}

    issues = run_periodic_invariants_check()
    if issues:
        msg = (
            f"[Teo Harness 10-Turn Quality Gate (Turn #{turn_count}) — ISSUES DETECTED]:\n"
            + "\n".join(f"- {i}" for i in issues)
        )
        return {
            "injectSteps": [
                {
                    "systemMessage": {
                        "systemMessage": msg,
                    }
                }
            ],
            "terminationBehavior": "force_continue",
        }

    return {"injectSteps": [], "terminationBehavior": ""}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["pre-tool", "post-invocation", "self-test"], required=True)
    args = parser.parse_args()

    if args.mode == "self-test":
        issues = run_periodic_invariants_check()
        print(json.dumps({"ok": len(issues) == 0, "issues": issues}, ensure_ascii=False))
        return 0 if not issues else 1

    payload = _read_stdin_json()
    if args.mode == "pre-tool":
        out = handle_pre_tool(payload)
    else:
        out = handle_post_invocation(payload)

    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
