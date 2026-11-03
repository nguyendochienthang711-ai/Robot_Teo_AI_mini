import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Thiết lập stdout/stderr UTF-8 trên Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
TTS_MODE = os.getenv("TEO_TTS_MODE", "chipmunk").lower()

PIPER_DIR = Path("models/piper")
PIPER_PROFILES = {
    "chipmunk": {
        "model": PIPER_DIR / "vi_VN-diemdam-medium.onnx",
        "length_scale": 1.42,
        "factor": 1.55,
        "label": "Tèo Sóc Chuột (Vui nhộn)",
    },
    "diemdam": {
        "model": PIPER_DIR / "vi_VN-diemdam-medium.onnx",
        "length_scale": 1.00,
        "factor": 1.00,
        "label": "Tèo Nam Trầm (Điềm đạm)",
    },
    "tramvang": {
        "model": PIPER_DIR / "vi_VN-tramvang-medium.onnx",
        "length_scale": 1.00,
        "factor": 1.00,
        "label": "Tèo Nam Trầm (Vang)",
    },
}

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)
SPEECH_THRESHOLD = 450

UDP_SIM_TARGET = ("127.0.0.1", 5555)
TODO_FILE = Path("teo_todo.json")
MEMORY_FILE = Path("teo_memory.json")
BOOKMARK_FILE = Path("teo_bookmarks.json")
VISION_MODEL = os.getenv("VISION_MODEL", "deepseek-flash")
DEFAULT_CITY = os.getenv("TEO_DEFAULT_CITY", "Ha Noi")

VN_CHARS_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)

# English system prompt to minimize token usage and latency while enforcing Vietnamese spoken output
SYSTEM_PROMPT = (
    "You are Teo, a smart, witty desktop robot secretary. "
    "Always respond in Vietnamese, calling yourself 'em' and the user 'sếp'. "
    "OUTPUT RULES: Reply in 1 to 3 short spoken sentences separated by periods. "
    "Never use markdown (*, #, -), ellipsis (...), bullet points, or emojis. "
    "Write numbers as spoken Vietnamese words when natural for TTS. "
    "Always call the appropriate tool for: robot body motions, todo list, laptop health/specs, "
    "voice profile switching, document reading/summarizing, music/media control, clipboard reading/writing, "
    "laptop screen vision, Pomodoro/timers, weather/web search, or saving/recalling long-term personal memories."
)
