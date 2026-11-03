"""
Group 1: Personal Secretary, Time & Task Management.
- Todo tasks management: add, view, complete, delete, clear.
- Pomodoro and countdown timers with async alert callback and 3D arm waving.
"""

import io
import threading
import time
from pathlib import Path

import config
from tools.common import _load_json_file, _save_json_file, _strip_accents
from tools.system import send_motion_to_3d_sim


def tool_quan_ly_cong_viec(args: dict) -> str:
    """Manage the user's Todo task list."""
    action = args.get("thao_tac", "xem")
    content = (args.get("noi_dung") or "").strip()
    index = args.get("vi_tri")
    todos: list[dict] = _load_json_file(config.TODO_FILE, [])

    if action == "them":
        if not content:
            return "Sếp chưa nói nội dung công việc cần thêm."
        todos.append(
            {
                "task": content,
                "done": False,
                "time": time.strftime("%H:%M %d/%m"),
            }
        )
        _save_json_file(config.TODO_FILE, todos)
        print(f"📝 [Tool Call -> Todo]: Đã thêm '{content}'")
        return f"Đã lưu công việc '{content}' vào danh sách của sếp."

    elif action == "hoan_thanh":
        target_idx = None
        if isinstance(index, int) and 1 <= index <= len(todos):
            target_idx = index - 1
        elif content:
            norm_q = _strip_accents(content)
            for i, t in enumerate(todos):
                if norm_q in _strip_accents(t.get("task", "")):
                    target_idx = i
                    break
        if target_idx is None:
            return "Không tìm thấy công việc tương ứng để đánh dấu hoàn thành."
        todos[target_idx]["done"] = True
        _save_json_file(config.TODO_FILE, todos)
        task_name = todos[target_idx]["task"]
        print(f"✅ [Tool Call -> Todo]: Hoàn thành '{task_name}'")
        return f"Đã đánh dấu hoàn thành công việc '{task_name}'."

    elif action == "xoa":
        target_idx = None
        if isinstance(index, int) and 1 <= index <= len(todos):
            target_idx = index - 1
        elif content:
            norm_q = _strip_accents(content)
            for i, t in enumerate(todos):
                if norm_q in _strip_accents(t.get("task", "")):
                    target_idx = i
                    break
        if target_idx is None:
            return "Không tìm thấy công việc cần xóa trong danh sách."
        removed = todos.pop(target_idx)
        _save_json_file(config.TODO_FILE, todos)
        print(f"🗑️ [Tool Call -> Todo]: Đã xóa '{removed.get('task')}'")
        return f"Đã xóa công việc '{removed.get('task')}' khỏi danh sách."

    elif action == "xoa_het":
        _save_json_file(config.TODO_FILE, [])
        return "Đã xóa sạch danh sách công việc."

    # Default: view list
    if not todos:
        return "Hiện tại danh sách công việc của sếp đang trống."
    items_str = []
    for i, t in enumerate(todos):
        status = "đã xong" if t.get("done") else "chưa làm"
        items_str.append(f"Việc số {i + 1}: {t.get('task')} ({status})")
    summary = "; ".join(items_str)
    print(f"📋 [Tool Call -> Todo]: {summary}")
    return f"Danh sách hiện có {len(todos)} việc: {summary}."


# --- Pomodoro & Background Timers ---

_active_timers: list[dict] = []
_timer_lock = threading.Lock()
_timer_counter = 0


def _speak_alert_sync(message: str):
    """Play alert chime and speak reminder when timer ends, combined with 3D Omni slide & arm waving."""
    send_motion_to_3d_sim("moonwalk_dance", duration=4.0, bpm=130)
    print(f"\n⏰ [BÁO THỨC TÈO]: {message}")
    try:
        import pygame
        from audio_io import fetch_piper_tts_sync

        audio_bytes, _ = fetch_piper_tts_sync(message, getattr(config, "TTS_MODE", "chipmunk"))
        if audio_bytes and pygame.mixer.get_init():
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(io.BytesIO(audio_bytes))
                pygame.mixer.music.play()
    except Exception:
        pass


def tool_dong_ho_tap_trung_pomodoro(args: dict) -> str:
    """Set countdown timer / Pomodoro, check remaining time, or cancel timers."""
    global _timer_counter
    action = args.get("thao_tac", "dat_hen_gio")
    minutes = float(args.get("so_phut", 25))
    reminder = (
        args.get("loi_nhac")
        or "Hết giờ tập trung rồi sếp ơi, sếp nghỉ ngơi uống miếng nước và vươn vai nhé."
    ).strip()

    now = time.time()
    with _timer_lock:
        # Clear finished timers
        _active_timers[:] = [t for t in _active_timers if t["end_time"] > now]

        if action == "huy":
            if not _active_timers:
                return "Hiện không có bộ hẹn giờ nào đang chạy."
            count = len(_active_timers)
            for t in _active_timers:
                t["timer"].cancel()
            _active_timers.clear()
            print(f"⏰ [Tool Call -> Timer]: Đã hủy {count} hẹn giờ")
            return f"Đã hủy toàn bộ {count} bộ hẹn giờ cho sếp."

        elif action == "xem_trang_thai":
            if not _active_timers:
                return "Hiện tại không có bộ hẹn giờ hay Pomodoro nào đang đếm ngược."
            parts = []
            for t in _active_timers:
                rem_sec = max(0, int(t["end_time"] - now))
                m, s = divmod(rem_sec, 60)
                parts.append(f"'{t['label']}' còn {m} phút {s} giây")
            return f"Đang có {len(_active_timers)} hẹn giờ: " + "; ".join(parts) + "."

        # Default: dat_hen_gio
        if minutes <= 0:
            return "Số phút hẹn giờ phải lớn hơn 0."

        duration_sec = minutes * 60.0
        _timer_counter += 1
        timer_id = _timer_counter

        def _on_timer_done(tid=timer_id, msg=reminder):
            with _timer_lock:
                _active_timers[:] = [t for t in _active_timers if t["id"] != tid]
            _speak_alert_sync(msg)

        t_obj = threading.Timer(duration_sec, _on_timer_done)
        t_obj.daemon = True
        t_obj.start()

        _active_timers.append(
            {
                "id": timer_id,
                "label": reminder,
                "end_time": now + duration_sec,
                "timer": t_obj,
            }
        )

    if minutes >= 1:
        time_desc = f"{int(minutes) if minutes.is_integer() else minutes} phút"
    else:
        time_desc = f"{int(duration_sec)} giây"
    print(f"⏰ [Tool Call -> Timer]: Đặt hẹn giờ {time_desc} - '{reminder}'")
    return f"Đã đặt đồng hồ đếm ngược {time_desc} với lời nhắc: {reminder}"

