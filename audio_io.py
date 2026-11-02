import asyncio
import contextlib
import io
import re
import time
import urllib.parse
import wave
import aiohttp
import edge_tts
import numpy as np
import pygame
import scipy.io.wavfile as wav
import sounddevice as sd
import speech_recognition as sr
from langdetect import detect
from piper.config import SynthesisConfig
from piper.voice import PiperVoice

import config
from config import (
    CHUNK_DURATION,
    CHUNK_SAMPLES,
    PIPER_PROFILES,
    SAMPLE_RATE,
    SPEECH_THRESHOLD,
    VN_CHARS_RE,
    VOICE_MAP,
)

# Thử nạp pycaw để tự động hạ nhỏ nhạc trình duyệt khi Tèo đang nghe
try:
    from pycaw.pycaw import AudioUtilities
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

pygame.mixer.init()
recognizer = sr.Recognizer()
edge_lock = asyncio.Lock()
edge_cooldown_until = 0.0

try:
    detect("Khởi động hệ thống tiếng Việt")
except Exception:
    pass


def set_background_music_volume(duck: bool):
    """Tự động hạ nhạc trình duyệt (Chrome/Edge/Spotify/mpv) xuống 15% khi sếp đang nói."""
    if not HAS_PYCAW:
        return
    target_apps = {"chrome.exe", "msedge.exe", "spotify.exe", "mpv.exe", "firefox.exe"}
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() in target_apps:
                vol = session.SimpleAudioVolume
                vol.SetMasterVolume(0.15 if duck else 1.0, None)
    except Exception:
        pass


def detect_lang_fast(text: str) -> str:
    """Nhận diện nhanh tiếng Việt bằng bảng mã dấu, chỉ gọi langdetect khi không có dấu."""
    if VN_CHARS_RE.search(text):
        return "vi"
    try:
        return detect(text)
    except Exception:
        return "vi"


def clean_for_tts(text: str) -> str:
    """Làm sạch ký tự đặc biệt và dấu '...' tránh lỗi NoAudioReceived của EdgeTTS."""
    text = re.sub(r"\.{2,}", ",", text)
    text = re.sub(r"[*#_~`🎵🎶🤖🎙️]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def record_with_auto_vad(filename="mic_input.wav", silence_limit_sec=0.7, max_sec=15.0):
    """Thu âm tự động ngắt khi sếp dừng nói 0.7 giây."""
    print("\n🎙️ [ĐANG NGHE... Sếp cứ nói tự nhiên, ngừng nói 0.7 giây là Tèo tự trả lời!]")
    set_background_music_volume(duck=True)
    frames = []
    has_spoken = False
    silent_chunks = 0
    max_silent_chunks = int(silence_limit_sec / CHUNK_DURATION)
    max_total_chunks = int(max_sec / CHUNK_DURATION)

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
        set_background_music_volume(duck=False)
        return filename, False

    if not frames:
        set_background_music_volume(duck=False)
        return filename, False

    audio_data = np.concatenate(frames, axis=0)
    wav.write(filename, SAMPLE_RATE, audio_data)
    return filename, has_spoken


def speech_to_text(audio_path: str) -> str:
    """Chuyển giọng nói sang văn bản bằng Google ASR."""
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


_piper_cache: dict[str, PiperVoice] = {}


def get_piper_voice(model_path) -> PiperVoice | None:
    """Tải và lưu trữ vào RAM mô hình Piper ONNX tương ứng."""
    path_str = str(model_path)
    if path_str not in _piper_cache:
        if model_path.exists():
            try:
                _piper_cache[path_str] = PiperVoice.load(path_str)
            except Exception as e:
                print(f"⚠️ Không tải được Piper voice {model_path.name}: {e}")
                return None
    return _piper_cache.get(path_str)


def fetch_piper_tts_sync(text: str, profile_name: str = "chipmunk") -> tuple[bytes, str]:
    """
    Sinh âm thanh Offline bằng Piper VITS tiếng Việt đã sửa dấu.
    Hỗ trợ chỉnh tông giọng sóc chuột hoặc giữ nguyên giọng nam trầm nguyên bản.
    """
    profile = PIPER_PROFILES.get(profile_name, PIPER_PROFILES["chipmunk"])
    voice = get_piper_voice(profile["model"])
    if not voice:
        return b"", ""

    try:
        syn_cfg = SynthesisConfig(length_scale=profile.get("length_scale", 1.0))
        raw_pcm = bytearray()
        base_sr = 22050
        with contextlib.redirect_stderr(io.StringIO()):
            for chunk in voice.synthesize(text, syn_config=syn_cfg):
                raw_pcm.extend(chunk.audio_int16_bytes)
                base_sr = chunk.sample_rate

        if not raw_pcm:
            return b"", ""

        factor = profile.get("factor", 1.0)
        target_sr = int(base_sr * factor)

        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(target_sr)
            wf.writeframes(raw_pcm)

        return wav_io.getvalue(), profile["label"]
    except Exception as e:
        print(f"⚠️ Lỗi tổng hợp Piper TTS: {e}")
        return b"", ""


# Khởi động sẵn mô hình mặc định vào RAM
if "chipmunk" in PIPER_PROFILES:
    get_piper_voice(PIPER_PROFILES["chipmunk"]["model"])


async def fetch_google_tts_fast(
    http_session: aiohttp.ClientSession, text: str, lang: str = "vi"
) -> tuple[bytes, str]:
    """Luồng Google TTS HTTP Keep-Alive: phát âm chuẩn tiếng Việt, phản xạ tức thì (~150-250ms)."""
    tl = "zh-CN" if lang.startswith("zh") else lang
    q = urllib.parse.quote(text)
    url = f"https://translate.googleapis.com/translate_tts?ie=UTF-8&client=tw-ob&tl={tl}&q={q}"
    try:
        async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
            if resp.status == 200:
                return await resp.read(), f"GoogleTTS ({tl})"
    except Exception:
        pass
    return b"", f"GoogleTTS ({tl})"


async def fetch_edge_tts_raw(text: str, voice: str) -> bytes:
    """Gọi EdgeTTS tuần tự qua khóa độc quyền."""
    async with edge_lock:
        comm = edge_tts.Communicate(text=text, voice=voice, rate="+10%")
        buf = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                buf.extend(chunk["data"])
        return bytes(buf)


async def fetch_tts_bytes_smart(
    http_session: aiohttp.ClientSession,
    sentence: str,
    is_first_sentence: bool = True,
    prefer_fast: bool = False,
) -> tuple[bytes, float, str, bool]:
    """
    Cơ chế TTS đa tầng thông minh:
    - Mặc định: Piper Offline (chipmunk, diemdam, tramvang) siêu tốc ~80-120ms, không độ trễ, không phụ thuộc mạng.
    - Hỗ trợ chuyển đổi dễ dàng qua biến môi trường TEO_TTS_MODE.
    - Fallback tự động sang GoogleTTS/EdgeTTS đối với ngoại ngữ (en, zh, ja).
    """
    global edge_cooldown_until
    t0 = time.perf_counter()
    clean_sent = clean_for_tts(sentence)
    if not re.search(r"\w", clean_sent):
        return b"", 0.0, "", prefer_fast

    lang = detect_lang_fast(clean_sent)

    # 1. Chế độ Piper Offline đa phong cách (Sóc Chuột / Nam Trầm Điềm Đạm / Nam Trầm Vang)
    current_mode = getattr(config, "TTS_MODE", "chipmunk").lower()
    if current_mode in PIPER_PROFILES and lang == "vi":
        audio_bytes, voice_tag = await asyncio.to_thread(fetch_piper_tts_sync, clean_sent, current_mode)
        if audio_bytes:
            ms = (time.perf_counter() - t0) * 1000
            return audio_bytes, ms, voice_tag, False

    # 2. Chế độ EdgeTTS (edge, auto)
    if current_mode in ("edge", "auto") and not prefer_fast and time.time() >= edge_cooldown_until:
        voice = VOICE_MAP.get(lang, "vi-VN-NamMinhNeural")
        timeout_sec = 0.70 if is_first_sentence else 2.2
        edge_task = asyncio.create_task(fetch_edge_tts_raw(clean_sent, voice))
        fast_task = asyncio.create_task(fetch_google_tts_fast(http_session, clean_sent, lang))

        done, _ = await asyncio.wait({edge_task}, timeout=timeout_sec)
        if edge_task in done and not edge_task.exception() and edge_task.result():
            fast_task.cancel()
            return edge_task.result(), (time.perf_counter() - t0) * 1000, voice, False

        edge_task.cancel()
        edge_cooldown_until = time.time() + 90.0
        fast_audio, fast_voice = await fast_task
        return fast_audio, (time.perf_counter() - t0) * 1000, fast_voice, True

    # 3. Fallback sang Google TTS (fast / google hoặc ngoại ngữ en, zh, ja)
    fast_audio, fast_voice = await fetch_google_tts_fast(http_session, clean_sent, lang)
    return fast_audio, (time.perf_counter() - t0) * 1000, fast_voice, True
