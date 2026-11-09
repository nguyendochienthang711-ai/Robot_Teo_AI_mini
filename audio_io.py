import asyncio
import contextlib
import io
import logging
import re
import threading
import time
import urllib.parse
import wave
import aiohttp
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
)

log = logging.getLogger("teo.audio")

# Thử nạp pycaw để tự động hạ nhỏ nhạc trình duyệt khi Tèo đang nghe
try:
    from pycaw.pycaw import AudioUtilities
    HAS_PYCAW = True
except Exception:
    HAS_PYCAW = False

recognizer = sr.Recognizer()
audio_play_lock = threading.RLock()
_saved_volumes: dict[int, float] = {}
_mixer_initialized = False


def ensure_mixer_init() -> bool:
    """Lazy-initialize pygame.mixer on first playback need (R-20)."""
    global _mixer_initialized
    if _mixer_initialized and pygame.mixer.get_init():
        return True
    try:
        pygame.mixer.init()
        _mixer_initialized = True
        return True
    except Exception as e:
        log.warning("Failed to initialize pygame.mixer: %s", e)
        return False


def _raw_play_audio_bytes_sync(audio_bytes: bytes, abort_event: threading.Event | None = None) -> None:
    """Low-level thread-safe serialized playback on pygame.mixer.music (R-08)."""
    if not audio_bytes or not ensure_mixer_init():
        return
    with audio_play_lock:
        try:
            sound_stream = io.BytesIO(audio_bytes)
            pygame.mixer.music.load(sound_stream)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if abort_event is not None and abort_event.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.02)
        finally:
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass


def play_audio_bytes_sync(
    audio_bytes: bytes,
    abort_event: threading.Event | None = None,
    priority: int = 1,
    label: str = "speech",
) -> None:
    """Priority-aware playback routed through PriorityAudioBus (TL-09, R-08)."""
    if not audio_bytes:
        return
    try:
        from teo_harness import audio_bus
        audio_bus.play_sync(
            audio_bytes,
            priority=priority,
            abort_event=abort_event,
            label=label,
            playback_fn=_raw_play_audio_bytes_sync,
        )
    except Exception:
        _raw_play_audio_bytes_sync(audio_bytes, abort_event)


def stop_audio_playback() -> None:
    """Immediately stop any active pygame.mixer playback (R-24)."""
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass


def set_background_music_volume(duck: bool):
    """Tự động hạ nhạc trình duyệt xuống 15% khi sếp đang nói và khôi phục đúng mức âm lượng cũ (R-23)."""
    if not HAS_PYCAW:
        return
    target_apps = {"chrome.exe", "msedge.exe", "spotify.exe", "mpv.exe", "firefox.exe"}
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() in target_apps:
                pid = session.Process.pid
                vol = session.SimpleAudioVolume
                if duck:
                    if pid not in _saved_volumes:
                        try:
                            _saved_volumes[pid] = float(vol.GetMasterVolume())
                        except Exception:
                            _saved_volumes[pid] = 1.0
                    vol.SetMasterVolume(min(_saved_volumes[pid], 0.15), None)
                else:
                    orig = _saved_volumes.pop(pid, 1.0)
                    vol.SetMasterVolume(orig, None)
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
    """Làm sạch ký tự đặc biệt và dấu '...' tránh lỗi của bộ đọc TTS."""
    text = re.sub(r"\.{2,}", ",", text)
    text = re.sub(r"[*#_~`🎵🎶🤖🎙️]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def record_with_auto_vad(filename: str | None = None, silence_limit_sec: float = 0.7, max_sec: float = 15.0):
    """Thu âm tự động ngắt khi sếp dừng nói 0.7 giây (lưu file tạm trong CACHE_DIR - R-20)."""
    if filename is None:
        filename = str(config.CACHE_DIR / "mic_input.wav")
    print("\n🎙️ [ĐANG NGHE... Sếp cứ nói tự nhiên, ngừng nói 0.7 giây là Tèo tự trả lời!]")
    set_background_music_volume(duck=True)
    try:
        from teo_harness import state_machine
        state_machine.set_state("LISTENING", detail="mic_recording")
    except Exception:
        pass
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
        try:
            from teo_harness import state_machine
            state_machine.set_state("IDLE", detail="mic_error")
        except Exception:
            pass
        return filename, False

    if not frames:
        set_background_music_volume(duck=False)
        try:
            from teo_harness import state_machine
            state_machine.set_state("IDLE", detail="mic_empty")
        except Exception:
            pass
        return filename, False

    audio_data = np.concatenate(frames, axis=0)
    wav.write(filename, SAMPLE_RATE, audio_data)
    try:
        from teo_harness import state_machine
        state_machine.set_state("THINKING" if has_spoken else "IDLE", detail="mic_done")
    except Exception:
        pass
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
_piper_lock = threading.Lock()


def get_piper_voice(model_path) -> PiperVoice | None:
    """Tải lười (lazy-load) và lưu trữ vào RAM mô hình Piper ONNX tương ứng (R-20)."""
    path_str = str(model_path)
    with _piper_lock:
        if path_str not in _piper_cache:
            if model_path.exists():
                try:
                    _piper_cache[path_str] = PiperVoice.load(path_str)
                except Exception as e:
                    print(f"⚠️ Không tải được Piper voice {model_path.name}: {e}")
                    return None
        return _piper_cache.get(path_str)


def warmup_piper_default() -> None:
    """Khởi động sẵn mô hình mặc định vào RAM khi chạy ứng dụng chính (R-20)."""
    mode = getattr(config, "TTS_MODE", "chipmunk").lower()
    if mode in PIPER_PROFILES:
        get_piper_voice(PIPER_PROFILES[mode]["model"])


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


async def fetch_google_tts_fast(
    http_session: aiohttp.ClientSession, text: str, lang: str = "vi"
) -> tuple[bytes, str]:
    """Luồng Google TTS HTTP Keep-Alive, tự chia nhỏ chuỗi ≤ 180 ký tự (R-22)."""
    tl = "zh-CN" if lang.startswith("zh") else lang
    chunks = [text[i : i + 180] for i in range(0, len(text), 180)] or [text]
    out_bytes = bytearray()
    try:
        for part in chunks:
            q = urllib.parse.quote(part)
            url = f"https://translate.googleapis.com/translate_tts?ie=UTF-8&client=tw-ob&tl={tl}&q={q}"
            async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    out_bytes.extend(await resp.read())
    except Exception:
        pass
    return bytes(out_bytes), f"GoogleTTS ({tl})"


async def fetch_tts_bytes_smart(
    http_session: aiohttp.ClientSession,
    sentence: str,
    is_first_sentence: bool = True,
    prefer_fast: bool = False,
) -> tuple[bytes, float, str, bool]:
    """
    Cơ chế TTS gọn nhẹ và ổn định:
    - Piper Offline (chipmunk, diemdam, tramvang) ~60-120ms.
    - Fallback trực tiếp sang Google TTS cho chế độ google hoặc ngoại ngữ.
    """
    t0 = time.perf_counter()
    clean_sent = clean_for_tts(sentence)
    if not re.search(r"\w", clean_sent):
        return b"", 0.0, "", prefer_fast

    lang = detect_lang_fast(clean_sent)

    current_mode = getattr(config, "TTS_MODE", "chipmunk").lower()
    if current_mode in PIPER_PROFILES and lang == "vi":
        audio_bytes, voice_tag = await asyncio.to_thread(fetch_piper_tts_sync, clean_sent, current_mode)
        if audio_bytes:
            ms = (time.perf_counter() - t0) * 1000
            return audio_bytes, ms, voice_tag, False

    fast_audio, fast_voice = await fetch_google_tts_fast(http_session, clean_sent, lang)
    return fast_audio, (time.perf_counter() - t0) * 1000, fast_voice, True
