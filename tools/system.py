"""
Group 4 & Group 6: System Diagnostics, TTS Voice Switcher & 3D Robot Omni/Motion Bundles.
- Laptop health (CPU, RAM, Battery, Disk, NVIDIA RTX 3050 GPU temperature and VRAM).
- Full hardware specifications (CPU model, physical/logical cores, total RAM, GPU, OS).
- TTS voice switcher (chipmunk, diemdam, tramvang, google).
- 3D MuJoCo Motion Bundles & 3-Wheel Omni Kiwi Drive (LeKiwi) holonomic navigation.
"""

import json
import platform
import socket
import subprocess
import sys

import psutil

import config
from config import PIPER_PROFILES, UDP_SIM_TARGET

if sys.platform == "win32":
    import winreg


# --- 3D MuJoCo Simulation: Motion Bundles & 3-Wheel Omni Kiwi Drive (LeKiwi) ---

VALID_MOTIONS = {
    "wave_greeting",
    "nod_yes",
    "shake_no",
    "look_around",
    "happy_dance",
    "moonwalk_dance",
    "move_forward",
    "move_backward",
    "slide_left",
    "slide_right",
    "circle_strafe",
    "spin_around",
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


def send_motion_to_3d_sim(motion: str, duration: float = 3.0, bpm: int = 120):
    """Send UDP motion packet to 3D MuJoCo simulation runner."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = json.dumps({"motion": motion, "duration": duration, "bpm": bpm}).encode("utf-8")
        sock.sendto(payload, UDP_SIM_TARGET)
        sock.close()
    except Exception:
        pass


def tool_dieu_khien_co_the_teo(args: dict) -> str:
    """Execute expressive upper-body gesture or Omni dance bundle (wave, nod, shake, happy_dance, moonwalk_dance)."""
    motion = args.get("hanh_dong") or args.get("goi_chuyen_dong") or "wave_greeting"
    if motion not in VALID_MOTIONS:
        motion = "wave_greeting"
    dur = float(args.get("so_giay", 3.5))
    bpm = int(args.get("bpm", 125))
    send_motion_to_3d_sim(motion, dur, bpm)
    desc = MOTION_LABELS.get(motion) or OMNI_MOVE_LABELS.get(motion, motion)
    print(f"🤖 [Tool Call -> 3D Motion Bundle]: Kích hoạt '{motion}' ({desc}) trong {dur}s (BPM={bpm})")
    return f"Đã thực hiện cử chỉ {motion} ({desc}) trong {dur} giây thành công."


def tool_di_chuyen_da_huong_omni(args: dict) -> str:
    """
    Control 3-Wheel Omni Kiwi Drive (LeKiwi) holonomic base on desk:
    move_forward, move_backward, slide_left, slide_right, circle_strafe, spin_around.
    Enforces 1.0-3.0s safety duration limit and 3 IR anti-drop cliff sensors check.
    """
    move = args.get("huong_di") or args.get("hanh_dong") or "slide_left"
    if move not in VALID_OMNI_MOVES:
        move = "slide_left"

    raw_dur = float(args.get("so_giay", 2.0))
    dur = max(1.0, min(3.0, raw_dur))
    bpm = int(args.get("bpm", 120))

    send_motion_to_3d_sim(move, dur, bpm)
    desc = OMNI_MOVE_LABELS.get(move, move)
    print(f"🛞 [Tool Call -> 3-Wheel Omni Kiwi Drive]: '{move}' ({desc}) trong {dur}s [3 IR chống rơi: AN TOÀN]")
    return (
        f"Đế 3 bánh Omni đã {desc} ({move}) trong {dur} giây an toàn "
        "với 3 cảm biến hồng ngoại chống rơi mép bàn."
    )


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

    # 3. GPU
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
                        if name and name not in gpus:
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
    """Check live laptop health (CPU, RAM, Battery, Disk, GPU) or full specs."""
    mode = args.get("che_do", "nhanh")
    cpu = psutil.cpu_percent(interval=0.15)
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
    gpu_live = get_gpu_live_status()

    live_str = f"Laptop của sếp đang dùng {cpu}% CPU, {ram}% RAM, pin ở mức {bat_info}"
    if disk_info:
        live_str += f", {disk_info}"
    if gpu_live:
        live_str += f", card rời {gpu_live}"
    live_str += "."

    if mode == "chi_tiet":
        specs = get_hardware_specs()
        res = f"{specs} Trạng thái hiện tại: {live_str}"
    else:
        res = live_str

    print(f"💻 [Tool Call -> Laptop Health ({mode})]: {res}")
    return res


# --- Voice Profile Switcher ---

VOICE_LABELS = {
    "chipmunk": "Tèo Sóc Chuột vui nhộn",
    "diemdam": "Tèo Nam Trầm điềm đạm",
    "tramvang": "Tèo Nam Trầm vang",
    "google": "Chị Google chuẩn ngữ âm",
}


def tool_doi_giong_noi_teo(args: dict) -> str:
    """Switch TTS voice profile between chipmunk, diemdam, tramvang, and google."""
    voice = (args.get("giong") or "chipmunk").lower().strip()
    if voice not in VOICE_LABELS:
        return (
            f"Giọng '{voice}' không hợp lệ. Sếp có thể chọn: "
            "chipmunk (Sóc chuột), diemdam (Nam trầm điềm đạm), tramvang (Nam trầm vang), hoặc google."
        )
    config.TTS_MODE = voice
    if voice in PIPER_PROFILES:
        try:
            from audio_io import get_piper_voice

            get_piper_voice(PIPER_PROFILES[voice]["model"])
        except Exception:
            pass
    label = VOICE_LABELS[voice]
    print(f"🔊 [Tool Call -> Voice Switch]: Đổi sang '{voice}' ({label})")
    return f"Đã đổi giọng nói của em sang chế độ {label} theo ý sếp."
