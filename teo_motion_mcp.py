"""
FastMCP server exposing Teo 3D Robot upper-body gestures and 3-Wheel Omni Kiwi Drive controls.
Delegates directly to tools.system for unified clamping and 2-way UDP ACK verification (R-11).
"""

from fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run()
