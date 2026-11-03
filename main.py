import asyncio
import logging
from logging.handlers import RotatingFileHandler
import sys
import time
import aiohttp

import config
from audio_io import (
    record_with_auto_vad,
    set_background_music_volume,
    speech_to_text,
    warmup_piper_default,
)
from brain import stop_speaking, stream_llm_and_speak
from config import DEEPSEEK_API_KEY, LOGS_DIR, MODEL_NAME
from tools.secretary import restore_timers


def setup_logging() -> None:
    """Configure rotating file logger in logs/teo.log (R-19)."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        LOGS_DIR / "teo.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root = logging.getLogger("teo")
    root.setLevel(logging.INFO)
    if not root.handlers:
        root.addHandler(handler)


async def main():
    setup_logging()
    if not DEEPSEEK_API_KEY:
        print("❌ Lỗi: Chưa tìm thấy DEEPSEEK_API_KEY trong file .env!")
        sys.exit(1)

    # Khôi phục hẹn giờ bền vững từ teo_timers.json và nạp sẵn giọng Piper (R-09, R-20)
    restore_timers()
    asyncio.create_task(asyncio.to_thread(warmup_piper_default))

    print("=== TRỢ LÝ ROBOT TÈO (GIỌNG NÓI STREAMING + ĐẾ 3 BÁNH OMNI LEKIWI + 12 TOOL ĐỢT 1 & 2) ===")
    print(f"-> Não bộ: DeepSeek ({MODEL_NAME}) | Prompt Tiếng Anh tối ưu Token/Cache -> Output Tiếng Việt")
    print("-> Đợt 1: Todo, Sức khỏe/Cấu hình Laptop, Đổi giọng nói, Đọc/Tóm tắt file, Nhạc YouTube/Media, Cử chỉ 3D, Di chuyển Omni")
    print("-> Đợt 2: Đọc/Ghi Clipboard, Nhìn màn hình Laptop, Hẹn giờ Pomodoro, Thời tiết/Web, Bộ nhớ dài hạn\n")

    async with aiohttp.ClientSession() as http_session:
        while True:
            try:
                cmd = await asyncio.to_thread(
                    input, "👉 Bấm [ENTER] để nói (hoặc gõ chữ / 'q' để thoát): "
                )
                cmd = cmd.strip()
            except (EOFError, KeyboardInterrupt):
                stop_speaking()
                print("\nTèo chào sếp, hẹn gặp lại sếp nhé!")
                break

            if cmd.lower() == "q":
                stop_speaking()
                print("Tèo chào sếp, hẹn gặp lại sếp nhé!")
                break

            stop_speaking()
            user_text = ""
            if cmd:
                user_text = cmd
                print(f"📝 [Sếp nhắn]: \"{user_text}\"")
            else:
                wav_path, has_spoken = await asyncio.to_thread(record_with_auto_vad)
                if not has_spoken:
                    set_background_music_volume(duck=False)
                    print("⚠️ Chưa nghe thấy tiếng nói, sếp thử nói lại nhé!")
                    continue
                user_text = await asyncio.to_thread(speech_to_text, wav_path)
                if not user_text:
                    set_background_music_volume(duck=False)
                    continue

            now_str = time.strftime("%H:%M ngày %d/%m/%Y")
            user_msg = f"[Giờ hệ thống: {now_str}] {user_text}"

            try:
                await stream_llm_and_speak(http_session, user_message=user_msg)
            except Exception as e:
                set_background_music_volume(duck=False)
                print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    asyncio.run(main())
