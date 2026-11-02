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
    nhip_nhac_bpm: int = 120
) -> str:
    """
    Điều khiển cơ thể 3D của robot Tèo thực hiện cử chỉ, nhảy theo nhạc hoặc di chuyển bánh xích.
    Các giá trị hợp lệ của 'goi_chuyen_dong':
    - 'wave_greeting': Vẫy tay chào và nghiêng đầu
    - 'happy_dance': Nhảy múa theo nhịp nhạc BPM (kết hợp cổ, 2 tay và bánh xích)
    - 'shake_no': Lắc đầu từ chối
    - 'move_forward': Tiến lên phía trước
    - 'move_backward': Lùi lại phía sau
    - 'spin_around': Xoay tròn tại chỗ
    - 'idle': Đứng yên nghỉ ngơi
    """
    valid_motions = {
        "wave_greeting", "happy_dance", "shake_no",
        "move_forward", "move_backward", "spin_around", "idle"
    }
    if goi_chuyen_dong not in valid_motions:
        goi_chuyen_dong = "wave_greeting"
    return _send_to_sim(goi_chuyen_dong, float(thoi_gian_giay), int(nhip_nhac_bpm))

if __name__ == "__main__":
    mcp.run()