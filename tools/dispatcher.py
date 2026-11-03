"""
Dispatcher: Maps tool function names to implementation handlers and executes tool calls.
"""

import json

from tools.documents import (
    tool_doc_va_tom_tat_tai_lieu,
    tool_ghi_nho_thong_tin_dai_han,
    tool_xu_ly_bo_nho_tam_clipboard,
)
from tools.media import tool_phat_nhac_va_dieu_khien_media
from tools.search import tool_tra_cuu_thong_tin_truc_tuyen
from tools.secretary import (
    tool_dong_ho_tap_trung_pomodoro,
    tool_quan_ly_cong_viec,
)
from tools.system import (
    tool_di_chuyen_da_huong_omni,
    tool_dieu_khien_co_the_teo,
    tool_doi_giong_noi_teo,
    tool_kiem_tra_suc_khoe_laptop,
)

TOOL_DISPATCH = {
    # Nhóm 1: Thư ký cá nhân & Thời gian
    "quan_ly_cong_viec": tool_quan_ly_cong_viec,
    "dong_ho_tap_trung_pomodoro": tool_dong_ho_tap_trung_pomodoro,
    # Nhóm 2: Đọc tài liệu, Clipboard & Bộ nhớ dài hạn
    "doc_va_tom_tat_tai_lieu": tool_doc_va_tom_tat_tai_lieu,
    "xu_ly_bo_nho_tam_clipboard": tool_xu_ly_bo_nho_tam_clipboard,
    "ghi_nho_thong_tin_dai_han": tool_ghi_nho_thong_tin_dai_han,
    # Nhóm 3: Thị giác màn hình máy tính
    "nhin_man_hinh_laptop": None,  # Nạp động theo nhu cầu để tối ưu tài nguyên
    # Nhóm 4: Điều khiển laptop & Chẩn đoán phần cứng
    "kiem_tra_suc_khoe_laptop": tool_kiem_tra_suc_khoe_laptop,
    # Nhóm 5: Giải trí, Âm nhạc & Đổi giọng
    "phat_nhac_va_dieu_khien_media": tool_phat_nhac_va_dieu_khien_media,
    "doi_giong_noi_teo": tool_doi_giong_noi_teo,
    # Nhóm 6: Cử chỉ thân trên & Đế 3 bánh Omni Kiwi Drive (LeKiwi)
    "dieu_khien_co_the_teo": tool_dieu_khien_co_the_teo,
    "di_chuyen_da_huong_omni": tool_di_chuyen_da_huong_omni,
    # Nhóm 7: Tra cứu thời tiết & Tìm kiếm trực tuyến
    "tra_cuu_thong_tin_truc_tuyen": tool_tra_cuu_thong_tin_truc_tuyen,
}


def execute_tool_call(func_name: str, args_json: str) -> str:
    """Execute tool call and return concise spoken Vietnamese output."""
    try:
        args = json.loads(args_json) if args_json else {}
        if not isinstance(args, dict):
            args = {}
    except Exception:
        args = {}

    if func_name == "nhin_man_hinh_laptop":
        from tools.vision import tool_nhin_man_hinh_laptop

        handler = tool_nhin_man_hinh_laptop
    else:
        handler = TOOL_DISPATCH.get(func_name)

    if not handler:
        return "Công cụ không tồn tại."

    try:
        return handler(args)
    except Exception as e:
        print(f"⚠️ [Tool Error - {func_name}]: {e}")
        return f"Đã xảy ra lỗi khi thực thi công cụ {func_name}: {e}"
