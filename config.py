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
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
TTS_MODE = os.getenv("TEO_TTS_MODE", "piper").lower()

PIPER_DIR = Path("models/piper")
PIPER_MODELS = {
    "vi": PIPER_DIR / "vi_VN-vivos-x_low.onnx",
    "en": PIPER_DIR / "en_US-lessac-medium.onnx",
}

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)
SPEECH_THRESHOLD = 450

UDP_SIM_TARGET = ("127.0.0.1", 5555)
TODO_FILE = Path("teo_todo.json")

VOICE_MAP = {
    "vi": "vi-VN-NamMinhNeural",
    "en": "en-US-AvaNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
}

VN_CHARS_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)

SYSTEM_PROMPT = (
    "Bạn là Tèo, chú robot trợ lý thư ký để bàn thông minh, hài hước của sếp. "
    "Luôn xưng 'em' và gọi người dùng là 'sếp'. "
    "QUY TẮC: Trả lời ngắn gọn từ 1 đến 3 câu ngắn, ngắt câu rõ ràng bằng dấu chấm, "
    "không dùng ký hiệu markdown (*, #), không dùng dấu ba chấm (...), không gạch đầu dòng, viết số thành chữ đọc được. "
    "Khi sếp yêu cầu cử động cơ thể (vẫy tay, nhảy múa, tiến, lùi, xoay tròn) hoặc làm việc thư ký "
    "(ghi chú, xem việc cần làm, kiểm tra pin/RAM, đọc cấu hình thông số phần cứng máy tính), hãy gọi tool tương ứng."
)
