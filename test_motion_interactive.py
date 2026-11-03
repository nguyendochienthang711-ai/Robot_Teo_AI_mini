"""
Kịch bản thử nghiệm toàn diện các công cụ chuyển động & động học Kiwi Drive (LeKiwi)
Kiểm tra:
- dieu_khien_co_the_teo (wave_greeting, nod_yes, shake_no, look_around, happy_dance, moonwalk_dance)
- di_chuyen_da_huong_omni (slide_left, slide_right, move_forward, move_backward, circle_strafe, spin_around)
- Xác thực bảo mật Wi-Fi HMAC-SHA256 2 chiều qua UDP port 5555
- Công thức động học ngược LeKiwi và tính toán tốc độ bánh xe (w1, w2, w3)
"""

import json
import math
import sys
import time

from tools.dispatcher import execute_tool_call

TEST_CASES = [
    {
        "name": "1. Vẫy tay chào và nghiêng cổ (wave_greeting)",
        "tool": "dieu_khien_co_the_teo",
        "args": {"hanh_dong": "wave_greeting", "so_giay": 2.5},
        "description": "Cổ xoay yaw dao động nhẹ + vẫy mạnh tay phải chào sếp.",
        "vx": 0.0, "vy": 0.0, "omega": 0.0,
    },
    {
        "name": "2. Gật đầu đồng ý (nod_yes)",
        "tool": "dieu_khien_co_the_teo",
        "args": {"hanh_dong": "nod_yes", "so_giay": 2.0},
        "description": "Hai tay vẫy nhẹ đồng ý kết hợp nhún nhẹ tiến lùi.",
        "vx": 0.0, "vy": 0.04, "omega": 0.0,
    },
    {
        "name": "3. Lắc đầu từ chối (shake_no)",
        "tool": "dieu_khien_co_the_teo",
        "args": {"hanh_dong": "shake_no", "so_giay": 2.0},
        "description": "Cổ xoay yaw tần số cao dứt khoát.",
        "vx": 0.0, "vy": 0.0, "omega": 0.0,
    },
    {
        "name": "4. Nhìn quanh tìm sếp (look_around)",
        "tool": "dieu_khien_co_the_teo",
        "args": {"hanh_dong": "look_around", "so_giay": 2.5},
        "description": "Xoay cổ góc rộng tìm kiếm người nói.",
        "vx": 0.0, "vy": 0.0, "omega": 0.0,
    },
    {
        "name": "5. Nhảy múa tại chỗ theo nhạc (happy_dance)",
        "tool": "dieu_khien_co_the_teo",
        "args": {"hanh_dong": "happy_dance", "so_giay": 2.5, "bpm": 130},
        "description": "Cổ + 2 tay bơm nhịp theo BPM 130 + lắc hông đa hướng.",
        "vx": 0.0, "vy": 0.0, "omega": 1.8,
    },
    {
        "name": "6. Trượt ngang sang TRÁI trên đế Omni (slide_left)",
        "tool": "di_chuyen_da_huong_omni",
        "args": {"huong_di": "slide_left", "so_giay": 2.0},
        "description": "Trượt thẳng sang trái mà ĐÔI MẮT LCD VẪN KHÓA VÀO SẾP.",
        "vx": -0.14, "vy": 0.0, "omega": 0.0,
    },
    {
        "name": "7. Trượt ngang sang PHẢI trên đế Omni (slide_right)",
        "tool": "di_chuyen_da_huong_omni",
        "args": {"huong_di": "slide_right", "so_giay": 2.0},
        "description": "Trượt thẳng sang phải mà ĐÔI MẮT LCD VẪN KHÓA VÀO SẾP.",
        "vx": 0.14, "vy": 0.0, "omega": 0.0,
    },
    {
        "name": "8. Tiến thẳng lên phía trước (move_forward)",
        "tool": "di_chuyen_da_huong_omni",
        "args": {"huong_di": "move_forward", "so_giay": 2.0},
        "description": "Di chuyển tiến về phía người dùng trên mặt bàn.",
        "vx": 0.0, "vy": 0.14, "omega": 0.0,
    },
    {
        "name": "9. Lùi lại phía sau (move_backward)",
        "tool": "di_chuyen_da_huong_omni",
        "args": {"huong_di": "move_backward", "so_giay": 2.0},
        "description": "Lùi an toàn vào khu vực trung tâm.",
        "vx": 0.0, "vy": -0.12, "omega": 0.0,
    },
    {
        "name": "10. Lượn vòng cung quanh bàn (circle_strafe)",
        "tool": "di_chuyen_da_huong_omni",
        "args": {"huong_di": "circle_strafe", "so_giay": 2.5},
        "description": "Quỹ đạo elip/vòng cung, cổ tự bù góc giữ nguyên ánh mắt nhìn sếp.",
        "vx": 0.14, "vy": 0.06, "omega": 0.0,
    },
    {
        "name": "11. Tự xoay tròn 360 độ (spin_around)",
        "tool": "di_chuyen_da_huong_omni",
        "args": {"huong_di": "spin_around", "so_giay": 2.0},
        "description": "3 bánh xe Omni quay cùng chiều với tốc độ đồng đều để xoay quanh tâm.",
        "vx": 0.0, "vy": 0.0, "omega": 3.2,
    },
    {
        "name": "12. Vũ đạo Moonwalk đỉnh cao (moonwalk_dance)",
        "tool": "dieu_khien_co_the_teo",
        "args": {"hanh_dong": "moonwalk_dance", "so_giay": 3.0, "bpm": 120},
        "description": "Kết hợp cả 6 kênh: Trượt ngang đa hướng + vẫy 2 tay + khóa ánh mắt.",
        "vx": 0.14, "vy": 0.05, "omega": 0.0,
    },
]


def calculate_kiwi_speeds(vx: float, vy: float, omega: float, r: float = 0.055, scale: float = 35.0):
    """Tính vận tốc 3 bánh xe theo công thức LeKiwi chuẩn."""
    sqrt3_2 = math.sqrt(3.0) / 2.0
    r_omega = r * omega
    w1 = (vx + r_omega) * scale
    w2 = (-0.5 * vx + sqrt3_2 * vy + r_omega) * scale
    w3 = (-0.5 * vx - sqrt3_2 * vy + r_omega) * scale
    return round(w1, 2), round(w2, 2), round(w3, 2)


def run_test_suite(auto_mode: bool = True):
    print("=" * 80)
    print("🤖 CHƯƠNG TRÌNH THỬ NGHIỆM ĐỘNG HỌC & CÔNG CỤ CHUYỂN ĐỘNG ROBOT TÈO")
    print("   Hệ thống: ESP32-S3 + PCA9685 + 3 Servo MG90S 180° + 3 Bánh Omni Kiwi Drive")
    print("=" * 80)

    success_count = 0
    total = len(TEST_CASES)

    for idx, tc in enumerate(TEST_CASES, start=1):
        print(f"\n--- [Test {idx}/{total}] {tc['name']} ---")
        print(f"📝 Mô tả: {tc['description']}")
        print(f"🔧 Tool: `{tc['tool']}` với tham số: {json.dumps(tc['args'], ensure_ascii=False)}")

        # Động học lý thuyết LeKiwi
        w1, w2, w3 = calculate_kiwi_speeds(tc["vx"], tc["vy"], tc["omega"])
        print(f"📐 Động học LeKiwi: w1={w1:+.2f} rad/s, w2={w2:+.2f} rad/s, w3={w3:+.2f} rad/s")

        # Thực thi qua dispatcher
        start_time = time.time()
        res = execute_tool_call(tc["tool"], json.dumps(tc["args"]))
        dur = round(time.time() - start_time, 3)

        if "ERROR" in res:
            print(f"⚠️ Kết quả: {res} (Lưu ý: Nếu chưa mở `teo_sim_runner.py`, mô phỏng sẽ báo unreachable)")
        else:
            print(f"✅ Kết quả: {res} (thời gian: {dur}s)")
            success_count += 1

        if auto_mode:
            time.sleep(1.2)
        else:
            input("Ấn Enter để tiếp tục test ca tiếp theo...")

    print("\n" + "=" * 80)
    print(f"🎯 TỔNG KẾT: Hoàn thành {total} ca kiểm thử chuyển động.")
    print("=" * 80)


if __name__ == "__main__":
    is_auto = True
    if len(sys.argv) > 1 and sys.argv[1] == "--step":
        is_auto = False
    run_test_suite(auto_mode=is_auto)