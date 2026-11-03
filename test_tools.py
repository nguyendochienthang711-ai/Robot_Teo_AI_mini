import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

import config
import tools
from tools import TOOLS_SCHEMA, execute_tool_call


class TestTeoToolsDot1AndDot2(unittest.TestCase):
    def setUp(self):
        """Tách biệt các file JSON lưu trữ (todo, memory, bookmark) trong thư mục tạm cho mỗi test."""
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.orig_todo = config.TODO_FILE
        self.orig_mem = config.MEMORY_FILE
        self.orig_bm = config.BOOKMARK_FILE
        self.orig_tts = config.TTS_MODE

        config.TODO_FILE = self.tmp_dir / "test_todo.json"
        config.MEMORY_FILE = self.tmp_dir / "test_memory.json"
        config.BOOKMARK_FILE = self.tmp_dir / "test_bookmarks.json"

    def tearDown(self):
        config.TODO_FILE = self.orig_todo
        config.MEMORY_FILE = self.orig_mem
        config.BOOKMARK_FILE = self.orig_bm
        config.TTS_MODE = self.orig_tts
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # ==========================================================================
    # 0. KIỂM TRA PROMPT TIẾNG ANH & SCHEMA CHUẨN (TỐI ƯU TOKEN / CACHE)
    # ==========================================================================
    def test_00_prompts_are_english_and_schema_count(self):
        # Đợt 1 + Nhóm 6 Omni (7 tools) + Đợt 2 (5 tools) = 12 tools (chuẩn 12-14 tools trong kế hoạch)
        self.assertEqual(len(TOOLS_SCHEMA), 12)
        expected_names = {
            # Đợt 1 & Nhóm 6 (Omni LeKiwi)
            "quan_ly_cong_viec",
            "kiem_tra_suc_khoe_laptop",
            "doi_giong_noi_teo",
            "doc_va_tom_tat_tai_lieu",
            "phat_nhac_va_dieu_khien_media",
            "dieu_khien_co_the_teo",
            "di_chuyen_da_huong_omni",
            # Đợt 2
            "xu_ly_bo_nho_tam_clipboard",
            "nhin_man_hinh_laptop",
            "dong_ho_tap_trung_pomodoro",
            "tra_cuu_thong_tin_truc_tuyen",
            "ghi_nho_thong_tin_dai_han",
        }
        actual_names = {t["function"]["name"] for t in TOOLS_SCHEMA}
        self.assertEqual(actual_names, expected_names)

        # Kiểm tra SYSTEM_PROMPT viết bằng tiếng Anh và yêu cầu trả lời tiếng Việt
        self.assertIn("You are Teo", config.SYSTEM_PROMPT)
        self.assertIn("Always respond in Vietnamese", config.SYSTEM_PROMPT)
        for t in TOOLS_SCHEMA:
            desc = t["function"]["description"]
            self.assertTrue(
                desc.isascii(),
                f"Tool description must be English ASCII to save tokens: {desc}",
            )

    # ==========================================================================
    # ĐỢT 1: 6 TOOLS CỐT LÕI
    # ==========================================================================
    def test_01_quan_ly_cong_viec(self):
        # 1. Xem khi trống
        res_empty = execute_tool_call("quan_ly_cong_viec", json.dumps({"thao_tac": "xem"}))
        self.assertIn("đang trống", res_empty)

        # 2. Thêm công việc
        res_add1 = execute_tool_call(
            "quan_ly_cong_viec",
            json.dumps({"thao_tac": "them", "noi_dung": "3 giờ chiều nộp báo cáo AI"}),
        )
        self.assertIn("Đã lưu công việc", res_add1)

        res_add2 = execute_tool_call(
            "quan_ly_cong_viec",
            json.dumps({"thao_tac": "them", "noi_dung": "Mua linh kiện ESP32-S3"}),
        )
        self.assertIn("Mua linh kiện ESP32-S3", res_add2)

        # 3. Xem danh sách
        res_list = execute_tool_call("quan_ly_cong_viec", json.dumps({"thao_tac": "xem"}))
        self.assertIn("2 việc", res_list)
        self.assertIn("chưa làm", res_list)

        # 4. Đánh dấu hoàn thành
        res_done = execute_tool_call(
            "quan_ly_cong_viec",
            json.dumps({"thao_tac": "hoan_thanh", "vi_tri": 1}),
        )
        self.assertIn("Đã đánh dấu hoàn thành", res_done)
        res_list_after = execute_tool_call("quan_ly_cong_viec", json.dumps({"thao_tac": "xem"}))
        self.assertIn("đã xong", res_list_after)

        # 5. Xóa 1 việc theo từ khóa không dấu
        res_del = execute_tool_call(
            "quan_ly_cong_viec",
            json.dumps({"thao_tac": "xoa", "noi_dung": "linh kien"}),
        )
        self.assertIn("Đã xóa công việc", res_del)

        # 6. Xóa hết
        res_clear = execute_tool_call("quan_ly_cong_viec", json.dumps({"thao_tac": "xoa_het"}))
        self.assertIn("Đã xóa sạch", res_clear)

    def test_02_kiem_tra_suc_khoe_laptop(self):
        res_fast = execute_tool_call("kiem_tra_suc_khoe_laptop", json.dumps({"che_do": "nhanh"}))
        self.assertIn("CPU", res_fast)
        self.assertIn("RAM", res_fast)
        self.assertIn("pin", res_fast)

        res_detail = execute_tool_call("kiem_tra_suc_khoe_laptop", json.dumps({"che_do": "chi_tiet"}))
        self.assertIn("Cấu hình máy tính của sếp", res_detail)
        self.assertIn("Hệ điều hành", res_detail)

    def test_03_doi_giong_noi_teo(self):
        res = execute_tool_call("doi_giong_noi_teo", json.dumps({"giong": "diemdam"}))
        self.assertIn("Đã đổi giọng nói", res)
        self.assertEqual(config.TTS_MODE, "diemdam")

        res_google = execute_tool_call("doi_giong_noi_teo", json.dumps({"giong": "google"}))
        self.assertIn("Google", res_google)
        self.assertEqual(config.TTS_MODE, "google")

        res_invalid = execute_tool_call("doi_giong_noi_teo", json.dumps({"giong": "unknown_voice"}))
        self.assertIn("không hợp lệ", res_invalid)

    def test_04_doc_va_tom_tat_tai_lieu(self):
        doc_file = self.tmp_dir / "bai_giang_ai.md"
        doc_file.write_text(
            "Câu một giới thiệu về trí tuệ nhân tạo. "
            "Câu hai nói về mạng nơ ron tích chập. "
            "Câu ba giải thích cơ chế tự chú ý Transformer. "
            "Câu bốn trình bày ứng dụng robot để bàn Tèo.",
            encoding="utf-8",
        )

        # 1. Tóm tắt
        res_sum = execute_tool_call(
            "doc_va_tom_tat_tai_lieu",
            json.dumps({"thao_tac": "tom_tat", "duong_dan": str(doc_file)}),
        )
        self.assertIn("Nội dung trích xuất", res_sum)
        self.assertIn("Transformer", res_sum)

        # 2. Đọc từ đầu (2 câu một lượt)
        res_read1 = execute_tool_call(
            "doc_va_tom_tat_tai_lieu",
            json.dumps({"thao_tac": "doc_tu_dau", "duong_dan": str(doc_file), "so_cau_doc": 2}),
        )
        self.assertIn("từ câu 1 đến câu 2", res_read1)
        self.assertIn("Câu một", res_read1)
        self.assertIn("Câu hai", res_read1)

        # 3. Đọc tiếp từ Bookmark (không cần truyền lại duong_dan)
        res_read2 = execute_tool_call(
            "doc_va_tom_tat_tai_lieu",
            json.dumps({"thao_tac": "doc_tiep", "so_cau_doc": 2}),
        )
        self.assertIn("từ câu 3 đến câu 4", res_read2)
        self.assertIn("Câu ba", res_read2)
        self.assertIn("Câu bốn", res_read2)

        # 4. Đọc lại câu vừa rồi
        res_repeat = execute_tool_call(
            "doc_va_tom_tat_tai_lieu",
            json.dumps({"thao_tac": "doc_lai", "so_cau_doc": 2}),
        )
        self.assertIn("từ câu 3 đến câu 4", res_repeat)

        # 5. Dừng đọc và kiểm tra trạng thái bookmark
        res_stop = execute_tool_call("doc_va_tom_tat_tai_lieu", json.dumps({"thao_tac": "dung"}))
        self.assertIn("Đã dừng đọc", res_stop)

        res_status = execute_tool_call("doc_va_tom_tat_tai_lieu", json.dumps({"thao_tac": "trang_thai"}))
        self.assertIn("bai_giang_ai.md", res_status)

    def test_05_phat_nhac_va_dieu_khien_media(self):
        played_urls = []
        sent_keys = []
        with (
            patch.object(
                tools.media,
                "_play_youtube_background",
                side_effect=lambda u: played_urls.append(u) or "trình phát ngầm không cửa sổ",
            ),
            patch.object(
                tools.media,
                "_find_youtube_video_url",
                return_value="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ),
            patch.object(tools.media, "_send_media_key", side_effect=lambda vk, repeat=1: sent_keys.append((vk, repeat))),
        ):
            res_play = execute_tool_call(
                "phat_nhac_va_dieu_khien_media",
                json.dumps({"thao_tac": "phat_nhac", "tu_khoa": "Lofi chill học bài"}),
            )
            self.assertIn("Đã bật ngầm bài hát", res_play)
            self.assertEqual(played_urls, ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])

            res_stop = execute_tool_call("phat_nhac_va_dieu_khien_media", json.dumps({"thao_tac": "dung_nhac"}))
            self.assertIn("Đã tắt trình phát nhạc ngầm", res_stop)
            res_pause = execute_tool_call("phat_nhac_va_dieu_khien_media", json.dumps({"thao_tac": "tam_dung"}))
            self.assertIn("tạm dừng", res_pause)
            res_next = execute_tool_call("phat_nhac_va_dieu_khien_media", json.dumps({"thao_tac": "bai_tiep"}))
            self.assertIn("bài nhạc tiếp theo", res_next)
            res_vol = execute_tool_call("phat_nhac_va_dieu_khien_media", json.dumps({"thao_tac": "tang_am"}))
            self.assertIn("tăng âm lượng", res_vol)
            self.assertEqual(len(sent_keys), 4)

    def test_06_dieu_khien_co_the_teo_and_omni_navigation(self):
        sent_motions = []
        with patch.object(
            tools.system,
            "send_motion_to_3d_sim",
            side_effect=lambda m, d, b: sent_motions.append((m, d, b)),
        ):
            # 1. Cử chỉ thân trên & Vũ đạo Moonwalk trên đế 3 bánh Omni
            res = execute_tool_call(
                "dieu_khien_co_the_teo",
                json.dumps({"hanh_dong": "moonwalk_dance", "so_giay": 5.0, "bpm": 135}),
            )
            self.assertIn("moonwalk_dance", res)
            self.assertEqual(sent_motions[-1], ("moonwalk_dance", 5.0, 135))

            execute_tool_call("dieu_khien_co_the_teo", json.dumps({"hanh_dong": "nod_yes"}))
            self.assertEqual(sent_motions[-1][0], "nod_yes")

            execute_tool_call("dieu_khien_co_the_teo", json.dumps({"hanh_dong": "look_around"}))
            self.assertEqual(sent_motions[-1][0], "look_around")

            # 2. Điều hướng toàn hướng Đế 3 bánh Omni Kiwi Drive (LeKiwi)
            res_slide_l = execute_tool_call(
                "di_chuyen_da_huong_omni",
                json.dumps({"huong_di": "slide_left", "so_giay": 2.0}),
            )
            self.assertIn("trượt ngang sang trái", res_slide_l)
            self.assertEqual(sent_motions[-1], ("slide_left", 2.0, 120))

            res_strafe = execute_tool_call(
                "di_chuyen_da_huong_omni",
                json.dumps({"huong_di": "circle_strafe", "so_giay": 10.0}),  # Phải tự giới hạn về 3.0s an toàn
            )
            self.assertIn("lượn vòng cung", res_strafe)
            self.assertEqual(sent_motions[-1], ("circle_strafe", 3.0, 120))

    def test_12_mujoco_lekiwi_omni_kinematics(self):
        import mujoco
        import teo_sim_runner

        # Kiểm tra công thức Kiwi Drive 3 bánh xe lệch 120 độ:
        # Khi trượt ngang sang phải (vx > 0, vy = 0, omega = 0): w1 > 0, w2 = w3 = -0.5 * w1
        w1, w2, w3 = teo_sim_runner.compute_lekiwi_wheel_speeds(0.2, 0.0, 0.0)
        self.assertGreater(w1, 0)
        self.assertAlmostEqual(w2, -0.5 * w1, places=5)
        self.assertAlmostEqual(w3, -0.5 * w1, places=5)

        # Kiểm tra nạp mô hình 3D MuJoCo 6 kênh PCA9685 (3 Servo thân trên + 3 Servo bánh Omni)
        xml_path = Path(__file__).parent / "teo_walle.xml"
        model = mujoco.MjModel.from_xml_path(str(xml_path))
        data = mujoco.MjData(model)
        self.assertEqual(model.nu, 6)

        state = {"motion": "slide_left", "bpm": 120, "end_time": time.time() + 2.0}
        teo_sim_runner.apply_motion_bundle(data, 0.5, state)
        self.assertLess(data.ctrl[3], 0)  # Bánh trước quay chiều trượt trái
        mujoco.mj_step(model, data)

    # ==========================================================================
    # ĐỢT 2: 5 TOOLS ĐỘT PHÁ CHO THƯ KÝ LAPTOP
    # ==========================================================================
    def test_07_xu_ly_bo_nho_tam_clipboard(self):
        clipboard_store = {"text": ""}

        def fake_copy(val):
            clipboard_store["text"] = val

        def fake_paste():
            return clipboard_store["text"]

        with (
            patch.object(tools.documents.pyperclip, "copy", side_effect=fake_copy),
            patch.object(tools.documents.pyperclip, "paste", side_effect=fake_paste),
        ):
            res_empty = execute_tool_call("xu_ly_bo_nho_tam_clipboard", json.dumps({"thao_tac": "doc"}))
            self.assertIn("đang trống", res_empty)

            res_write = execute_tool_call(
                "xu_ly_bo_nho_tam_clipboard",
                json.dumps({"thao_tac": "ghi", "noi_dung_ghi": "def hello(): return 42"}),
            )
            self.assertIn("Đã sao chép", res_write)

            res_read = execute_tool_call("xu_ly_bo_nho_tam_clipboard", json.dumps({"thao_tac": "doc"}))
            self.assertIn("def hello(): return 42", res_read)

    def test_08_nhin_man_hinh_laptop(self):
        fake_img = Image.new("RGB", (800, 600), color=(30, 60, 90))
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(message=MagicMock(content="Màn hình đang mở file main.py trong VS Code."))
        ]
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_resp

        with (
            patch.object(tools.vision, "_capture_screen_image", return_value=fake_img),
            patch.object(tools.vision, "_get_active_window_title", return_value="VS Code - main.py"),
            patch("tools.vision.OpenAI", return_value=mock_client_instance),
        ):
            res = execute_tool_call(
                "nhin_man_hinh_laptop",
                json.dumps({"cau_hoi": "Trên màn hình đang mở gì?"}),
            )
            self.assertIn("VS Code - main.py", res)
            self.assertIn("Màn hình đang mở file main.py", res)

    def test_09_dong_ho_tap_trung_pomodoro(self):
        alerted = []
        with patch.object(tools.secretary, "_speak_alert_sync", side_effect=lambda msg: alerted.append(msg)):
            res_set = execute_tool_call(
                "dong_ho_tap_trung_pomodoro",
                json.dumps({"thao_tac": "dat_hen_gio", "so_phut": 0.002, "loi_nhac": "Tắt bếp sếp ơi"}),
            )
            self.assertIn("Đã đặt đồng hồ đếm ngược", res_set)

            res_status = execute_tool_call(
                "dong_ho_tap_trung_pomodoro",
                json.dumps({"thao_tac": "xem_trang_thai"}),
            )
            self.assertIn("Tắt bếp sếp ơi", res_status)

            time.sleep(0.3)
            self.assertIn("Tắt bếp sếp ơi", alerted)

            execute_tool_call(
                "dong_ho_tap_trung_pomodoro",
                json.dumps({"thao_tac": "dat_hen_gio", "so_phut": 25, "loi_nhac": "Pomodoro học AI"}),
            )
            res_cancel = execute_tool_call("dong_ho_tap_trung_pomodoro", json.dumps({"thao_tac": "huy"}))
            self.assertIn("Đã hủy toàn bộ", res_cancel)

    def test_10_tra_cuu_thong_tin_truc_tuyen(self):
        def fake_get(url, timeout=4.0, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            if "geocoding-api" in url:
                resp.json.return_value = {
                    "results": [
                        {"name": "Hà Nội", "latitude": 21.0285, "longitude": 105.8542}
                    ]
                }
            else:
                resp.json.return_value = {
                    "current": {
                        "temperature_2m": 24.5,
                        "apparent_temperature": 25.0,
                        "relative_humidity_2m": 65,
                        "wind_speed_10m": 10.0,
                        "weather_code": 1,
                    }
                }
            return resp

        def fake_post(url, data=None, headers=None, timeout=5.0):
            resp = MagicMock()
            resp.status_code = 200
            resp.text = """
            <html><body>
              <div class="result__body">
                <a class="result__title">Giá vàng hôm nay</a>
                <a class="result__snippet">Giá vàng SJC niêm yết ở mức 89 triệu đồng mỗi lượng.</a>
              </div>
            </body></html>
            """
            return resp

        with (
            patch.object(tools.search.requests, "get", side_effect=fake_get),
            patch.object(tools.search.requests, "post", side_effect=fake_post),
        ):
            res_wx = execute_tool_call(
                "tra_cuu_thong_tin_truc_tuyen",
                json.dumps({"loai": "thoi_tiet", "tu_khoa": ""}),
            )
            self.assertIn("Hà Nội", res_wx)
            self.assertIn("24.5 độ C", res_wx)

            res_search = execute_tool_call(
                "tra_cuu_thong_tin_truc_tuyen",
                json.dumps({"loai": "tim_kiem", "tu_khoa": "giá vàng hôm nay"}),
            )
            self.assertIn("Giá vàng hôm nay", res_search)
            self.assertIn("89 triệu đồng", res_search)

    def test_11_ghi_nho_thong_tin_dai_han(self):
        res_save = execute_tool_call(
            "ghi_nho_thong_tin_dai_han",
            json.dumps(
                {
                    "thao_tac": "luu",
                    "khoa": "Phòng học môn AI",
                    "noi_dung": "Phòng P.402 nhà A1 sáng thứ Ba",
                }
            ),
        )
        self.assertIn("đã ghi nhớ vào bộ nhớ dài hạn", res_save)

        res_find = execute_tool_call(
            "ghi_nho_thong_tin_dai_han",
            json.dumps({"thao_tac": "tim_kiem", "khoa": "phong hoc mon ai"}),
        )
        self.assertIn("P.402 nhà A1", res_find)

        res_all = execute_tool_call(
            "ghi_nho_thong_tin_dai_han",
            json.dumps({"thao_tac": "xem_tat_ca"}),
        )
        self.assertIn("1 thông tin", res_all)

        res_del = execute_tool_call(
            "ghi_nho_thong_tin_dai_han",
            json.dumps({"thao_tac": "xoa", "khoa": "Phòng học"}),
        )
        self.assertIn("Đã xóa thông tin", res_del)


if __name__ == "__main__":
    unittest.main(verbosity=2)
