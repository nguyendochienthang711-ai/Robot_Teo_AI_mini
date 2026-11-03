"""
Teo AI Robot Secretary - Modular Tools Package.

Groups:
- secretary: Todo list & Pomodoro timers.
- documents: Document reader/summarizer, Clipboard & Long-Term Memory.
- vision: Laptop screen screenshot analysis.
- system: Laptop diagnostics & 3D physical motions.
- media: YouTube background audio player & Media controller.
- search: Online weather & DuckDuckGo web search.
"""

from tools import common, dispatcher, documents, media, schemas, search, secretary, system, vision

# Common & Schemas
from tools.common import _load_json_file, _save_json_file, _strip_accents
from tools.dispatcher import TOOL_DISPATCH, execute_tool_call

# Documents & Memory
from tools.documents import (
    tool_doc_va_tom_tat_tai_lieu,
    tool_ghi_nho_thong_tin_dai_han,
    tool_xu_ly_bo_nho_tam_clipboard,
)

# Media & YouTube
from tools.media import (
    _find_youtube_video_url,
    _play_youtube_background,
    _send_media_key,
    _stop_background_music,
    tool_phat_nhac_va_dieu_khien_media,
)
from tools.schemas import TOOLS_SCHEMA

# Search & Weather
from tools.search import (
    _fetch_weather,
    _fetch_web_search,
    tool_tra_cuu_thong_tin_truc_tuyen,
)

# Secretary & Timers
from tools.secretary import (
    _active_timers,
    _speak_alert_sync,
    tool_dong_ho_tap_trung_pomodoro,
    tool_quan_ly_cong_viec,
)

# System & 3D Simulation
from tools.system import (
    VALID_MOTIONS,
    VOICE_LABELS,
    get_gpu_live_status,
    get_hardware_specs,
    send_motion_to_3d_sim,
    tool_doi_giong_noi_teo,
    tool_kiem_tra_suc_khoe_laptop,
    tool_thuc_hien_cu_chi_co_the,
)

# Vision
from tools.vision import (
    _capture_screen_image,
    _get_active_window_title,
    tool_nhin_man_hinh_laptop,
)

__all__ = [
    # Submodules
    "common",
    "dispatcher",
    "documents",
    "media",
    "schemas",
    "search",
    "secretary",
    "system",
    "vision",
    # Core interfaces
    "TOOLS_SCHEMA",
    "execute_tool_call",
    "TOOL_DISPATCH",
    # Tools
    "tool_quan_ly_cong_viec",
    "tool_kiem_tra_suc_khoe_laptop",
    "tool_doi_giong_noi_teo",
    "tool_doc_va_tom_tat_tai_lieu",
    "tool_phat_nhac_va_dieu_khien_media",
    "tool_thuc_hien_cu_chi_co_the",
    "tool_xu_ly_bo_nho_tam_clipboard",
    "tool_nhin_man_hinh_laptop",
    "tool_dong_ho_tap_trung_pomodoro",
    "tool_tra_cuu_thong_tin_truc_tuyen",
    "tool_ghi_nho_thong_tin_dai_han",
    # Helpers
    "send_motion_to_3d_sim",
    "get_hardware_specs",
    "get_gpu_live_status",
    "_strip_accents",
    "_load_json_file",
    "_save_json_file",
    "_speak_alert_sync",
    "_play_youtube_background",
    "_stop_background_music",
    "_send_media_key",
    "_find_youtube_video_url",
    "_capture_screen_image",
    "_get_active_window_title",
    "_fetch_weather",
    "_fetch_web_search",
]
