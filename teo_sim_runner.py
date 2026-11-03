import json
import math
import os
import socket
import time
import mujoco
import mujoco.viewer

# Mở socket UDP không chặn (non-blocking) để nhận lệnh từ Tools / FastMCP
UDP_IP = "127.0.0.1"
UDP_PORT = 5555

# Bán kính đế tròn 3 bánh Omni LeKiwi (m) và giới hạn an toàn mặt bàn (3 cảm biến IR)
BASE_RADIUS = 0.055
WHEEL_SCALE = 35.0
SAFE_TABLE_RADIUS = 0.42

current_state = {
    "motion": "idle",
    "bpm": 120,
    "end_time": 0.0,
}


def compute_lekiwi_wheel_speeds(vx: float, vy: float, omega_rot: float) -> tuple[float, float, float]:
    """
    Công thức động học ngược 3 bánh xe đa hướng (3-Wheel Omni Kiwi Drive - LeKiwi):
      w1 = vx + R * omega
      w2 = -0.5 * vx + (sqrt(3)/2) * vy + R * omega
      w3 = -0.5 * vx - (sqrt(3)/2) * vy + R * omega
    Trong đó:
      - vx: vận tốc trượt ngang phải (+) / trái (-) (m/s)
      - vy: vận tốc tiến (+) / lùi (-) (m/s)
      - omega_rot: vận tốc góc tự xoay quanh tâm (rad/s)
    """
    sqrt3_half = math.sqrt(3.0) / 2.0
    r_omega = BASE_RADIUS * omega_rot
    w1 = (vx + r_omega) * WHEEL_SCALE
    w2 = (-0.5 * vx + sqrt3_half * vy + r_omega) * WHEEL_SCALE
    w3 = (-0.5 * vx - sqrt3_half * vy + r_omega) * WHEEL_SCALE
    return w1, w2, w3


def apply_motion_bundle(data, t: float, state: dict):
    """
    Giải mã tên gói Motion Bundle & Kiwi Drive thành xung điều khiển mượt cho:
    - Kênh 0..2 PCA9685: 3 Servo thân trên MG90S 180° (Cổ, Tay trái, Tay phải)
    - Kênh 3..5 PCA9685: 3 Servo bánh xe Omni MG90S 360° (w1, w2, w3)
    """
    motion = state["motion"]
    bpm = max(60, min(200, state.get("bpm", 120)))
    freq = bpm / 60.0
    beat_omega = 2.0 * math.pi * freq

    neck, l_arm, r_arm = 0.0, 0.0, 0.0
    vx, vy, omega_rot = 0.0, 0.0, 0.0

    if time.time() > state["end_time"]:
        state["motion"] = "idle"
        motion = "idle"

    if motion == "idle":
        # Thở nhẹ tự nhiên
        l_arm = 0.08 * math.sin(2.0 * t)
        r_arm = 0.08 * math.sin(2.0 * t)

    elif motion == "wave_greeting":
        # Nghiêng cổ nhẹ + vẫy tay phải chào
        neck = 0.35 * math.sin(4.0 * t)
        r_arm = -0.9 + 0.45 * math.sin(10.0 * t)
        l_arm = 0.2

    elif motion == "nod_yes":
        # Gật đầu / vẫy nhẹ 2 tay đồng ý
        l_arm = -0.4 + 0.3 * math.sin(8.0 * t)
        r_arm = -0.4 + 0.3 * math.sin(8.0 * t)
        vy = 0.04 * math.sin(8.0 * t)

    elif motion == "shake_no":
        # Lắc cổ từ chối
        neck = 0.7 * math.sin(10.0 * t)

    elif motion == "look_around":
        # Xoay cổ tìm chủ nhân
        neck = 0.85 * math.sin(2.5 * t)
        l_arm = -0.15 * math.cos(2.5 * t)
        r_arm = 0.15 * math.cos(2.5 * t)

    elif motion == "happy_dance":
        # Nhảy múa tại chỗ theo nhịp BPM
        neck = 0.45 * math.sin(beat_omega * t)
        l_arm = -0.5 + 0.6 * math.sin(beat_omega * t)
        r_arm = -0.5 - 0.6 * math.sin(beat_omega * t)
        omega_rot = 1.8 * math.sin(beat_omega * t)

    elif motion == "moonwalk_dance":
        # Vũ đạo Moonwalk trượt ngang đa hướng kết hợp vẫy 2 tay theo nhịp BPM, mắt vẫn nhìn thẳng
        vx = 0.14 * math.sin(0.5 * beat_omega * t)
        vy = 0.05 * math.cos(beat_omega * t)
        neck = -0.25 * math.sin(0.5 * beat_omega * t)  # Giữ ánh mắt khóa về phía chủ nhân khi trượt
        l_arm = -0.55 + 0.55 * math.sin(beat_omega * t)
        r_arm = -0.55 + 0.55 * math.cos(beat_omega * t)

    elif motion == "move_forward":
        vy = 0.14
        l_arm, r_arm = -0.25, -0.25

    elif motion == "move_backward":
        vy = -0.12

    elif motion == "slide_left":
        # Trượt ngang sang trái giữ nguyên ánh mắt nhìn thẳng
        vx = -0.14
        l_arm, r_arm = -0.2, 0.1

    elif motion == "slide_right":
        # Trượt ngang sang phải giữ nguyên ánh mắt nhìn thẳng
        vx = 0.14
        l_arm, r_arm = 0.1, -0.2

    elif motion == "circle_strafe":
        # Lượn vòng cung quanh mặt bàn trong khi mặt vẫn khóa hướng về phía người ngồi
        vx = 0.14 * math.cos(1.2 * t)
        vy = 0.06 * math.sin(1.2 * t)
        neck = -0.3 * math.cos(1.2 * t)
        l_arm = -0.25 + 0.15 * math.sin(3.0 * t)
        r_arm = -0.25 - 0.15 * math.sin(3.0 * t)

    elif motion == "spin_around":
        omega_rot = 3.2
        l_arm, r_arm = -0.7, -0.7

    # Tính tốc độ 3 bánh xe Omni theo công thức LeKiwi
    w1, w2, w3 = compute_lekiwi_wheel_speeds(vx, vy, omega_rot)

    # Ghi vào 6 kênh điều khiển (ctrl) của MuJoCo
    data.ctrl[0] = neck
    data.ctrl[1] = l_arm
    data.ctrl[2] = r_arm
    data.ctrl[3] = w1
    data.ctrl[4] = w2
    data.ctrl[5] = w3

    # Cập nhật vận tốc phẳng Holonomic (Kiwi Drive) trong hệ tọa độ mặt bàn + bảo vệ 3 cảm biến IR chống rơi
    if vx != 0.0 or vy != 0.0 or omega_rot != 0.0:
        # Lấy góc hướng hiện tại (yaw) từ quaternion của freejoint root (qpos[3..6] = w, x, y, z)
        qw, qx, qy, qz = data.qpos[3], data.qpos[4], data.qpos[5], data.qpos[6]
        yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
        # Trong mô hình: trục +X của thân hướng về phía trước (vy), trục -Y hướng sang phải (vx)
        world_vx = vy * math.cos(yaw) + vx * math.sin(yaw)
        world_vy = vy * math.sin(yaw) - vx * math.cos(yaw)

        # Kiểm tra 3 mắt hồng ngoại IR chống rơi mép bàn
        px, py = data.qpos[0], data.qpos[1]
        if math.hypot(px + world_vx * 0.05, py + world_vy * 0.05) > SAFE_TABLE_RADIUS:
            world_vx, world_vy = -px * 0.5, -py * 0.5

        data.qvel[0] = world_vx
        data.qvel[1] = world_vy
        data.qvel[5] = omega_rot


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)

    xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teo_walle.xml")
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)

    print(f"[Tèo 3D Sim - Đế 3 bánh Omni LeKiwi] Đang lắng nghe lệnh UDP tại {UDP_IP}:{UDP_PORT}...")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        start_t = time.time()
        while viewer.is_running():
            step_start = time.time()

            try:
                raw_bytes, _ = sock.recvfrom(1024)
                cmd = json.loads(raw_bytes.decode("utf-8"))
                current_state["motion"] = cmd.get("motion", "idle")
                current_state["bpm"] = int(cmd.get("bpm", 120))
                duration = float(cmd.get("duration", 3.0))
                current_state["end_time"] = time.time() + duration
                print(
                    f"-> Thực thi Motion/Omni: {current_state['motion']} "
                    f"(BPM={current_state['bpm']}, {duration}s)"
                )
            except BlockingIOError:
                pass

            apply_motion_bundle(data, time.time() - start_t, current_state)
            mujoco.mj_step(model, data)
            viewer.sync()

            elapsed = time.time() - step_start
            if elapsed < model.opt.timestep:
                time.sleep(model.opt.timestep - elapsed)


if __name__ == "__main__":
    main()
