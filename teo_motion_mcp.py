import json
import socket
from fastmcp import FastMCP

# Khởi tạo máy chủ MCP cho Robot Tèo (strict_input_validation=False là mặc định)
mcp = FastMCP("TeoRobotMotionController")

UDP_TARGET = ("127.0.0.1", 5555)


def _send_to_sim(motion: str, duration: float = 3.0, bpm: int = 120) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = json.dumps({"motion": motion, "duration": duration, "bpm": bpm}).encode("utf-8")
    sock.sendto(payload, UDP_TARGET)
    sock.close()
    return f"Đã kích hoạt gói chuyển động '{motion}' trong {duration} giây (BPM={bpm})."


@mcp.tool
def thuc_hien_cu_chi_teo(
    goi_chuyen_dong: str,
    thoi_gian_giay: float = 3.5,
    nhip_nhac_bpm: int = 120,
) -> str:
    """Execute 3D motion bundle for Teo robot: wave_greeting, nod_yes, shake_no, look_around, happy_dance, move_forward, move_backward, spin_around, idle."""
    valid_motions = {
        "wave_greeting",
        "nod_yes",
        "shake_no",
        "look_around",
        "happy_dance",
        "move_forward",
        "move_backward",
        "spin_around",
        "idle",
    }
    if goi_chuyen_dong not in valid_motions:
        goi_chuyen_dong = "wave_greeting"
    return _send_to_sim(goi_chuyen_dong, float(thoi_gian_giay), int(nhip_nhac_bpm))


if __name__ == "__main__":
    mcp.run()
