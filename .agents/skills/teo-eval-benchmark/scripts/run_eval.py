"""
Helper runner for the Teo Evaluation & Benchmark Skill.
Supports offline deterministic replay, --live DeepSeek benchmark, and --full unit/integration test suite.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config


def print_recent_traces(limit: int = 5) -> None:
    trace_file = config.TRACE_LOG_FILE
    if not trace_file.exists():
        print("ℹ️ No agent trace log found yet at logs/agent_traces.jsonl.")
        return
    lines = [ln.strip() for ln in trace_file.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    recent = lines[-limit:]
    print(f"\n📊 [RECENT AGENT TRACES ({len(recent)} of {len(lines)} turns)]:")
    for raw in recent:
        try:
            rec = json.loads(raw)
            print(
                f"  - {rec.get('turn_id')}: states={rec.get('state_transitions')} | "
                f"tools={[t.get('name') for t in rec.get('tool_calls', [])]} | "
                f"cache_ok={rec.get('cache_invariant_ok')} | total={rec.get('total_ms')}ms"
            )
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Teo Agent Evaluation & Regression Suite")
    parser.add_argument("--live", action="store_true", help="Run live DeepSeek API benchmark")
    parser.add_argument("--full", action="store_true", help="Run all unit/integration tests + eval suite + trace summary")
    args = parser.parse_args()

    py_exe = sys.executable

    if args.full:
        print("🔍 [1/3] Running Tool Schema & Policy Validator...")
        v_cmd = [py_exe, str(ROOT_DIR / ".agents/skills/teo-tool-builder/scripts/validate_tools.py")]
        if subprocess.call(v_cmd, cwd=str(ROOT_DIR)) != 0:
            return 1

        print("\n🧪 [2/3] Running Unit, Simulation & Harness Regression Tests...")
        u_cmd = [
            py_exe,
            "-m",
            "unittest",
            "test_tools.py",
            "test_sim_integration.py",
            "test_agent_harness.py",
        ]
        if subprocess.call(u_cmd, cwd=str(ROOT_DIR)) != 0:
            return 1

    print("\n⚡ [Running Teo Agent Evaluation Suite]...")
    h_cmd = [py_exe, str(ROOT_DIR / "teo_harness.py")]
    if args.live:
        h_cmd.append("--live")
    rc = subprocess.call(h_cmd, cwd=str(ROOT_DIR))
    if args.full:
        print_recent_traces()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
