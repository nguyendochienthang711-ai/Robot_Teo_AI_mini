import asyncio
import os
import time
import edge_tts
import pygame
from langdetect import detect

# Khởi tạo trình phát âm thanh trên Windows
pygame.mixer.init()

# Bảng ánh xạ giọng đọc tự động theo ngôn ngữ (phục vụ tính năng Dịch thuật Mục 6.9)
VOICE_MAP = {
    "vi": "vi-VN-NamMinhNeural",   # Đổi thành "vi-VN-HoaiMyNeural" nếu thích giọng nữ
    "en": "en-US-AvaNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
}

async def teo_speak(text: str, output_file: str = "temp_reply.mp3"):
    start_time = time.perf_counter()

    # 1. Tự động phát hiện ngôn ngữ của câu để chọn giọng chuẩn
    try:
        lang = detect(text)
    except Exception:
        lang = "vi"
    voice = VOICE_MAP.get(lang, "vi-VN-NamMinhNeural")

    # 2. Gọi EdgeTTS sinh file âm thanh (tăng tốc độ đọc nhẹ +10% cho lanh lợi)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+10%")
    await communicate.save(output_file)

    latency_ms = (time.perf_counter() - start_time) * 1000
    print(f"[Tèo TTS] Ngôn ngữ: {lang} | Giọng: {voice} | Độ trễ tạo âm: {latency_ms:.0f} ms")
    print(f"[Tèo nói]: {text}\n")

    # 3. Phát ra loa laptop
    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)

    # Giải phóng file sau khi đọc xong
    pygame.mixer.music.unload()

async def main():
    print("=== KIỂM THỬ GIỌNG NÓI CỦA TÈO (BƯỚC 0.1) ===\n")
    
    # Test 1: Giọng tiếng Việt tự nhiên (đọc số và ngày tháng dạng lời nói)
    await teo_speak(
        "Chào sếp! Em là Tèo, trợ lý robot của sếp đây. "
        "Hệ thống âm thanh trên laptop Victus mười lăm đã sẵn sàng hoạt động!"
    )

    # Test 2: Kiểm thử tự động đổi giọng khi dịch sang tiếng Anh
    await teo_speak(
        "Hello boss! When I translate documents into English, I will automatically switch to an English native voice."
    )

if __name__ == "__main__":
    asyncio.run(main())