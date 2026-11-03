"""
Group 3: Computer Vision & Screen Analysis.
- Capture laptop screen screenshots, compress to 1280px to save vision tokens (~384 tokens),
  and analyze active window diagrams, error traces, or slides via Vision model.
"""

import base64
import ctypes
import io
import sys
import time
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageGrab

import config


def _get_active_window_title() -> str:
    """Retrieve title of currently focused Windows window."""
    if sys.platform != "win32":
        return "Không rõ"
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value.strip()
    except Exception:
        pass
    return "Màn hình Desktop"


def _capture_screen_image() -> Image.Image | None:
    """Safely capture desktop screenshot using PIL ImageGrab."""
    try:
        return ImageGrab.grab()
    except Exception:
        return None


def tool_nhin_man_hinh_laptop(args: dict) -> str:
    """Analyze laptop screen with Vision LLM and answer user questions in Vietnamese."""
    question = (args.get("cau_hoi") or "Giải thích nội dung đang hiển thị trên màn hình").strip()
    save_file = bool(args.get("luu_file", False))
    win_title = _get_active_window_title()

    img = _capture_screen_image()
    if img is None:
        return (
            f"Cửa sổ đang mở là '{win_title}', nhưng hiện tại em chưa chụp được ảnh màn hình "
            "do giới hạn quyền hiển thị."
        )

    # Scale down to 1280px max dimension for optimal token efficiency (~384 tokens) and low latency
    max_dim = 1280
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    if save_file:
        shots_dir = Path("screenshots")
        shots_dir.mkdir(exist_ok=True)
        shot_path = shots_dir / f"screen_{int(time.time())}.jpg"
        img.convert("RGB").save(shot_path, format="JPEG", quality=82)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=80)
    b64_img = base64.b64encode(buf.getvalue()).decode("ascii")

    vision_model = config.VISION_MODEL or config.MODEL_NAME
    if config.DEEPSEEK_API_KEY:
        try:
            client = OpenAI(
                api_key=config.DEEPSEEK_API_KEY,
                base_url=config.DEEPSEEK_BASE_URL,
                timeout=20.0,
            )
            resp = client.chat.completions.create(
                model=vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Analyze the user's laptop screenshot and answer their question concisely "
                            "in 1-3 short spoken Vietnamese sentences without markdown."
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Active window: '{win_title}'. User question: {question}",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                            },
                        ],
                    },
                ],
                max_tokens=180,
            )
            answer = (resp.choices[0].message.content or "").strip()
            if answer:
                print(f"👁️ [Tool Call -> Screen Vision ({vision_model})]: {answer}")
                return f"Trên màn hình cửa sổ '{win_title}': {answer}"
        except Exception as e:
            print(f"⚠️ [Screen Vision Fallback]: Model '{vision_model}' chưa nhận ảnh trực tiếp ({e})")

    return (
        f"Em đã chụp màn hình cửa sổ '{win_title}' (kích thước {img.size[0]} nhân {img.size[1]} điểm ảnh). "
        f"Lưu ý: Model hiện tại '{vision_model}' chỉ hỗ trợ văn bản nên sếp hãy đặt biến VISION_MODEL "
        "trong file .env sang model hỗ trợ thị giác như deepseek-flash để em phân tích chi tiết hình ảnh nhé."
    )

