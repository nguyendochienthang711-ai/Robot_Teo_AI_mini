"""
FastMCP server exposing Teo 3D Robot upper-body gestures, 3-Wheel Omni Kiwi Drive controls,
and Runtime & Evaluation Harness inspection tools to external IDEs and AI agents.
Delegates directly to tools.system and teo_harness for unified clamping, HMAC-SHA256 UDP sync,
and deterministic evaluation (R-11).
"""

import asyncio
import json

from fastmcp import FastMCP

import config
from teo_harness import (
    BASELINE_CACHE_FINGERPRINT,
    LCD_EYE_PROFILES,
    run_deterministic_eval_suite,
    state_machine,
)
from tools.common import load_json
from tools.system import tool_di_chuyen_da_huong_omni, tool_dieu_khien_co_the_teo

mcp = FastMCP("TeoRobotMotionController")


@mcp.tool
def dieu_khien_co_the_teo(
    hanh_dong: str,
    so_giay: float = 3.5,
    bpm: int = 125,
) -> str:
    """Execute upper-body gesture or dance bundle: wave_greeting, nod_yes, shake_no, look_around, happy_dance, moonwalk_dance, idle."""
    return tool_dieu_khien_co_the_teo(
        {"hanh_dong": hanh_dong, "so_giay": so_giay, "bpm": bpm}
    )


@mcp.tool
def di_chuyen_da_huong_omni(
    huong_di: str,
    so_giay: float = 2.0,
) -> str:
    """Navigate 3-wheel Omni Kiwi Drive base on desk (0.5-3.0s): move_forward, move_backward, slide_left, slide_right, circle_strafe, spin_around, idle."""
    return tool_di_chuyen_da_huong_omni(
        {"huong_di": huong_di, "so_giay": so_giay}
    )


@mcp.tool
def xem_trang_thai_harness_teo() -> str:
    """Inspect Teo Agent Runtime Harness status: current AI state, ST7789 LCD eye expression, Omni wheel lock, pending HITL confirmation, active timers, and prompt cache fingerprint."""
    snap = state_machine.get_snapshot()
    timers = load_json(config.TIMERS_FILE, [])
    recent_audits = []
    if config.AUDIT_LOG_FILE.exists():
        try:
            lines = config.AUDIT_LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
            for ln in lines[-5:]:
                if ln.strip():
                    recent_audits.append(json.loads(ln))
        except Exception:
            pass
    report = {
        "agent_state": snap,
        "prompt_cache_fingerprint": BASELINE_CACHE_FINGERPRINT,
        "active_timers_count": len(timers) if isinstance(timers, list) else 0,
        "recent_tool_audits": recent_audits,
    }
    return json.dumps(report, ensure_ascii=False, indent=2)


@mcp.tool
def dong_bo_trang_thai_ai_teo(
    trang_thai: str,
    chi_tiet: str = "mcp_manual_sync",
) -> str:
    """Set Teo AI State Machine state (IDLE, LISTENING, THINKING, HITL_CONFIRM, SPEAKING, ALERT) and broadcast signed HMAC packet to update ST7789 LCD eyes and arm posture."""
    st = (trang_thai or "").strip().upper()
    if st not in LCD_EYE_PROFILES:
        valid_str = ", ".join(LCD_EYE_PROFILES.keys())
        return f"ERROR invalid_state: '{trang_thai}'. Valid states: {valid_str}"
    entry = state_machine.set_state(st, detail=chi_tiet)
    return json.dumps(entry, ensure_ascii=False)


@mcp.tool
def chay_kiem_thu_harness_teo() -> str:
    """Run the 8-scenario offline deterministic evaluation suite for Teo's brain.py and runtime harness (0 API tokens, <2s)."""
    summary = asyncio.run(run_deterministic_eval_suite(verbose=False))
    return json.dumps(summary, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
