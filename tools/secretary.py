"""
Group 1: Personal Secretary, Time & Task Management.
- Todo tasks management with safe disambiguation and atomic persistence (TL-05, TL-10).
- Persistent timers & Pomodoro alarms with restore on reboot and arm waving (TL-09).
"""

import io
import logging
import threading
import time
from typing import Any

import config
from tools.common import _strip_accents, load_json, save_json, update_json
from tools.system import send_motion_to_3d_sim

log = logging.getLogger("teo.secretary")

# --- Todo Tasks Management (TL-05, TL-10) ---

def tool_quan_ly_cong_viec(args: dict) -> str:
    """Manage the user's Todo task list with exact matching and disambiguation (TL-10)."""
    action = args.get("thao_tac", "xem")
    content = (args.get("noi_dung") or "").strip()
    index = args.get("vi_tri")

    if action == "them":
        if not content:
            return "Sếp chưa nói nội dung công việc cần thêm."

        def mutate_add(todos: list[dict]):
            todos.append({
                "task": content,
                "done": False,
                "time": time.strftime("%H:%M %d/%m"),
            })

        update_json(config.TODO_FILE, [], mutate_add)
        return f"Đã lưu công việc '{content}' vào danh sách của sếp."

    elif action == "hoan_thanh":
        def mutate_done(todos: list[dict]):
            if isinstance(index, int) and 1 <= index <= len(todos):
                todos[index - 1]["done"] = True
                return ("OK", todos[index - 1]["task"])
            if content:
                q = _strip_accents(content)
                exact = [i for i, t in enumerate(todos) if _strip_accents(t.get("task", "")) == q]
                cands = exact or [i for i, t in enumerate(todos) if q in _strip_accents(t.get("task", ""))]
                if not cands:
                    return ("NOT_FOUND", None)
                if len(cands) > 1:
                    names = "; ".join(f"Số {i+1}: {todos[i]['task']}" for i in cands[:5])
                    return ("MULTI", names, len(cands))
                todos[cands[0]]["done"] = True
                return ("OK", todos[cands[0]]["task"])
            return ("MISSING", None)

        res = update_json(config.TODO_FILE, [], mutate_done)
        if res[0] == "OK":
            return f"Đã đánh dấu hoàn thành công việc '{res[1]}'."
        elif res[0] == "MULTI":
            return f"Có {res[2]} việc khớp: {res[1]}. Sếp hãy nói rõ số thứ tự việc cần hoàn thành nhé."
        return "Không tìm thấy công việc tương ứng để đánh dấu hoàn thành."

    elif action == "xoa":
        def mutate_del(todos: list[dict]):
            if isinstance(index, int) and 1 <= index <= len(todos):
                removed = todos.pop(index - 1)
                return ("OK", removed["task"])
            if content:
                q = _strip_accents(content)
                exact = [i for i, t in enumerate(todos) if _strip_accents(t.get("task", "")) == q]
                cands = exact or [i for i, t in enumerate(todos) if q in _strip_accents(t.get("task", ""))]
                if not cands:
                    return ("NOT_FOUND", None)
                if len(cands) > 1:
                    names = "; ".join(f"Số {i+1}: {todos[i]['task']}" for i in cands[:5])
                    return ("MULTI", names, len(cands))
                removed = todos.pop(cands[0])
                return ("OK", removed["task"])
            return ("MISSING", None)

        res = update_json(config.TODO_FILE, [], mutate_del)
        if res[0] == "OK":
            return f"Đã xóa công việc '{res[1]}' khỏi danh sách."
        elif res[0] == "MULTI":
            return f"Có {res[2]} việc khớp: {res[1]}. Sếp hãy nói rõ số thứ tự việc cần xóa nhé."
        return "Không tìm thấy công việc cần xóa trong danh sách."

    elif action == "xoa_het":
        save_json(config.TODO_FILE, [])
        return "Đã xóa sạch danh sách công việc."

    # Default: view list
    todos = load_json(config.TODO_FILE, [])
    if not todos:
        return "Hiện tại danh sách công việc của sếp đang trống."
    items_str = []
    for i, t in enumerate(todos):
        status = "đã xong" if t.get("done") else "chưa làm"
        items_str.append(f"Việc số {i + 1}: {t.get('task')} ({status})")
    summary = "; ".join(items_str)
    return f"Danh sách hiện có {len(todos)} việc: {summary}."


# --- Persistent Pomodoro & Countdown Timers (TL-09) ---

_active_timers: list[dict] = []
_timer_lock = threading.RLock()
_timer_counter = 0


def _save_persistent_timers():
    """Save active timer records to teo_timers.json (TL-09)."""
    with _timer_lock:
        recs = [
            {"id": t["id"], "label": t["label"], "due_ts": t["end_time"]}
            for t in _active_timers
        ]
    save_json(config.TIMERS_FILE, recs)


def _speak_alert_sync(message: str):
    """Play alert chime and speak reminder when timer ends. Safe body gesture only (TL-09)."""
    # Safe upper body gesture (wave greeting) instead of dangerous base motion
    send_motion_to_3d_sim("wave_greeting", duration=3.0, bpm=120)
    log.info("Timer alert fired: %s", message)

    try:
        import pygame
        from audio_io import fetch_piper_tts_sync

        audio_bytes, _ = fetch_piper_tts_sync(message, getattr(config, "TTS_MODE", "chipmunk"))
        if audio_bytes and pygame.mixer.get_init():
            # Wait up to 3 seconds if audio bus is currently busy
            for _ in range(30):
                if not pygame.mixer.music.get_busy():
                    break
                time.sleep(0.1)
            pygame.mixer.music.load(io.BytesIO(audio_bytes))
            pygame.mixer.music.play()
    except Exception as e:
        log.warning("Audio alert playback fallback: %s", e)
        try:
            import winsound
            winsound.Beep(1000, 600)
        except Exception:
            pass


def _fire_timer(tid: int, label: str):
    """Handle timer expiration and remove from persistent state."""
    with _timer_lock:
        _active_timers[:] = [t for t in _active_timers if t["id"] != tid]
    _save_persistent_timers()
    _speak_alert_sync(label)


def _arm_timer(tid: int, label: str, due_ts: float):
    """Arm a countdown timer with background thread execution."""
    delay = max(0.0, due_ts - time.time())
    t_obj = threading.Timer(delay, _fire_timer, args=(tid, label))
    t_obj.daemon = True
    t_obj.start()
    _active_timers.append({
        "id": tid,
        "label": label,
        "end_time": due_ts,
        "timer": t_obj,
    })


def restore_timers():
    """Restore pending timers from teo_timers.json upon system startup (TL-09)."""
    global _timer_counter
    records = load_json(config.TIMERS_FILE, [])
    now = time.time()
    with _timer_lock:
        for rec in records:
            tid = rec.get("id", 0)
            label = rec.get("label", "Hẹn giờ")
            due_ts = rec.get("due_ts", 0)
            if due_ts > now - 600:  # Fire even if missed within 10 minutes
                _timer_counter = max(_timer_counter, tid)
                _arm_timer(tid, label, due_ts)
    _save_persistent_timers()


def tool_dong_ho_tap_trung_pomodoro(args: dict) -> str:
    """Set countdown timer / Pomodoro, check status, or cancel timers with persistent recovery (TL-09)."""
    global _timer_counter
    action = args.get("thao_tac", "dat_hen_gio")
    raw_minutes = args.get("so_phut", 25)
    hen_gio_id = args.get("hen_gio_id")
    reminder = (
        args.get("loi_nhac")
        or "Hết giờ tập trung rồi sếp ơi, sếp nghỉ ngơi uống miếng nước và vươn vai nhé."
    ).strip()

    try:
        minutes = float(raw_minutes)
    except (TypeError, ValueError):
        minutes = 25.0

    now = time.time()
    with _timer_lock:
        # Clear finished timers
        _active_timers[:] = [t for t in _active_timers if t["end_time"] > now]

        if action == "huy":
            if not _active_timers:
                return "Hiện không có bộ hẹn giờ nào đang chạy."
            if hen_gio_id is not None:
                matches = [t for t in _active_timers if t["id"] == hen_gio_id]
                if not matches:
                    return f"Không tìm thấy bộ hẹn giờ số {hen_gio_id}."
                matches[0]["timer"].cancel()
                _active_timers.remove(matches[0])
                _save_persistent_timers()
                return f"Đã hủy bộ hẹn giờ số {hen_gio_id} cho sếp."
            else:
                count = len(_active_timers)
                for t in _active_timers:
                    t["timer"].cancel()
                _active_timers.clear()
                _save_persistent_timers()
                return f"Đã hủy toàn bộ {count} bộ hẹn giờ cho sếp."

        elif action == "xem_trang_thai":
            if not _active_timers:
                return "Hiện tại không có bộ hẹn giờ hay Pomodoro nào đang đếm ngược."
            parts = []
            for t in _active_timers:
                rem_sec = max(0, int(t["end_time"] - now))
                m, s = divmod(rem_sec, 60)
                parts.append(f"Mã {t['id']}: '{t['label']}' còn {m} phút {s} giây")
            return f"Đang có {len(_active_timers)} hẹn giờ: " + "; ".join(parts) + "."

        # Default: dat_hen_gio
        if minutes <= 0 or minutes > 720:
            return "Số phút hẹn giờ phải lớn hơn 0 và không quá 720 phút (12 tiếng)."

        duration_sec = minutes * 60.0
        _timer_counter += 1
        timer_id = _timer_counter
        due_ts = now + duration_sec

        _arm_timer(timer_id, reminder, due_ts)

    _save_persistent_timers()

    if minutes == 1.5:
        time_desc = "một phút rưỡi"
    elif minutes >= 1:
        time_desc = f"{int(minutes) if minutes.is_integer() else minutes} phút"
    else:
        time_desc = f"{int(duration_sec)} giây"

    return f"Đã đặt đồng hồ đếm ngược {time_desc} với lời nhắc: {reminder}"
