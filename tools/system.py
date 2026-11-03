"""
Group 4 & Group 6: System Diagnostics, TTS Voice Switcher & 3D Robot Omni/Motion Bundles.
- Laptop health (CPU, RAM, Battery, Disk, NVIDIA RTX 3050 GPU temperature and VRAM).
- Full hardware specifications (CPU model, physical/logical cores, total RAM, GPU, OS).
- TTS voice switcher with model validation & persistent settings (TL-17).
- 3D MuJoCo Motion Bundles & 3-Wheel Omni Kiwi Drive (LeKiwi) with clamped motion & 2-way UDP ACK (TL-03).
"""

import json
import logging
import math
import platform
import socket
import subprocess
import sys
import uuid
from typing import Any

import psutil

import config
from config import PIPER_PROFILES, UDP_SIM_TARGET
from tools.common import update_json

if sys.platform == "win32":
    import winreg

log = logging.getLogger("teo.system")

# --- 3D MuJoCo Simulation: Motion Bundles & 3-Wheel Omni Kiwi Drive (LeKiwi) ---

BASE_MOTIONS = {
    "moonwalk_dance",
    "move_forward",
    "move_backward",
    "slide_left",
    "slide_right",
    "circle_strafe",
    "spin_around",
}

VALID_MOTIONS = {
    "wave_greeting",
    "nod_yes",
    "shake_no",
    "look_around",
    "happy_dance",
    "moonwalk_dance",
    "idle",
}

VALID_OMNI_MOVES = {
    "move_forward",
    "move_backward",
    "slide_left",
    "slide_right",
    "circle_strafe",
    "spin_around",
    "idle",
}

MAX_BODY_SEC = 8.0
MAX_BASE_SEC = 3.0
MIN_SEC = 0.5

MOTION_LABELS = {
    "wave_greeting": "vẫy tay chào và nghiêng đầu",
    "nod_yes": "gật đầu đồng ý",
    "shake_no": "lắc đầu từ chối",
    "look_around": "xoay cổ nhìn quanh tìm sếp",
    "happy_dance": "nhảy múa tại chỗ theo nhịp nhạc",
    "moonwalk_dance": "nhảy trượt ngang Moonwalk đa hướng trên đế 3 bánh Omni",
    "idle": "đứng yên nghỉ ngơi",
}

OMNI_MOVE_LABELS = {
    "move_forward": "tiến lên phía trước",
    "move_backward": "lùi lại phía sau",
    "slide_left": "trượt ngang sang trái giữ nguyên ánh mắt nhìn sếp",
    "slide_right": "trượt ngang sang phải giữ nguyên ánh mắt nhìn sếp",
    "circle_strafe": "lượn vòng cung quanh mặt bàn giữ nguyên hướng mắt nhìn sếp",
    "spin_around": "xoay tròn 360 độ tại chỗ",
    "idle": "dừng đứng yên",
}


def build_motion(motion: str, duration: Any, bpm: Any, is_omni: bool = False) -> tuple[str, float, int]:
    """Validate motion identifier, enforce strict duration clamping and finite numbers (TL-03)."""
    allowed = VALID_OMNI_MOVES if is_omni else VALID_MOTIONS
    if motion not in allowed:
        raise ValueError(f"unknown motion: {motion}")

    try:
        dur = float(duration)
    except (TypeError, ValueError):
        dur = 2.0 if is_omni else 3.5

    if not math.isfinite(dur):
        raise ValueError("duration must be finite")

    cap = MAX_BASE_SEC if (motion in BASE_MOTIONS or motion == "happy_dance" or is_omni) else MAX_BODY_SEC
    clamped_dur = max(MIN_SEC, min(cap, dur))

    try:
        bpm_val = int(bpm)
    except (TypeError, ValueError):
        bpm_val = 120 if is_omni else 125
    clamped_bpm = max(60, min(160, bpm_val))

    return motion, clamped_dur, clamped_bpm


def send_motion_to_3d_sim(motion: str, duration: float = 3.0, bpm: int = 120, timeout: float = 0.4) -> bool:
    """Send UDP motion packet to 3D MuJoCo sim with 2-way ACK check (TL-03)."""
    msg_id = uuid.uuid4().hex[:8]
    payload = json.dumps({
        "id": msg_id,
        "motion": motion,
        "duration": duration,
        "bpm": bpm,
    }).encode("utf-8")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            s.sendto(payload, UDP_SIM_TARGET)
            data, _ = s.recvfrom(256)
            ack_msg = json.loads(data.decode("utf-8"))
            return ack_msg.get("ack") == msg_id
    except (OSError, ValueError):
        return False


def tool_dieu_khien_co_the_teo(args: dict) -> str:
    """Execute expressive upper-body gesture or Omni dance bundle (wave, nod, shake, happy_dance, moonwalk_dance)."""
    motion = args.get("hanh_dong") or "wave_greeting"
    try:
        motion, dur, bpm = build_motion(motion, args.get("so_giay", 3.5), args.get("bpm", 125), is_omni=False)
    except ValueError as err:
        return f"ERROR invalid_arguments: {err}"

    ok = send_motion_to_3d_sim(motion, dur, bpm)
    if ok is False:
        return "ERROR robot_unreachable: motion was NOT executed."

    desc = MOTION_LABELS.get(motion, motion)
    dur_str = str(round(dur, 1)).replace(".", ",")
    return f"Đã thực hiện cử chỉ {motion} ({desc}) trong {dur_str} giây."


def tool_di_chuyen_da_huong_omni(args: dict) -> str:
    """Control 3-Wheel Omni Kiwi Drive (LeKiwi) holonomic base on desk with strict clamping (TL-03)."""
    move = args.get("huong_di") or "slide_left"
    try:
        move, dur, bpm = build_motion(move, args.get("so_giay", 2.0), args.get("bpm", 120), is_omni=True)
    except ValueError as err:
        return f"ERROR invalid_arguments: {err}"

    ok = send_motion_to_3d_sim(move, dur, bpm)
    if ok is False:
        return "ERROR robot_unreachable: motion was NOT executed."

    desc = OMNI_MOVE_LABELS.get(move, move)
    dur_str = str(round(dur, 1)).replace(".", ",")
    return f"Đế 3 bánh Omni đã {desc} ({move}) trong {dur_str} giây."


# --- Laptop Health & Hardware Specs ---

def get_gpu_live_status() -> str:
    """Read temperature and VRAM usage of NVIDIA GPU via nvidia-smi."""
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            stderr=subprocess.DEVNULL,
            timeout=1.5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        ).decode("utf-8", errors="ignore").strip()
        if out:
            parts = [p.strip() for p in out.splitlines()[0].split(",")]
            if len(parts) >= 4:
                name, temp, mem_used, mem_total = parts[:4]
                return f"{name} nhiệt độ {temp} độ C, VRAM đang dùng {mem_used} trên {mem_total} MB"
    except Exception:
        pass
    return ""


def get_hardware_specs() -> str:
    """Extract hardware specifications: CPU, cores, RAM, GPU, SSD disks, OS."""
    # 1. CPU
    cpu_name = platform.processor()
    if sys.platform == "win32":
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            val, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            cpu_name = val.strip()
        except Exception:
            pass
    cores_phys = psutil.cpu_count(logical=False) or 0
    cores_log = psutil.cpu_count(logical=True) or 0

    # 2. RAM
    ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)

    # 3. GPU (filter basic display adapter - TL-20)
    gpus = []
    if sys.platform == "win32":
        try:
            path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            for i in range(20):
                try:
                    sub = winreg.EnumKey(key, i)
                    sub_key = winreg.OpenKey(key, sub)
                    try:
                        name, _ = winreg.QueryValueEx(sub_key, "DriverDesc")
                        if name and "Basic Display" not in name and name not in gpus:
                            gpus.append(name)
                    except Exception:
                        pass
                except OSError:
                    break
        except Exception:
            pass
    gpu_str = ", ".join(gpus) if gpus else "Không phát hiện card rời"

    # 4. Storage disks
    disks = []
    for part in psutil.disk_partitions(all=False):
        if "fixed" in part.opts or not part.opts:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_gb = round(usage.total / (1024**3), 1)
                free_gb = round(usage.free / (1024**3), 1)
                drive_letter = part.device.replace("\\", "").rstrip(":")
                disks.append(f"ổ {drive_letter} (tổng {total_gb} GB, còn trống {free_gb} GB)")
            except Exception:
                pass
    disk_str = ", ".join(disks) if disks else "không rõ"

    # 5. OS
    os_name = f"{platform.system()} {platform.release()}"
    try:
        ver_parts = [int(x) for x in platform.version().split(".") if x.isdigit()]
        if len(ver_parts) >= 3 and ver_parts[2] >= 22000:
            os_name = "Windows 11"
    except Exception:
        pass

    return (
        f"Cấu hình máy tính của sếp: "
        f"Vi xử lý {cpu_name} ({cores_phys} nhân thực, {cores_log} luồng). "
        f"Bộ nhớ RAM {ram_gb} GB. "
        f"Card màn hình {gpu_str}. "
        f"Ổ cứng {disk_str}. "
        f"Hệ điều hành {os_name} 64-bit."
    )


def tool_kiem_tra_suc_khoe_laptop(args: dict) -> str:
    """Check live laptop health or full hardware specs. Prevents dGPU wake-up in fast mode (TL-20)."""
    mode = args.get("che_do", "nhanh")
    cpu = psutil.cpu_percent(interval=0.05)
    ram = psutil.virtual_memory().percent
    bat = psutil.sensors_battery()
    bat_info = (
        f"{bat.percent}% ({'đang cắm sạc' if bat.power_plugged else 'đang dùng pin'})"
        if bat
        else "không rõ"
    )

    disk_parts = []
    for part in psutil.disk_partitions(all=False):
        if "fixed" in part.opts or not part.opts:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                free_gb = round(usage.free / (1024**3), 1)
                drive = part.device.replace("\\", "").rstrip(":")
                disk_parts.append(f"ổ {drive} trống {free_gb} GB")
            except Exception:
                pass
    disk_info = ", ".join(disk_parts) if disk_parts else ""

    # In fast mode, do NOT wake dGPU to save power (TL-20)
    gpu_live = get_gpu_live_status() if mode == "chi_tiet" else ""

    live_str = f"Laptop của sếp đang dùng {cpu}% CPU, {ram}% RAM, pin ở mức {bat_info}"
    if disk_info:
        live_str += f", {disk_info}"
    if gpu_live:
        live_str += f", card rời {gpu_live}"
    live_str += "."

    if mode == "chi_tiet":
        specs = get_hardware_specs()
        return f"{specs} Trạng thái hiện tại: {live_str}"
    return live_str


# --- Voice Profile Switcher (TL-17) ---

VOICE_LABELS = {
    "chipmunk": "Tèo Sóc Chuột vui nhộn",
    "diemdam": "Tèo Nam Trầm điềm đạm",
    "tramvang": "Tèo Nam Trầm vang",
    "google": "Chị Google chuẩn ngữ âm",
}


def tool_doi_giong_noi_teo(args: dict) -> str:
    """Switch TTS voice profile with model validation and settings persistence (TL-17)."""
    voice = (args.get("giong") or "chipmunk").lower().strip()
    if voice not in VOICE_LABELS:
        return (
            f"Giọng '{voice}' không hợp lệ. Sếp có thể chọn: "
            "chipmunk (Sóc chuột), diemdam (Nam trầm điềm đạm), tramvang (Nam trầm vang), hoặc google."
        )

    # Validate that the Piper model file can actually be loaded (TL-17)
    if voice in PIPER_PROFILES:
        try:
            from audio_io import get_piper_voice
            model_path = PIPER_PROFILES[voice]["model"]
            if not model_path.exists() or get_piper_voice(model_path) is None:
                return f"ERROR voice_unavailable: model for '{voice}' is not installed. Voice unchanged."
        except Exception:
            pass

    config.TTS_MODE = voice
    # Persist chosen voice profile to teo_settings.json
    try:
        update_json(config.SETTINGS_FILE, {}, lambda s: s.update({"tts_mode": voice}))
    except Exception:
        pass

    label = VOICE_LABELS[voice]
    return f"Đã đổi giọng nói của em sang chế độ {label} theo ý sếp."
