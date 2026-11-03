import json
import socket
from fastmcp import FastMCP

mcp = FastMCP("TeoRobotMotionController")

UDP_TARGET = ("127.0.0.1", 5555)

VALID_BODY_MOTIONS = {
    "wave_greeting",
    "nod_yes",
    "shake_no",
    "look_around",
    "happy_dance",
    "moonwalk_dance",
    "idle",
}

VALID_OMNI_MOVES = {
    "move_forward",
    "move_backward",
    "slide_left",
    "slide_right",
    "circle_strafe",
    "spin_around",
    "idle",
}


def _send_to_sim(motion: str, duration: float = 3.0, bpm: int = 120) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = json.dumps({"motion": motion, "duration": duration, "bpm": bpm}).encode("utf-8")
    sock.sendto(payload, UDP_TARGET)
    sock.close()
    return f"Đã kích hoạt chuyển động '{motion}' trong {duration} giây (BPM={bpm})."


@mcp.tool
def dieu_khien_co_the_teo(
    hanh_dong: str,
    so_giay: float = 3.5,
    bpm: int = 125,
) -> str:
    """Execute upper-body gesture or dance bundle: wave_greeting, nod_yes, shake_no, look_around, happy_dance, moonwalk_dance, idle."""
    if hanh_dong not in VALID_BODY_MOTIONS and hanh_dong not in VALID_OMNI_MOVES:
        hanh_dong = "wave_greeting"
    return _send_to_sim(hanh_dong, float(so_giay), int(bpm))


@mcp.tool
def di_chuyen_da_huong_omni(
    huong_di: str,
    so_giay: float = 2.0,
) -> str:
    """Navigate 3-wheel Omni Kiwi Drive base on desk (1-3s with 3 IR cliff sensors): move_forward, move_backward, slide_left, slide_right, circle_strafe, spin_around, idle."""
    if huong_di not in VALID_OMNI_MOVES:
        huong_di = "slide_left"
    clamped_sec = max(1.0, min(3.0, float(so_giay)))
    return _send_to_sim(huong_di, clamped_sec, 120)


if __name__ == "__main__":
    mcp.run()
