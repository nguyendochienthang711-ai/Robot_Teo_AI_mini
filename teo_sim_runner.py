import json
import math
import os
import socket
import time
import mujoco
import mujoco.viewer

from tools.guardrails import sign_wifi_packet, verify_wifi_packet

# Cổng UDP lắng nghe lệnh điều khiển từ Tools (Python / LLM)
UDP_IP = "127.0.0.1"
UDP_PORT = 5555

# Bán kính tâm bánh xe 3 bánh Omni LeKiwi CAD v10 (58mm = 0.058m)
BASE_RADIUS = 0.058
WHEEL_SCALE = 35.0
SAFE_TABLE_RADIUS = 0.42

current_state = {
    "motion": "idle",
    "bpm": 120,
    "end_time": 0.0,
    "last_cliff_alert": 0.0,
    "agent_state": "IDLE",
    "eye_mood": "relaxed_blink",
    "eye_rgba": [0.0, 0.88, 1.0, 1.0],
    "arm_pose": [0.0, 0.0],
    "wheel_locked": False,
}


def compute_lekiwi_wheel_speeds(vx: float, vy: float, omega_rot: float) -> tuple[float, float, float]:
    """
    Công thức động học ngược 3 bánh xe đa hướng (3-Wheel Omni Kiwi Drive - LeKiwi):
      w1 = vx + R * omega_rot
      w2 = -0.5 * vx + (sqrt(3)/2) * vy + R * omega_rot
      w3 = -0.5 * vx - (sqrt(3)/2) * vy + R * omega_rot
    Trong đó:
      - vx: vận tốc trượt ngang phải (+) / trái (-) (m/s)
      - vy: vận tốc tiến (+) / lùi (-) (m/s)
      - omega_rot: vận tốc góc tự xoay quanh trục thẳng đứng (rad/s)
      - R: bán kính tâm đế tới bánh xe (0.055m)
    """
    sqrt3_half = math.sqrt(3.0) / 2.0
    r_omega = BASE_RADIUS * omega_rot
    w1 = (vx + r_omega) * WHEEL_SCALE
    w2 = (-0.5 * vx + sqrt3_half * vy + r_omega) * WHEEL_SCALE
    w3 = (-0.5 * vx - sqrt3_half * vy + r_omega) * WHEEL_SCALE
    return w1, w2, w3


def apply_motion_bundle(data, t: float, state: dict):
    """
    Giải mã tên gói Motion Bundle & Kiwi Drive thành xung điều khiển cho:
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
        pose = state.get("arm_pose") or [0.0, 0.0]
        if state.get("agent_state", "IDLE") != "IDLE" and (pose[0] != 0.0 or pose[1] != 0.0):
            # Tư thế cánh tay biểu đạt trạng thái AI (LISTENING / THINKING / HITL_CONFIRM / SPEAKING / ALERT)
            l_arm = float(pose[0]) + 0.04 * math.sin(3.0 * t)
            r_arm = float(pose[1]) + 0.04 * math.sin(3.0 * t)
        else:
            # Thở nhẹ tự nhiên, hai tay đung đưa nhẹ
            l_arm = 0.08 * math.sin(2.0 * t)
            r_arm = 0.08 * math.sin(2.0 * t)
        # Giữ robot đứng yên chắc chắn trên mặt bàn khi nhàn rỗi
        data.qvel[0] = 0.0
        data.qvel[1] = 0.0
        data.qvel[5] = 0.0

    elif motion == "wave_greeting":
        # Nghiêng cổ chào + vẫy mạnh tay phải
        neck = 0.35 * math.sin(4.0 * t)
        r_arm = -0.9 + 0.45 * math.sin(10.0 * t)
        l_arm = 0.2

    elif motion == "nod_yes":
        # Gật đầu đồng ý + vẫy nhẹ 2 tay
        l_arm = -0.4 + 0.3 * math.sin(8.0 * t)
        r_arm = -0.4 + 0.3 * math.sin(8.0 * t)
        vy = 0.04 * math.sin(8.0 * t)

    elif motion == "shake_no":
        # Lắc cổ từ chối dứt khoát
        neck = 0.7 * math.sin(10.0 * t)

    elif motion == "look_around":
        # Xoay cổ quan sát xung quanh tìm sếp
        neck = 0.85 * math.sin(2.5 * t)
        l_arm = -0.15 * math.cos(2.5 * t)
        r_arm = 0.15 * math.cos(2.5 * t)

    elif motion == "happy_dance":
        # Vũ đạo vui vẻ tại chỗ theo nhịp điệu BPM
        neck = 0.45 * math.sin(beat_omega * t)
        l_arm = -0.5 + 0.6 * math.sin(beat_omega * t)
        r_arm = -0.5 - 0.6 * math.sin(beat_omega * t)
        omega_rot = 1.8 * math.sin(beat_omega * t)

    elif motion == "moonwalk_dance":
        # Vũ đạo Moonwalk: trượt ngang đa hướng + vẫy 2 tay, mắt vẫn nhìn thẳng
        vx = 0.14 * math.sin(0.5 * beat_omega * t)
        vy = 0.05 * math.cos(beat_omega * t)
        neck = -0.25 * math.sin(0.5 * beat_omega * t)  # Khóa ánh mắt về chủ nhân
        l_arm = -0.55 + 0.55 * math.sin(beat_omega * t)
        r_arm = -0.55 + 0.55 * math.cos(beat_omega * t)

    elif motion == "move_forward":
        vy = 0.14
        l_arm, r_arm = -0.25, -0.25

    elif motion == "move_backward":
        vy = -0.12

    elif motion == "slide_left":
        # Trượt ngang sang trái trên đế Omni, mặt vẫn nhìn thẳng
        vx = -0.14
        l_arm, r_arm = -0.2, 0.1

    elif motion == "slide_right":
        # Trượt ngang sang phải trên đế Omni, mặt vẫn nhìn thẳng
        vx = 0.14
        l_arm, r_arm = 0.1, -0.2

    elif motion == "circle_strafe":
        # Lượn vòng cung quanh mặt bàn trong khi mặt vẫn khóa hướng vào sếp
        vx = 0.14 * math.cos(1.2 * t)
        vy = 0.06 * math.sin(1.2 * t)
        neck = -0.3 * math.cos(1.2 * t)
        l_arm = -0.25 + 0.15 * math.sin(3.0 * t)
        r_arm = -0.25 - 0.15 * math.sin(3.0 * t)

    elif motion == "spin_around":
        omega_rot = 3.2
        l_arm, r_arm = -0.7, -0.7

    # Unibody Pod (bỏ servo cổ): chuyển biểu cảm xoay cổ sang xoay thân Holonomic trên đế Omni
    if neck != 0.0 and omega_rot == 0.0:
        omega_rot = neck * 2.2

    # Nếu State Machine đang khóa bánh xe (LISTENING thu âm hoặc chờ HITL), triệt tiêu vận tốc đế
    if state.get("wheel_locked", False):
        vx, vy, omega_rot = 0.0, 0.0, 0.0
        data.qvel[0] = 0.0
        data.qvel[1] = 0.0
        data.qvel[5] = 0.0

    # Tính tốc độ 3 bánh xe Omni theo công thức LeKiwi
    w1, w2, w3 = compute_lekiwi_wheel_speeds(vx, vy, omega_rot)

    # Mượt hóa góc 2 servo cánh tay (Rate limiting) tránh sốc xung cơ khí làm robot giật nảy
    smoothed = state.setdefault("smoothed_ctrl", [0.0, 0.0])
    target_ctrl = [l_arm, r_arm]
    for i in range(2):
        smoothed[i] += (target_ctrl[i] - smoothed[i]) * 0.15
        data.ctrl[i] = smoothed[i]

    # Ghi tốc độ 3 bánh xe Omni vào ctrl[2..4] (5 kênh vật lý trên Unibody CAD v10)
    data.ctrl[2] = w1
    data.ctrl[3] = w2
    data.ctrl[4] = w3

    # Giữ thăng bằng và triệt tiêu dao động lắc lư (Roll & Pitch Damping)
    data.qvel[3] *= 0.85
    data.qvel[4] *= 0.85

    # Cập nhật vận tốc phẳng Holonomic và cơ chế 3 cảm biến IR chống rơi mép bàn
    if vx != 0.0 or vy != 0.0 or omega_rot != 0.0:
        qw, qx, qy, qz = data.qpos[3], data.qpos[4], data.qpos[5], data.qpos[6]
        yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
        world_vx = vy * math.cos(yaw) + vx * math.sin(yaw)
        world_vy = vy * math.sin(yaw) - vx * math.cos(yaw)

        # 3 Cảm biến IR hướng xuống gầm: kiểm tra khoảng cách tâm bàn
        px, py = data.qpos[0], data.qpos[1]
        dist_to_center = math.hypot(px + world_vx * 0.05, py + world_vy * 0.05)
        if dist_to_center > SAFE_TABLE_RADIUS:
            now = time.time()
            if now - state.get("last_cliff_alert", 0.0) > 1.0:
                print(
                    f"⚠️ [IR CLIFF ALERT]: Phát hiện mép bàn tại r={dist_to_center:.3f}m > {SAFE_TABLE_RADIUS}m! "
                    "Kích hoạt phanh khẩn cấp & lùi an toàn!"
                )
                state["last_cliff_alert"] = now
            # Phanh tức thì và đẩy nhẹ ngược về phía tâm bàn
            world_vx = -px * 0.6
            world_vy = -py * 0.6

        data.qvel[0] = world_vx
        data.qvel[1] = world_vy
        data.qvel[5] = omega_rot


def make_key_callback(state: dict):
    """Bắt phím bấm trực tiếp từ cửa sổ giao diện 3D MuJoCo để test chuyển động tức thì."""
    def key_callback(keycode: int):
        # Số 1..6: Các cử chỉ thân trên & vũ đạo
        if keycode == ord("1"):
            state["motion"] = "wave_greeting"
            state["end_time"] = time.time() + 3.0
            print("👉 [PHÍM 1]: Cử chỉ vẫy tay chào sếp (wave_greeting)")
        elif keycode == ord("2"):
            state["motion"] = "nod_yes"
            state["end_time"] = time.time() + 2.5
            print("👉 [PHÍM 2]: Gật đầu đồng ý (nod_yes)")
        elif keycode == ord("3"):
            state["motion"] = "shake_no"
            state["end_time"] = time.time() + 2.5
            print("👉 [PHÍM 3]: Lắc đầu từ chối (shake_no)")
        elif keycode == ord("4"):
            state["motion"] = "happy_dance"
            state["bpm"] = 128
            state["end_time"] = time.time() + 3.0
            print("👉 [PHÍM 4]: Nhảy múa vui vẻ theo nhịp BPM 128 (happy_dance)")
        elif keycode == ord("5"):
            state["motion"] = "moonwalk_dance"
            state["bpm"] = 120
            state["end_time"] = time.time() + 3.5
            print("👉 [PHÍM 5]: Vũ đạo Moonwalk trượt đa hướng (moonwalk_dance)")
        elif keycode == ord("6"):
            state["motion"] = "look_around"
            state["end_time"] = time.time() + 3.0
            print("👉 [PHÍM 6]: Xoay cổ nhìn quanh tìm sếp (look_around)")
        # Phím di chuyển Omni Kiwi Drive: W, S, A, D, C, R, Space
        elif keycode in (ord("W"), ord("w"), 265):
            state["motion"] = "move_forward"
            state["end_time"] = time.time() + 2.0
            print("👉 [PHÍM W / UP]: Đế Omni tiến lên phía trước (move_forward)")
        elif keycode in (ord("S"), ord("s"), 264):
            state["motion"] = "move_backward"
            state["end_time"] = time.time() + 2.0
            print("👉 [PHÍM S / DOWN]: Đế Omni lùi lại phía sau (move_backward)")
        elif keycode in (ord("A"), ord("a"), 263):
            state["motion"] = "slide_left"
            state["end_time"] = time.time() + 2.0
            print("👉 [PHÍM A / LEFT]: Trượt ngang sang trái giữ ánh mắt (slide_left)")
        elif keycode in (ord("D"), ord("d"), 262):
            state["motion"] = "slide_right"
            state["end_time"] = time.time() + 2.0
            print("👉 [PHÍM D / RIGHT]: Trượt ngang sang phải giữ ánh mắt (slide_right)")
        elif keycode in (ord("C"), ord("c")):
            state["motion"] = "circle_strafe"
            state["end_time"] = time.time() + 3.0
            print("👉 [PHÍM C]: Lượn vòng cung quanh bàn giữ mắt khóa vào sếp (circle_strafe)")
        elif keycode in (ord("R"), ord("r")):
            state["motion"] = "spin_around"
            state["end_time"] = time.time() + 2.5
            print("👉 [PHÍM R]: Tự xoay tròn 360 độ tại chỗ (spin_around)")
        elif keycode in (ord("T"), ord("t")):
            # Mô phỏng chạm tay lên cảm biến chạm TTP223 trên đỉnh đầu Tèo
            try:
                from teo_harness import state_machine
                touch_pkt = sign_wifi_packet(
                    {"id": f"sim_touch_{int(time.time() * 1000)}", "event": "touch_confirm"},
                    role="robot_node",
                )
                ok_t, reason_t = state_machine.handle_robot_node_packet(touch_pkt)
                print(f"🖐️ [PHÍM T - CHẠM ĐỈNH ĐẦU TTP223]: ok={ok_t} ({reason_t})")
            except Exception as err:
                print(f"🖐️ [PHÍM T - TTP223]: {err}")
        elif keycode == 32:  # Space bar
            state["motion"] = "idle"
            state["end_time"] = 0.0
            print("🛑 [SPACE]: Dừng khẩn cấp / Đứng yên (idle)")
    return key_callback


def _update_st7789_eye_color(model, rgba: list[float]) -> None:
    """Cập nhật màu mắt ST7789 trên mô hình 3D MuJoCo theo trạng thái AI (thay cho vòng LED)."""
    if len(rgba) != 4:
        return
    for geom_name in ("lcd_eye_left", "lcd_eye_right"):
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
        if gid >= 0:
            model.geom_rgba[gid] = rgba


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)

    xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teo_walle.xml")
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)

    print("=" * 70)
    print("🤖 [TÈO 3D SIMULATION - PHẦN CỨNG WALL-E & ĐẾ 3 BÁNH OMNI LEKIWI]")
    print(f"📡 Đang lắng nghe lệnh UDP HMAC-SHA256 tại {UDP_IP}:{UDP_PORT}")
    print("⌨️  HỖ TRỢ ĐIỀU KHIỂN PHÍM TẮT TRỰC TIẾP TRONG CỬA SỔ 3D:")
    print("   [1] Vẫy tay chào     [2] Gật đầu      [3] Lắc đầu      [4] Nhảy vui vẻ")
    print("   [5] Vũ đạo Moonwalk  [6] Nhìn quanh")
    print("   [W/S] Tiến / Lùi     [A/D] Trượt ngang Trái / Phải (Mắt nhìn thẳng)")
    print("   [C] Lượn vòng cung   [R] Xoay 360 độ   [SPACE] Dừng khẩn cấp")
    print("=" * 70)

    key_cb = make_key_callback(current_state)

    with mujoco.viewer.launch_passive(model, data, key_callback=key_cb) as viewer:
        start_t = time.time()
        while viewer.is_running():
            step_start = time.time()

            try:
                raw_bytes, addr = sock.recvfrom(1024)
                cmd = json.loads(raw_bytes.decode("utf-8", errors="replace"))
                if not isinstance(cmd, dict):
                    raise ValueError("UDP payload must be a JSON object")

                pkt_type = cmd.get("type", "motion_cmd")
                req_perm = "state_sync" if pkt_type == "state_sync" else "motion_cmd"

                # Xác thực bảo mật gói tin Wi-Fi qua HMAC-SHA256 & chống replay
                ok_auth, reason = verify_wifi_packet(
                    cmd,
                    expected_role="laptop_controller",
                    required_permission=req_perm,
                )
                if not ok_auth:
                    print(f"🚫 [Sim Security Blocked]: Từ chối gói UDP không hợp lệ ({reason})")
                    continue

                if pkt_type == "state_sync":
                    current_state["agent_state"] = str(cmd.get("state", "IDLE"))
                    current_state["eye_mood"] = str(cmd.get("eye_mood", "relaxed_blink"))
                    current_state["wheel_locked"] = bool(cmd.get("wheel_locked", False))
                    if isinstance(cmd.get("arm_pose"), list) and len(cmd["arm_pose"]) == 2:
                        current_state["arm_pose"] = [float(cmd["arm_pose"][0]), float(cmd["arm_pose"][1])]
                    if isinstance(cmd.get("eye_rgba"), list) and len(cmd["eye_rgba"]) == 4:
                        current_state["eye_rgba"] = [float(x) for x in cmd["eye_rgba"]]
                        _update_st7789_eye_color(model, current_state["eye_rgba"])
                    print(
                        f"👁️ [ST7789 AI State -> {current_state['agent_state']}]: "
                        f"eye={current_state['eye_mood']}, wheel_locked={current_state['wheel_locked']}"
                    )
                    continue

                if cmd.get("id"):
                    try:
                        ack_pkt = sign_wifi_packet({"ack": cmd.get("id")}, role="robot_node")
                        sock.sendto(json.dumps(ack_pkt).encode("utf-8"), addr)
                    except OSError:
                        pass

                motion = str(cmd.get("motion", "idle"))
                bpm = max(60, min(160, int(cmd.get("bpm", 120))))
                duration = float(cmd.get("duration", 3.0))
                if not math.isfinite(duration):
                    duration = 3.0
                duration = max(0.5, min(8.0, duration))
                current_state["motion"] = motion
                current_state["bpm"] = bpm
                current_state["end_time"] = time.time() + duration
                print(
                    f"⚡ [UDP Motion Nhận Thành Công]: {current_state['motion']} "
                    f"(BPM={current_state['bpm']}, {duration}s)"
                )
            except BlockingIOError:
                pass
            except (ConnectionResetError, ValueError, TypeError, OSError) as err:
                print(f"[Sim UDP Warning]: Bỏ qua gói UDP lỗi: {err}")

            apply_motion_bundle(data, time.time() - start_t, current_state)
            mujoco.mj_step(model, data)
            viewer.sync()

            elapsed = time.time() - step_start
            if elapsed < model.opt.timestep:
                time.sleep(model.opt.timestep - elapsed)


if __name__ == "__main__":
    main()