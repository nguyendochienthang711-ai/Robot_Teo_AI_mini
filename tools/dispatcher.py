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
    get_hardware_specs,
    tool_doi_giong_noi_teo,
    tool_kiem_tra_suc_khoe_laptop,
    tool_thuc_hien_cu_chi_co_the,
)

TOOL_DISPATCH = {
    # Đợt 1
    "quan_ly_cong_viec": tool_quan_ly_cong_viec,
    "quan_ly_viec_can_lam": tool_quan_ly_cong_viec,  # Backward compatibility alias
    "kiem_tra_suc_khoe_laptop": tool_kiem_tra_suc_khoe_laptop,
    "doc_thong_so_may_tinh": lambda _: get_hardware_specs(),  # Backward compatibility alias
    "doi_giong_noi_teo": tool_doi_giong_noi_teo,
    "doc_va_tom_tat_tai_lieu": tool_doc_va_tom_tat_tai_lieu,
    "phat_nhac_va_dieu_khien_media": tool_phat_nhac_va_dieu_khien_media,
    "thuc_hien_cu_chi_co_the": tool_thuc_hien_cu_chi_co_the,
    "dieu_khien_co_the_teo": tool_thuc_hien_cu_chi_co_the,  # Backward compatibility alias
    # Đợt 2
    "xu_ly_bo_nho_tam_clipboard": tool_xu_ly_bo_nho_tam_clipboard,
    "nhin_man_hinh_laptop": None,  # Will be resolved dynamically to allow patching/lazy loading
    "dong_ho_tap_trung_pomodoro": tool_dong_ho_tap_trung_pomodoro,
    "tra_cuu_thong_tin_truc_tuyen": tool_tra_cuu_thong_tin_truc_tuyen,
    "ghi_nho_thong_tin_dai_han": tool_ghi_nho_thong_tin_dai_han,
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

