import json
import socket
import time
import psutil
from config import TODO_FILE, UDP_SIM_TARGET


def send_motion_to_3d_sim(motion: str, duration: float = 3.0, bpm: int = 120):
    """Bắn gói tin UDP sang cửa sổ 3D MuJoCo (nếu đang bật)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = json.dumps({"motion": motion, "duration": duration, "bpm": bpm}).encode("utf-8")
        sock.sendto(payload, UDP_SIM_TARGET)
        sock.close()
    except Exception:
        pass


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "dieu_khien_co_the_teo",
            "description": "Điều khiển cơ thể 3D của robot Tèo thực hiện cử chỉ, nhảy theo nhạc hoặc di chuyển bánh xích.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hanh_dong": {
                        "type": "string",
                        "enum": [
                            "wave_greeting",
                            "happy_dance",
                            "shake_no",
                            "move_forward",
                            "move_backward",
                            "spin_around",
                        ],
                        "description": (
                            "Gói chuyển động: wave_greeting (vẫy tay chào), happy_dance (nhảy múa), "
                            "shake_no (lắc đầu), move_forward (tiến lên), move_backward (lùi lại), spin_around (xoay vòng)."
                        ),
                    },
                    "so_giay": {"type": "number", "description": "Thời gian thực hiện (giây), mặc định 3.5"},
                    "bpm": {"type": "integer", "description": "Nhịp nhạc BPM khi nhảy, mặc định 125"},
                },
                "required": ["hanh_dong"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "quan_ly_viec_can_lam",
            "description": "Thêm công việc mới vào danh sách nhắc việc (Todo) hoặc xem danh sách việc cần làm của sếp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thao_tac": {
                        "type": "string",
                        "enum": ["xem", "them", "xoa_het"],
                        "description": "'xem' để đọc danh sách, 'them' để ghi chú việc mới, 'xoa_het' để làm trống.",
                    },
                    "noi_dung": {"type": "string", "description": "Nội dung công việc cần thêm (nếu thao_tac là 'them')."},
                },
                "required": ["thao_tac"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kiem_tra_suc_khoe_laptop",
            "description": "Kiểm tra phần trăm pin, mức sử dụng CPU và RAM hiện tại của laptop HP Victus 15.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def execute_tool_call(func_name: str, args_json: str) -> str:
    """Thực thi hàm công cụ khi DeepSeek gọi."""
    try:
        args = json.loads(args_json) if args_json else {}
    except Exception:
        args = {}

    if func_name == "dieu_khien_co_the_teo":
        motion = args.get("hanh_dong", "wave_greeting")
        dur = float(args.get("so_giay", 3.5))
        bpm = int(args.get("bpm", 125))
        send_motion_to_3d_sim(motion, dur, bpm)
        print(f"🤖 [Tool Call -> 3D Sim]: Kích hoạt '{motion}' trong {dur}s (BPM={bpm})")
        return f"Đã thực hiện cử chỉ {motion} thành công."

    elif func_name == "quan_ly_viec_can_lam":
        action = args.get("thao_tac", "xem")
        todos = json.loads(TODO_FILE.read_text(encoding="utf-8")) if TODO_FILE.exists() else []
        if action == "them":
            item = args.get("noi_dung", "").strip()
            if item:
                todos.append({"task": item, "time": time.strftime("%H:%M %d/%m")})
                TODO_FILE.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"📝 [Tool Call -> Todo]: Đã thêm '{item}'")
                return f"Đã lưu công việc '{item}' vào sổ tay của sếp."
        elif action == "xoa_het":
            TODO_FILE.write_text("[]", encoding="utf-8")
            return "Đã xóa sạch danh sách công việc."
        if not todos:
            return "Hiện tại danh sách công việc của sếp đang trống."
        summary = "; ".join([f"Việc số {i+1}: {t['task']}" for i, t in enumerate(todos)])
        print(f"📋 [Tool Call -> Todo]: {summary}")
        return f"Danh sách hiện có {len(todos)} việc: {summary}"

    elif func_name == "kiem_tra_suc_khoe_laptop":
        cpu = psutil.cpu_percent(interval=0.2)
        ram = psutil.virtual_memory().percent
        bat = psutil.sensors_battery()
        bat_info = f"{bat.percent}% ({'đang cắm sạc' if bat.power_plugged else 'đang dùng pin'})" if bat else "không rõ"
        res = f"Laptop Victus của sếp đang dùng {cpu}% CPU, {ram}% RAM, pin ở mức {bat_info}."
        print(f"💻 [Tool Call -> Laptop]: {res}")
        return res

    return "Công cụ không tồn tại."
