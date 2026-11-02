import asyncio
import io
import os
import re
import sys
import time

# Thiết lập stdout/stderr UTF-8 để in tiếng Việt không bị lỗi charmap trên Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import edge_tts
import numpy as np
import pygame
import scipy.io.wavfile as wav
import sounddevice as sd
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI
from langdetect import detect

# 1. Nạp API Key và khởi tạo kết nối DeepSeek LLM
load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    print("❌ Lỗi: Chưa tìm thấy DEEPSEEK_API_KEY trong file .env!")
    print("   Vui lòng kiểm tra lại file .env của bạn.")
    sys.exit(1)

llm_client = OpenAI(
    api_key=deepseek_api_key,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    timeout=30.0,
)
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Khởi tạo âm thanh
pygame.mixer.init()

# Warm-up langdetect
try:
    detect("Khởi động hệ thống tiếng Việt")
except Exception:
    pass

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1  # Đọc mic từng mảnh 100ms
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

VOICE_MAP = {
    "vi": "vi-VN-NamMinhNeural",
    "en": "en-US-AvaNeural",
    "zh-cn": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
}

# System Prompt tĩnh tối ưu cho Tèo
SYSTEM_PROMPT = (
    "Bạn là Tèo, chú robot trợ lý thư ký để bàn thông minh, lanh lợi của sếp. "
    "Luôn xưng 'em' và gọi người dùng là 'sếp'. "
    "QUY TẮC: Trả lời ngắn gọn từ 1 đến 3 câu ngắn, ngắt câu rõ ràng bằng dấu chấm, "
    "không dùng ký hiệu markdown (*, #), không gạch đầu dòng, viết số thành chữ đọc được."
)
chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
recognizer = sr.Recognizer()


def record_with_auto_vad(filename="mic_input.wav", silence_limit_sec=0.9, max_sec=15.0):
    """Thu âm thông minh: Tự động dừng ngay khi bạn ngắt lời 0.9 giây."""
    print("\n🎙️ [ĐANG NGHE... Sếp cứ nói tự nhiên, ngừng nói 1 giây là Tèo tự trả lời!]")
    frames = []
    has_spoken = False
    silent_chunks = 0
    max_silent_chunks = int(silence_limit_sec / CHUNK_DURATION)
    max_total_chunks = int(max_sec / CHUNK_DURATION)

    # Ngưỡng độ to giọng nói
    SPEECH_THRESHOLD = 450

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            for _ in range(max_total_chunks):
                chunk, _ = stream.read(CHUNK_SAMPLES)
                frames.append(chunk.copy())

                rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if rms > SPEECH_THRESHOLD:
                    if not has_spoken:
                        print("   🗣️ (Đã bắt được giọng của sếp...)")
                    has_spoken = True
                    silent_chunks = 0
                else:
                    if has_spoken:
                        silent_chunks += 1
                        if silent_chunks >= max_silent_chunks:
                            break
    except Exception as e:
        print(f"⚠️ Lỗi truy cập Micro: {e}")
        return filename, False

    if not frames:
        return filename, False

    audio_data = np.concatenate(frames, axis=0)
    wav.write(filename, SAMPLE_RATE, audio_data)
    return filename, has_spoken


def speech_to_text(audio_path: str) -> str:
    """Dịch giọng nói sang chữ (Speech-to-Text miễn phí, không cần Groq)."""
    t0 = time.perf_counter()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="vi-VN")
            latency = (time.perf_counter() - t0) * 1000
            print(f"👂 [Google ASR ({latency:.0f} ms)]: \"{text}\"")
            return text
    except sr.UnknownValueError:
        print("⚠️ Tèo không nghe rõ sếp vừa nói gì, sếp nói lại giúp em nhé.")
        return ""
    except Exception as e:
        print(f"⚠️ Lỗi nhận diện giọng nói: {e}")
        return ""


async def fetch_tts_bytes(sentence: str) -> tuple[bytes, float, str]:
    """Tải âm thanh của 1 câu ngắn vào thẳng bộ nhớ RAM (BytesIO) không qua ổ cứng."""
    t0 = time.perf_counter()
    try:
        lang = detect(sentence)
    except Exception:
        lang = "vi"
    voice = VOICE_MAP.get(lang, "vi-VN-NamMinhNeural")

    audio_buffer = bytearray()
    for attempt in range(2):
        try:
            comm = edge_tts.Communicate(text=sentence, voice=voice, rate="+12%")
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    audio_buffer.extend(chunk["data"])
            if audio_buffer:
                break
        except Exception:
            if attempt == 1:
                break
            await asyncio.sleep(0.2)

    latency = (time.perf_counter() - t0) * 1000
    return bytes(audio_buffer), latency, voice


async def speak_pipelined(full_reply: str):
    """Kỹ thuật cuốn chiếu: Phát câu 1 ngay lập tức trong khi tải ngầm câu 2, 3."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", full_reply) if s.strip()]
    if not sentences:
        return

    tasks = [asyncio.create_task(fetch_tts_bytes(s)) for s in sentences]

    for idx, (sentence, task) in enumerate(zip(sentences, tasks)):
        audio_bytes, tts_ms, voice = await task
        if not audio_bytes:
            continue
        if idx == 0:
            print(f"⚡ [Tèo TTS Câu 1 ({tts_ms:.0f} ms | {voice})]: Phát âm thanh ngay!")
        print(f"   🤖 [Tèo nói câu {idx+1}]: {sentence}")

        soundStream = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(soundStream)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.03)
        pygame.mixer.music.unload()


async def main():
    print("=== BƯỚC 0.2: ĐÀM THOẠI VỚI ROBOT TÈO (DEEPSEEK API + EDGETTS) ===")
    print(f"-> Não bộ: DeepSeek ({MODEL_NAME}) | ASR: Google Free | TTS: EdgeTTS")
    print("-> Sếp có thể bấm [ENTER] để nói qua Mic, hoặc gõ chữ trực tiếp rồi bấm [ENTER]!\n")

    while True:
        try:
            cmd = input("👉 Bấm [ENTER] để nói (hoặc gõ chữ hỏi Tèo / 'q' để thoát): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTèo chào sếp, hẹn gặp lại sếp nhé!")
            break

        if cmd.lower() == "q":
            print("Tèo chào sếp, hẹn gặp lại sếp nhé!")
            break

        user_text = ""
        if cmd:
            # Người dùng gõ text trực tiếp
            user_text = cmd
            print(f"📝 [Sếp nhắn]: \"{user_text}\"")
        else:
            # Người dùng bấm ENTER để thu âm qua Mic
            wav_path, has_spoken = record_with_auto_vad()
            if not has_spoken:
                print("⚠️ Chưa nghe thấy tiếng nói, sếp thử nói to hơn một chút nhé!")
                continue
            user_text = speech_to_text(wav_path)
            if not user_text:
                continue

        # 3. LLM DeepSeek trả lời (kèm Dynamic Suffix Injection đẩy giờ xuống cuối)
        t_llm = time.perf_counter()
        now_str = time.strftime("%H:%M ngày %d/%m/%Y")
        chat_history.append({"role": "user", "content": f"[Giờ hệ thống: {now_str}] {user_text}"})

        try:
            resp = llm_client.chat.completions.create(
                model=MODEL_NAME,
                messages=chat_history,
                temperature=0.6,
                max_tokens=180,
            )
            reply = resp.choices[0].message.content.strip()
            chat_history.append({"role": "assistant", "content": reply})
            latency_llm = (time.perf_counter() - t_llm) * 1000
            print(f"🧠 [DeepSeek suy nghĩ ({latency_llm:.0f} ms)]")

            # 4. Đọc cuốn chiếu từng câu qua EdgeTTS
            await speak_pipelined(reply)
        except Exception as e:
            print(f"❌ Lỗi khi gọi DeepSeek API: {e}")


if __name__ == "__main__":
    asyncio.run(main())
