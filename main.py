import asyncio
import time
import aiohttp

from audio_io import record_with_auto_vad, set_background_music_volume, speech_to_text
from brain import chat_history, stream_llm_and_speak
from config import MODEL_NAME


async def main():
    print("=== TRỢ LÝ ROBOT TÈO (GIỌNG NÓI STREAMING + ĐẾ 3 BÁNH OMNI LEKIWI + 12 TOOL ĐỢT 1 & 2) ===")
    print(f"-> Não bộ: DeepSeek ({MODEL_NAME}) | Prompt Tiếng Anh tối ưu Token/Cache -> Output Tiếng Việt")
    print("-> Đợt 1: Todo, Sức khỏe/Cấu hình Laptop, Đổi giọng nói, Đọc/Tóm tắt file, Nhạc YouTube/Media, Cử chỉ 3D, Di chuyển Omni")
    print("-> Đợt 2: Đọc/Ghi Clipboard, Nhìn màn hình Laptop, Hẹn giờ Pomodoro, Thời tiết/Web, Bộ nhớ dài hạn\n")

    async with aiohttp.ClientSession() as http_session:
        while True:
            try:
                cmd = input("👉 Bấm [ENTER] để nói (hoặc gõ chữ / 'q' để thoát): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nTèo chào sếp, hẹn gặp lại sếp nhé!")
                break

            if cmd.lower() == "q":
                print("Tèo chào sếp, hẹn gặp lại sếp nhé!")
                break

            user_text = ""
            if cmd:
                user_text = cmd
                print(f"📝 [Sếp nhắn]: \"{user_text}\"")
            else:
                wav_path, has_spoken = record_with_auto_vad()
                if not has_spoken:
                    set_background_music_volume(duck=False)
                    print("⚠️ Chưa nghe thấy tiếng nói, sếp thử nói lại nhé!")
                    continue
                user_text = speech_to_text(wav_path)
                if not user_text:
                    set_background_music_volume(duck=False)
                    continue

            now_str = time.strftime("%H:%M ngày %d/%m/%Y")
            chat_history.append({"role": "user", "content": f"[Giờ hệ thống: {now_str}] {user_text}"})

            try:
                reply = await stream_llm_and_speak(http_session)
                if reply:
                    chat_history.append({"role": "assistant", "content": reply})
            except Exception as e:
                set_background_music_volume(duck=False)
                print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    asyncio.run(main())
