"""
English function calling schemas for Teo Desktop Robot Secretary.
Concise English prompts save input tokens, preserve prompt caching, and reduce latency.
Strict validation via additionalProperties: False (TL-16).
"""

TOOLS_SCHEMA = [
    # --- BATCH 1: CORE TOOLS (6 TOOLS) ---
    {
        "type": "function",
        "function": {
            "name": "quan_ly_cong_viec",
            "description": "Manage the user's Todo task list: view all tasks, add a new task, mark a task done, delete a specific task, or clear all tasks.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["xem", "them", "hoan_thanh", "xoa", "xoa_het"],
                        "description": "'xem' (list), 'them' (add), 'hoan_thanh' (mark completed), 'xoa' (delete one), 'xoa_het' (clear all).",
                    },
                    "noi_dung": {
                        "type": "string",
                        "description": "Task text when adding, or keyword to match when completing/deleting.",
                    },
                    "vi_tri": {
                        "type": "integer",
                        "description": "1-based task number to mark completed or delete.",
                    },
                },
                "required": ["thao_tac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kiem_tra_suc_khoe_laptop",
            "description": "Check laptop diagnostics (CPU, RAM, battery, free disk space, GPU temp/VRAM) or full hardware specifications.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "che_do": {
                        "type": "string",
                        "enum": ["nhanh", "chi_tiet"],
                        "description": "'nhanh' for live usage/battery/disk/GPU status, 'chi_tiet' to include full hardware specs (CPU model, cores, total RAM, GPU model, OS).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doi_giong_noi_teo",
            "description": "Switch Teo robot's TTS voice profile during conversation.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "giong": {
                        "type": "string",
                        "enum": ["chipmunk", "diemdam", "tramvang", "google"],
                        "description": "'chipmunk' (cute high-pitched), 'diemdam' (calm male), 'tramvang' (deep resonant male), 'google' (female Google TTS).",
                    },
                },
                "required": ["giong"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doc_va_tom_tat_tai_lieu",
            "description": "Summarize or read aloud documents (.pdf, .docx, .pptx, .txt, .md) with automatic sentence-level bookmarking.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["tom_tat", "doc_tu_dau", "doc_tiep", "doc_lai", "dung", "trang_thai"],
                        "description": "'tom_tat' (extract text to summarize), 'doc_tu_dau' (read from start), 'doc_tiep' (continue from bookmark), 'doc_lai' (repeat previous sentences), 'dung' (stop & save bookmark), 'trang_thai' (check bookmark status).",
                    },
                    "duong_dan": {
                        "type": "string",
                        "description": "File path or filename in allowed document directories.",
                    },
                    "so_cau_doc": {
                        "type": "integer",
                        "description": "Number of sentences to read in one batch (default 5).",
                    },
                },
                "required": ["thao_tac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "phat_nhac_va_dieu_khien_media",
            "description": "Search and play music/videos on YouTube or control system media playback (play, pause, next, previous, volume).",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": [
                            "phat_nhac",
                            "dung_nhac",
                            "tam_dung",
                            "tiep_tuc",
                            "bai_tiep",
                            "bai_truoc",
                            "tang_am",
                            "giam_am",
                            "tat_tieng",
                        ],
                        "description": "'phat_nhac' (search & play YouTube audio in background), 'dung_nhac' (stop background player), 'tam_dung' (pause), 'tiep_tuc' (resume), 'bai_tiep' (next), 'bai_truoc' (previous), 'tang_am' (volume up), 'giam_am' (volume down), 'tat_tieng' (mute).",
                    },
                    "tu_khoa": {
                        "type": "string",
                        "description": "Song title or artist to play on YouTube when thao_tac is 'phat_nhac'.",
                    },
                },
                "required": ["thao_tac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dieu_khien_co_the_teo",
            "description": "Trigger 3D robot upper-body gestures and dance bundles: wave greeting, nod yes, shake no, look around, happy dance, or moonwalk dance.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "hanh_dong": {
                        "type": "string",
                        "enum": [
                            "wave_greeting",
                            "nod_yes",
                            "shake_no",
                            "look_around",
                            "happy_dance",
                            "moonwalk_dance",
                            "idle",
                        ],
                        "description": "Gesture/dance bundle: wave_greeting, nod_yes, shake_no, look_around, happy_dance, moonwalk_dance, idle.",
                    },
                    "so_giay": {
                        "type": "number",
                        "description": "Duration in seconds (clamped between 0.5 and 8.0s, default 3.5).",
                    },
                    "bpm": {
                        "type": "integer",
                        "description": "Dance tempo in BPM (clamped between 60 and 160, default 125).",
                    },
                },
                "required": ["hanh_dong"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "di_chuyen_da_huong_omni",
            "description": "Navigate the 3-Wheel Omni Kiwi Drive (LeKiwi) base on the desk: move forward, backward, slide left/right keeping eye contact, circle strafe, or spin.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "huong_di": {
                        "type": "string",
                        "enum": [
                            "move_forward",
                            "move_backward",
                            "slide_left",
                            "slide_right",
                            "circle_strafe",
                            "spin_around",
                            "idle",
                        ],
                        "description": "Omni direction: move_forward, move_backward, slide_left, slide_right, circle_strafe, spin_around, idle.",
                    },
                    "so_giay": {
                        "type": "number",
                        "description": "Move duration in seconds (clamped between 0.5 and 3.0s for desk safety, default 2.0).",
                    },
                },
                "required": ["huong_di"],
            },
        },
    },
    # --- BATCH 2: DESKTOP SECRETARY BREAKTHROUGH TOOLS (5 TOOLS) ---
    {
        "type": "function",
        "function": {
            "name": "xu_ly_bo_nho_tam_clipboard",
            "description": "Read text recently copied to the system clipboard (Ctrl+C) or write text to the clipboard.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["doc", "ghi"],
                        "description": "'doc' to read current clipboard text, 'ghi' to copy text into clipboard.",
                    },
                    "noi_dung_ghi": {
                        "type": "string",
                        "description": "Text to copy into clipboard when thao_tac is 'ghi'.",
                    },
                },
                "required": ["thao_tac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "nhin_man_hinh_laptop",
            "description": "Capture a screenshot of the active window and answer questions about what is displayed.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "cau_hoi": {
                        "type": "string",
                        "description": "Question or analysis request about the active screen window.",
                    },
                },
                "required": ["cau_hoi"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dong_ho_tap_trung_pomodoro",
            "description": "Set an asynchronous countdown timer or Pomodoro alarm with voice reminder, check status, or cancel timers.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["dat_hen_gio", "xem_trang_thai", "huy"],
                        "description": "'dat_hen_gio' (start timer), 'xem_trang_thai' (check remaining time), 'huy' (cancel timer).",
                    },
                    "so_phut": {
                        "type": "number",
                        "description": "Countdown duration in minutes (0.01 to 720 minutes).",
                    },
                    "loi_nhac": {
                        "type": "string",
                        "description": "Vietnamese reminder message spoken when the timer finishes.",
                    },
                    "hen_gio_id": {
                        "type": "integer",
                        "description": "Optional timer ID to cancel specifically.",
                    },
                },
                "required": ["thao_tac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tra_cuu_thong_tin_truc_tuyen",
            "description": "Look up real-time weather forecasts by city or search the web for current information, news, and prices.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "loai": {
                        "type": "string",
                        "enum": ["thoi_tiet", "tim_kiem"],
                        "description": "'thoi_tiet' for weather forecast, 'tim_kiem' for general web search.",
                    },
                    "tu_khoa": {
                        "type": "string",
                        "description": "City name for weather or search keywords for web search.",
                    },
                },
                "required": ["loai", "tu_khoa"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ghi_nho_thong_tin_dai_han",
            "description": "Save, search, list, or delete long-term personal facts, habits, preferences, or room numbers in persistent memory.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["luu", "tim_kiem", "xem_tat_ca", "xoa"],
                        "description": "'luu' (save fact), 'tim_kiem' (search memory), 'xem_tat_ca' (list all memories), 'xoa' (delete memory by key).",
                    },
                    "khoa": {
                        "type": "string",
                        "description": "Memory topic/key to save, search, or delete.",
                    },
                    "noi_dung": {
                        "type": "string",
                        "description": "Detailed fact to remember when thao_tac is 'luu'.",
                    },
                },
                "required": ["thao_tac"],
            },
        },
    },
]
