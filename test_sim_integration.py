"""
Integration test for 3D MuJoCo Simulation Runner, HMAC-SHA256 Wi-Fi UDP protocol,
and LeKiwi 3-Wheel Omni kinematics with downward IR cliff sensors.
"""

import json
import math
import socket
import threading
import time
import unittest

import mujoco
from config import UDP_SIM_TARGET
from teo_sim_runner import (
    BASE_RADIUS,
    SAFE_TABLE_RADIUS,
    apply_motion_bundle,
    compute_lekiwi_wheel_speeds,
)
from tools.dispatcher import execute_tool_call
from tools.guardrails import sign_wifi_packet, verify_wifi_packet
from tools.system import send_motion_to_3d_sim


class TestSimIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = mujoco.MjModel.from_xml_path("teo_walle.xml")
        cls.data = mujoco.MjData(cls.model)

    def test_01_xml_structure_matches_hardware(self):
        """Kiểm tra mô hình 3D khớp chính xác các thông số phần cứng CAD v10 Unibody."""
        # 5 actuators tương ứng 5 servo MG90S của thiết kế Unibody (2 tay + 3 bánh Omni)
        self.assertEqual(self.model.nu, 5)
        actuator_names = [mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(5)]
        self.assertEqual(
            actuator_names,
            [
                "servo_left_arm",
                "servo_right_arm",
                "servo_omni_w1",
                "servo_omni_w2",
                "servo_omni_w3",
            ],
        )

        # Kiểm tra sự tồn tại của 3 mắt IR, tấm đế, màn hình ST7789, TTP223, PCA9685, 2S 18650, đệm chống lật
        geom_names = [mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, i) for i in range(self.model.ngeom)]
        self.assertIn("omni_base_plate", geom_names)
        self.assertIn("ir1_led", geom_names)
        self.assertIn("ir2_led", geom_names)
        self.assertIn("ir3_led", geom_names)
        self.assertIn("lcd_screen", geom_names)
        self.assertIn("ttp223_touch_pad", geom_names)
        self.assertIn("pca9685_board", geom_names)
        self.assertIn("battery_cell_1", geom_names)
        self.assertIn("battery_cell_2", geom_names)
        self.assertIn("omni_pad_tail", geom_names)
        self.assertIn("desk_top", geom_names)
        self.assertIn("safety_border", geom_names)

    def test_02_lekiwi_kinematics_formulas(self):
        """Kiểm tra tính đúng đắn của công thức động học LeKiwi 3 bánh Omni."""
        # Trường hợp 1: Trượt ngang sang phải (vx = 0.14, vy = 0, omega = 0)
        # w1 = vx * scale = 0.14 * 35 = 4.9
        # w2 = -0.5 * 0.14 * 35 = -2.45
        # w3 = -0.5 * 0.14 * 35 = -2.45
        w1, w2, w3 = compute_lekiwi_wheel_speeds(0.14, 0.0, 0.0)
        self.assertAlmostEqual(w1, 4.9, places=2)
        self.assertAlmostEqual(w2, -2.45, places=2)
        self.assertAlmostEqual(w3, -2.45, places=2)

        # Trường hợp 2: Tiến thẳng (vx = 0, vy = 0.14, omega = 0)
        # w1 = 0
        # w2 = sqrt(3)/2 * 0.14 * 35 = 0.866025 * 4.9 ≈ 4.2435
        # w3 = -sqrt(3)/2 * 0.14 * 35 ≈ -4.2435
        w1, w2, w3 = compute_lekiwi_wheel_speeds(0.0, 0.14, 0.0)
        self.assertAlmostEqual(w1, 0.0, places=2)
        self.assertAlmostEqual(w2, 4.2435, places=2)
        self.assertAlmostEqual(w3, -4.2435, places=2)

        # Trường hợp 3: Tự xoay tại chỗ (vx = 0, vy = 0, omega = 3.2)
        # w1 = w2 = w3 = R * omega * 35 = 0.058 * 3.2 * 35 = 6.496
        w1, w2, w3 = compute_lekiwi_wheel_speeds(0.0, 0.0, 3.2)
        self.assertAlmostEqual(w1, 6.496, places=2)
        self.assertAlmostEqual(w2, 6.496, places=2)
        self.assertAlmostEqual(w3, 6.496, places=2)

    def test_03_ir_cliff_detection_and_table_containment(self):
        """Kiểm tra cơ chế 3 mắt hồng ngoại IR chống rơi mép bàn khi robot trượt."""
        state = {"motion": "move_forward", "bpm": 120, "end_time": time.time() + 2.0}
        data = mujoco.MjData(self.model)
        data.qpos[3] = 1.0  # Unit quaternion qw=1

        # Đặt vị trí robot chạm vạch an toàn mép bàn (x = 0.42m, y = 0.0m)
        data.qpos[0] = 0.42
        data.qpos[1] = 0.0
        # Di chuyển tiến tới: world_vx = +0.14 -> dist = 0.42 + 0.14*0.05 = 0.427 > 0.42m
        apply_motion_bundle(data, 0.1, state)

        # Sau khi kích hoạt IR, vận tốc world_vx phải bị đảo chiều âm (-px * 0.6) để lùi vào giữa bàn
        self.assertLess(data.qvel[0], 0.0)

    def test_04_udp_hmac_handshake_roundtrip(self):
        """Kiểm tra quy trình truyền nhận UDP thời gian thực có ký số HMAC-SHA256."""
        stop_event = threading.Event()

        def mock_sim_server():
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(UDP_SIM_TARGET)
            server_sock.settimeout(0.2)
            try:
                while not stop_event.is_set():
                    try:
                        data, addr = server_sock.recvfrom(1024)
                        pkt = json.loads(data.decode("utf-8"))
                        valid, _ = verify_wifi_packet(
                            pkt,
                            expected_role="laptop_controller",
                            required_permission="motion_cmd",
                        )
                        if valid and "id" in pkt:
                            ack_pkt = sign_wifi_packet(
                                {"ack": pkt["id"]},
                                role="robot_node",
                            )
                            server_sock.sendto(json.dumps(ack_pkt).encode("utf-8"), addr)
                    except socket.timeout:
                        continue
            finally:
                server_sock.close()

        server_thread = threading.Thread(target=mock_sim_server, daemon=True)
        server_thread.start()
        time.sleep(0.08)

        try:
            # Test gửi lệnh gesture thân trên
            res1 = execute_tool_call("dieu_khien_co_the_teo", '{"hanh_dong": "wave_greeting", "so_giay": 2.5}')
            self.assertIn("Đã thực hiện cử chỉ wave_greeting", res1)

            # Test gửi lệnh đế 3 bánh Omni
            res2 = execute_tool_call("di_chuyen_da_huong_omni", '{"huong_di": "slide_left", "so_giay": 2.0}')
            self.assertIn("Đế 3 bánh Omni đã trượt ngang sang trái", res2)
        finally:
            stop_event.set()
            server_thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()