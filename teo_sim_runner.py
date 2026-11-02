import json
import math
import os
import socket
import time
import mujoco
import mujoco.viewer

# Mở socket UDP không chặn (non-blocking) để nhận lệnh từ FastMCP
UDP_IP = "127.0.0.1"
UDP_PORT = 5555
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

# Trạng thái Motion Bundle hiện tại
current_state = {
    "motion": "idle",
    "bpm": 120,
    "end_time": 0.0,
}

def apply_motion_bundle(data, t: float, state: dict):
    """Giải mã tên gói Motion Bundle thành xung điều khiển mượt cho 3 Servo + 2 Bánh xích."""
    motion = state["motion"]
    bpm = max(60, min(200, state.get("bpm", 120)))
    freq = bpm / 60.0  # Số nhịp mỗi giây (Hz)
    omega = 2.0 * math.pi * freq

    # Reset mặc định
    neck, l_arm, r_arm, l_wheel, r_wheel = 0.0, 0.0, 0.0, 0.0, 0.0

    if time.time() > state["end_time"]:
        state["motion"] = "idle"
        motion = "idle"

    if motion == "idle":
        # Thở nhẹ tự nhiên
        l_arm = 0.08 * math.sin(2.0 * t)
        r_arm = 0.08 * math.sin(2.0 * t)

    elif motion == "wave_greeting":
        # Vẫy tay phải chào và nghiêng nhẹ đầu
        neck = 0.35 * math.sin(4.0 * t)
        r_arm = -0.9 + 0.45 * math.sin(10.0 * t)
        l_arm = 0.2

    elif motion == "shake_no":
        # Lắc đầu từ chối
        neck = 0.7 * math.sin(10.0 * t)

    elif motion == "happy_dance":
        # Nhảy theo nhịp nhạc (BPM): xoay cổ, vẫy 2 tay ngược pha và lắc nhẹ đế bánh xích
        neck = 0.5 * math.sin(omega * t)
        l_arm = -0.5 + 0.6 * math.sin(omega * t)
        r_arm = -0.5 - 0.6 * math.sin(omega * t)
        l_wheel = 3.5 * math.sin(omega * t)
        r_wheel = -3.5 * math.sin(omega * t)

    elif motion == "move_forward":
        l_wheel, r_wheel = 5.0, 5.0
        l_arm, r_arm = -0.3, -0.3

    elif motion == "move_backward":
        l_wheel, r_wheel = -4.0, -4.0

    elif motion == "spin_around":
        l_wheel, r_wheel = 5.0, -5.0
        l_arm, r_arm = -0.8, -0.8

    # Ghi vào mảng điều khiển (ctrl) của MuJoCo
    data.ctrl[0] = neck
    data.ctrl[1] = l_arm
    data.ctrl[2] = r_arm
    data.ctrl[3] = l_wheel
    data.ctrl[4] = r_wheel

def main():
    xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teo_walle.xml")
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)

    print(f"[Tèo 3D Sim] Đang lắng nghe lệnh Motion Bundle tại UDP {UDP_IP}:{UDP_PORT}...")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        start_t = time.time()
        while viewer.is_running():
            step_start = time.time()

            # Kiểm tra gói tin UDP mới từ FastMCP
            try:
                raw_bytes, _ = sock.recvfrom(1024)
                cmd = json.loads(raw_bytes.decode("utf-8"))
                current_state["motion"] = cmd.get("motion", "idle")
                current_state["bpm"] = int(cmd.get("bpm", 120))
                duration = float(cmd.get("duration", 3.0))
                current_state["end_time"] = time.time() + duration
                print(f"-> Thực thi Motion Bundle: {current_state['motion']} (BPM={current_state['bpm']}, {duration}s)")
            except BlockingIOError:
                pass

            # Cập nhật quỹ đạo khớp và tiến hành bước mô phỏng vật lý
            apply_motion_bundle(data, time.time() - start_t, current_state)
            mujoco.mj_step(model, data)
            viewer.sync()

            # Giữ tốc độ khung hình ổn định
            elapsed = time.time() - step_start
            if elapsed < model.opt.timestep:
                time.sleep(model.opt.timestep - elapsed)

if __name__ == "__main__":
    main()
