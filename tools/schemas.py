"""
English function calling schemas for Teo Desktop Robot Secretary.
Concise English prompts save input tokens, preserve prompt caching, and reduce latency.
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
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["tom_tat", "doc_tu_dau", "doc_tiep", "doc_lai", "dung", "trang_thai"],
                        "description": "'tom_tat' (extract text to summarize), 'doc_tu_dau' (read from start), 'doc_tiep' (continue from bookmark), 'doc_lai' (repeat previous sentences), 'dung' (stop & save bookmark), 'trang_thai' (check bookmark status).",
                    },
                    "duong_dan": {
                        "type": "string",
                        "description": "File path or filename (optional when continuing/stopping an active bookmarked document).",
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
            "name": "thuc_hien_cu_chi_co_the",
            "description": "Trigger 3D robot physical motion bundles (head, arms, tank tracks) in MuJoCo / ESP32.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hanh_dong": {
                        "type": "string",
                        "enum": [
                            "wave_greeting",
                            "nod_yes",
                            "shake_no",
                            "look_around",
                            "happy_dance",
                            "move_forward",
                            "move_backward",
                            "spin_around",
                            "idle",
                        ],
                        "description": "Motion bundle: wave_greeting, nod_yes, shake_no, look_around, happy_dance, move_forward, move_backward, spin_around, idle.",
                    },
                    "so_giay": {
                        "type": "number",
                        "description": "Duration in seconds (default 3.5).",
                    },
                    "bpm": {
                        "type": "integer",
                        "description": "Dance tempo in BPM (default 125).",
                    },
                },
                "required": ["hanh_dong"],
            },
        },
    },
    # --- BATCH 2: DESKTOP SECRETARY BREAKTHROUGH TOOLS (5 TOOLS) ---
    {
        "type": "function",
        "function": {
            "name": "xu_ly_bo_nho_tam_clipboard",
            "description": "Read text/code recently copied to the system clipboard (Ctrl+C) to translate, summarize, or debug, or write text to the clipboard.",
            "parameters": {
                "type": "object",
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
            "description": "Capture a screenshot of the current laptop screen and analyze diagrams, slides, or error messages using vision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cau_hoi": {
                        "type": "string",
                        "description": "Question or task about what is shown on the laptop screen.",
                    },
                    "luu_file": {
                        "type": "boolean",
                        "description": "Set true to save screenshot to disk (default false).",
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
            "description": "Set an asynchronous countdown timer / Pomodoro alarm with voice announcement and arm waving, check remaining time, or cancel timers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["dat_hen_gio", "xem_trang_thai", "huy"],
                        "description": "'dat_hen_gio' (start timer), 'xem_trang_thai' (check remaining time), 'huy' (cancel all timers).",
                    },
                    "so_phut": {
                        "type": "number",
                        "description": "Countdown duration in minutes (e.g. 25 for Pomodoro, 0.5 for 30s).",
                    },
                    "loi_nhac": {
                        "type": "string",
                        "description": "Vietnamese reminder message spoken when the timer finishes.",
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
                "properties": {
                    "loai": {
                        "type": "string",
                        "enum": ["thoi_tiet", "tim_kiem"],
                        "description": "'thoi_tiet' for live weather by city, 'tim_kiem' for general web search.",
                    },
                    "tu_khoa": {
                        "type": "string",
                        "description": "City name (e.g., 'Ho Chi Minh', 'Ha Noi') for weather, or search query for web search.",
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
            "description": "Save, search, list, or delete long-term personal facts, habits, preferences, or room numbers in persistent memory (teo_memory.json).",
            "parameters": {
                "type": "object",
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["luu", "tim_kiem", "xem_tat_ca", "xoa"],
                        "description": "'luu' (save fact), 'tim_kiem' (search memory), 'xem_tat_ca' (list all memories), 'xoa' (delete memory by key).",
                    },
                    "khoa": {
                        "type": "string",
                        "description": "Memory topic/key or search keyword (e.g., 'phòng học AI', 'sở thích').",
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

