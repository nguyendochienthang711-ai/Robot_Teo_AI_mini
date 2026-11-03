"""
Group 5: Entertainment, YouTube Background Audio & System Media Control.
- Background YouTube player (mpv / ffplay / headless Edge or Chrome) without showing windows.
- Virtual media keys (play/pause, next, previous, volume up/down, mute).
- Fully compatible with pycaw auto-ducking.
"""

import ctypes
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import requests

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_STOP = 0xB2
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

_bg_music_proc: subprocess.Popen | None = None


def _stop_background_music():
    """Kill existing background music process if active."""
    global _bg_music_proc
    if _bg_music_proc is not None:
        try:
            if _bg_music_proc.poll() is None:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(_bg_music_proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                else:
                    _bg_music_proc.terminate()
        except Exception:
            pass
        _bg_music_proc = None


def _play_youtube_background(url: str) -> str:
    """
    Play YouTube music in background without opening any visible window:
    1. mpv --no-video (if available)
    2. yt-dlp + ffplay -nodisp (if available)
    3. Headless/Off-screen Edge/Chrome with autoplay and dedicated profile (default on Windows).
    """
    global _bg_music_proc
    _stop_background_music()

    no_win_flag = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    # Tier 1: mpv --no-video
    mpv_bin = shutil.which("mpv")
    if mpv_bin:
        _bg_music_proc = subprocess.Popen(
            [mpv_bin, "--no-video", "--ytdl=yes", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=no_win_flag,
        )
        return "mpv (chạy ngầm)"

    # Tier 2: yt-dlp + ffplay -nodisp
    ytdlp_bin = shutil.which("yt-dlp")
    ffplay_bin = shutil.which("ffplay")
    if ytdlp_bin and ffplay_bin:
        try:
            audio_url = (
                subprocess.check_output(
                    [ytdlp_bin, "-g", "-f", "bestaudio", url],
                    stderr=subprocess.DEVNULL,
                    timeout=6.0,
                    creationflags=no_win_flag,
                )
                .decode("utf-8", errors="ignore")
                .splitlines()[0]
                .strip()
            )
            if audio_url:
                _bg_music_proc = subprocess.Popen(
                    [ffplay_bin, "-nodisp", "-autoexit", "-loglevel", "quiet", audio_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=no_win_flag,
                )
                return "ffplay (chạy ngầm)"
        except Exception:
            pass

    # Tier 3: Off-screen hidden browser instance
    browser_candidates = [
        shutil.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    browser_bin = next((b for b in browser_candidates if b and os.path.exists(b)), None)
    if browser_bin:
        profile_dir = (Path.cwd() / ".teo_music_profile").resolve()
        autoplay_url = f"{url}&autoplay=1" if "?" in url else f"{url}?autoplay=1"
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

        _bg_music_proc = subprocess.Popen(
            [
                browser_bin,
                f"--user-data-dir={profile_dir}",
                f"--app={autoplay_url}",
                "--autoplay-policy=no-user-gesture-required",
                "--window-position=-32000,-32000",
                "--window-size=10,10",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=no_win_flag,
        )
        return "trình phát ngầm không cửa sổ"

    # Fallback
    webbrowser.open(url)
    return "trình duyệt"


def _send_media_key(vk_code: int, repeat: int = 1):
    """Simulate Windows media key press."""
    if sys.platform != "win32":
        return
    try:
        for _ in range(repeat):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
    except Exception:
        pass


def _find_youtube_video_url(query: str) -> str:
    """Find best matching YouTube video watch URL for given query."""
    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    try:
        resp = requests.get(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=3.5,
        )
        if resp.status_code == 200:
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if match:
                return f"https://www.youtube.com/watch?v={match.group(1)}"
    except Exception:
        pass
    return search_url


def tool_phat_nhac_va_dieu_khien_media(args: dict) -> str:
    """Play YouTube music in background without window or control media playback."""
    action = args.get("thao_tac", "phat_nhac")
    query = (args.get("tu_khoa") or "").strip()

    if action == "phat_nhac":
        if not query:
            return "Sếp muốn nghe bài hát gì thì nói tên bài hát cho em mở nhé."
        url = _find_youtube_video_url(query)
        engine = _play_youtube_background(url)
        print(f"🎵 [Tool Call -> Media ({engine})]: Phát ngầm '{query}' -> {url}")
        return f"Đã bật ngầm bài hát '{query}' cho sếp thưởng thức."

    elif action == "dung_nhac":
        _stop_background_music()
        _send_media_key(VK_MEDIA_STOP)
        return "Đã tắt trình phát nhạc ngầm."

    elif action in {"tam_dung", "tiep_tuc"}:
        _send_media_key(VK_MEDIA_PLAY_PAUSE)
        label = "tạm dừng" if action == "tam_dung" else "phát tiếp"
        return f"Đã {label} trình phát nhạc."

    elif action == "bai_tiep":
        _send_media_key(VK_MEDIA_NEXT_TRACK)
        return "Đã chuyển sang bài nhạc tiếp theo."

    elif action == "bai_truoc":
        _send_media_key(VK_MEDIA_PREV_TRACK)
        return "Đã quay lại bài nhạc trước đó."

    elif action == "tang_am":
        _send_media_key(VK_VOLUME_UP, repeat=5)
        return "Đã tăng âm lượng hệ thống lên cho sếp."

    elif action == "giam_am":
        _send_media_key(VK_VOLUME_DOWN, repeat=5)
        return "Đã giảm nhỏ âm lượng hệ thống xuống."

    elif action == "tat_tieng":
        _send_media_key(VK_VOLUME_MUTE)
        return "Đã bật hoặc tắt chế độ im lặng âm thanh."

    return f"Thao tác media '{action}' không hợp lệ."

