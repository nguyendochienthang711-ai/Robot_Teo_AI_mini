"""
Security Guardrails, Human-in-the-Loop (HITL) Confirmation & Wi-Fi HMAC Authentication.
- Input Guardrail: Fast local regex (<1ms, 0 LLM tokens) blocking prompt injection & ASR noise.
- Output Guardrail: Data Loss Prevention (DLP) redacting leaked API keys/secrets before TTS/display.
- HITL Manager: Holds sensitive laptop data operations pending until user says "OK" / "Đồng ý".
- Wi-Fi Auth & RBAC: HMAC-SHA256 packet signing, timestamp window (±5s), anti-replay nonce cache, and role verification.
"""

from collections import deque
from dataclasses import dataclass
import hashlib
import hmac
import json
import logging
import re
import time
from typing import Literal

import config
from tools.common import _strip_accents

log = logging.getLogger("teo.guardrails")

# ==============================================================================
# 1. INPUT & OUTPUT GUARDRAILS (< 1 ms, 0 LLM Tokens)
# ==============================================================================

MAX_USER_INPUT_CHARS = 1000

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|system)\s+(prompt|instructions)", re.I),
    re.compile(r"<\s*/?\s*untrusted_data\b", re.I),
    re.compile(r"\bsystem\s*prompt\s*:", re.I),
    re.compile(r"bỏ\s+qua\s+(mọi\s+|tất\s+cả\s+)?(chỉ\s+thị|hướng\s+dẫn|luật)\s+trước", re.I),
]


def check_input_guardrail(user_text: str) -> tuple[bool, str]:
    """
    Validate user/ASR input before sending to LLM.
    Returns (allowed: bool, cleaned_text_or_rejection_reason: str).
    """
    cleaned = re.sub(r"[\x00-\x08\x0b-\x1f]", "", (user_text or "")).strip()
    if not cleaned:
        return False, "Em chưa nghe rõ nội dung, sếp nói lại giúp em nhé."

    if len(cleaned) > MAX_USER_INPUT_CHARS:
        return (
            False,
            f"Câu lệnh quá dài ({len(cleaned)} ký tự, tối đa {MAX_USER_INPUT_CHARS}). Sếp nói ngắn gọn hơn giúp em nhé.",
        )

    for pat in _INJECTION_PATTERNS:
        if pat.search(cleaned):
            log.warning("Input guardrail blocked suspected prompt injection: %s", cleaned[:80])
            return (
                False,
                "Yêu cầu chứa cú pháp can thiệp chỉ thị hệ thống nên em xin phép từ chối thực hiện.",
            )

    return True, cleaned


def sanitize_output_guardrail(reply_text: str) -> str:
    """
    Scan LLM/TTS output for accidental secret leakage (DLP) and strip unsafe formatting.
    """
    if not reply_text:
        return ""

    out = reply_text

    # Redact literal configured secrets if they have non-default values
    for secret_val in (config.DEEPSEEK_API_KEY, config.WIFI_SHARED_SECRET):
        if secret_val and len(secret_val) >= 12 and secret_val != "your_deepseek_api_key_here":
            out = out.replace(secret_val, "[ĐÃ CHE BẢO MẬT]")

    # Redact regex secret patterns (sk-..., AKIA..., ghp_..., private keys)
    for pat in config.SECRET_PATTERNS:
        # Skip the full-line base64 anchor pattern on normal Vietnamese sentences with spaces
        if pat.startswith("^"):
            continue
        out = re.sub(pat, "[ĐÃ CHE BẢO MẬT]", out)

    return out


# ==============================================================================
# 2. HUMAN-IN-THE-LOOP (HITL) CONFIRMATION FOR LAPTOP DATA OPERATIONS
# ==============================================================================

@dataclass
class PendingAction:
    func_name: str
    args_json: str
    description_vi: str
    created_at: float


_pending_action: PendingAction | None = None

_CONFIRM_PHRASES = {
    "ok",
    "oke",
    "okay",
    "ok em",
    "oke em",
    "dong y",
    "uk",
    "ukm",
    "uh",
    "uhm",
    "u",
    "duoc",
    "duoc roi",
    "lam di",
    "lam luon",
    "chot",
    "tiep tuc",
    "xac nhan",
    "yes",
    "alo ok",
}

_REJECT_PHRASES = {
    "khong",
    "khong dong y",
    "dung",
    "dung lam",
    "huy",
    "huy bo",
    "thoi",
    "bo qua",
    "no",
    "cancel",
}


def describe_hitl_action(func_name: str, args: dict) -> str | None:
    """
    Return a human-friendly Vietnamese description if (func_name, args) accesses or modifies
    sensitive laptop data and therefore requires explicit user confirmation ("OK" / "Đồng ý").
    Returns None if no HITL confirmation is needed.
    """
    action = (args or {}).get("thao_tac", "")

    if func_name == "nhin_man_hinh_laptop":
        return "chụp ảnh cửa sổ màn hình laptop hiện tại để phân tích"

    if func_name == "xu_ly_bo_nho_tam_clipboard":
        if action == "ghi":
            return "ghi đè nội dung mới vào bộ nhớ tạm clipboard của laptop"
        return "đọc nội dung trong bộ nhớ tạm clipboard của laptop"

    if func_name == "doc_va_tom_tat_tai_lieu":
        if action in ("tom_tat", "doc_tu_dau"):
            path_str = (args or {}).get("duong_dan") or "tài liệu trên máy"
            return f"mở và đọc file tài liệu '{path_str}' trên laptop"
        return None

    if func_name == "quan_ly_cong_viec" and action in ("xoa", "xoa_het"):
        if action == "xoa_het":
            return "xóa toàn bộ danh sách công việc"
        target = (args or {}).get("noi_dung") or f"vị trí số {(args or {}).get('vi_tri')}"
        return f"xóa công việc '{target}' khỏi danh sách"

    if func_name == "ghi_nho_thong_tin_dai_han" and action == "xoa":
        key = (args or {}).get("khoa") or ""
        return f"xóa mục '{key}' khỏi bộ nhớ dài hạn"

    return None


def set_pending_action(func_name: str, args_json: str, description_vi: str) -> PendingAction:
    """Store a pending sensitive laptop action awaiting user voice/text confirmation."""
    global _pending_action
    _pending_action = PendingAction(
        func_name=func_name,
        args_json=args_json,
        description_vi=description_vi,
        created_at=time.time(),
    )
    return _pending_action


def get_pending_action() -> PendingAction | None:
    """Return active pending action if it has not expired."""
    global _pending_action
    if _pending_action is None:
        return None
    if time.time() - _pending_action.created_at > config.HITL_CONFIRM_TIMEOUT_SEC:
        _pending_action = None
        return None
    return _pending_action


def clear_pending_action() -> None:
    """Clear any stored pending HITL action."""
    global _pending_action
    _pending_action = None


def detect_hitl_intent(user_text: str) -> Literal["confirm", "reject", "none"]:
    """
    Check if a short user utterance is confirming ("OK", "đồng ý") or rejecting ("không", "hủy")
    a pending HITL action.
    """
    norm = _strip_accents(user_text)
    norm = re.sub(r"[^a-z0-9\s]", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    if not norm:
        return "none"

    words = norm.split()
    # Rejections take strict precedence if user says e.g. "không đồng ý" or "thôi đừng làm"
    if norm in _REJECT_PHRASES or (len(words) <= 5 and any(w in {"khong", "huy", "thoi", "dung", "cancel"} for w in words)):
        return "reject"

    if norm in _CONFIRM_PHRASES:
        return "confirm"

    if len(words) <= 5 and (
        "dong y" in norm
        or "ok" in words
        or "oke" in words
        or "okay" in words
        or "chot" in words
        or "xac nhan" in norm
        or "lam di" in norm
    ):
        return "confirm"

    return "none"


# ==============================================================================
# 3. WI-FI / UDP PACKET AUTHENTICATION (HMAC-SHA256 + ANTI-REPLAY + RBAC)
# ==============================================================================

RoleType = Literal["laptop_controller", "robot_node"]

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "laptop_controller": {"motion_cmd"},
    "robot_node": {"ack", "telemetry", "touch_confirm"},
}

_seen_nonces: deque[str] = deque(maxlen=256)


def _canonical_message(packet: dict) -> bytes:
    """Build deterministic byte payload excluding the 'sig' field for HMAC calculation."""
    body = {k: v for k, v in sorted(packet.items()) if k != "sig"}
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_packet_hmac(packet: dict, secret: str | None = None) -> str:
    """Compute hex HMAC-SHA256 signature for a Wi-Fi/UDP packet."""
    key = (secret if secret is not None else config.WIFI_SHARED_SECRET).encode("utf-8")
    msg = _canonical_message(packet)
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def sign_wifi_packet(payload: dict, role: RoleType = "laptop_controller", secret: str | None = None) -> dict:
    """Attach timestamp, role, and HMAC-SHA256 signature to a packet before sending over Wi-Fi/UDP."""
    pkt = dict(payload)
    pkt.setdefault("ts", round(time.time(), 3))
    pkt.setdefault("role", role)
    pkt["sig"] = compute_packet_hmac(pkt, secret=secret)
    return pkt


def verify_wifi_packet(
    packet: dict,
    expected_role: RoleType,
    required_permission: str,
    secret: str | None = None,
    check_replay: bool = True,
) -> tuple[bool, str]:
    """
    Verify authenticity, freshness, anti-replay nonce, and role permission of an incoming Wi-Fi/UDP packet.
    Returns (ok: bool, reason: str).
    """
    if not isinstance(packet, dict):
        return False, "invalid_packet_type"

    sig = packet.get("sig")
    if not sig or not isinstance(sig, str):
        return False, "missing_signature"

    expected_sig = compute_packet_hmac(packet, secret=secret)
    if not hmac.compare_digest(sig, expected_sig):
        return False, "invalid_hmac_signature"

    # Verify timestamp freshness against replay attacks
    try:
        ts = float(packet.get("ts", 0.0))
    except (TypeError, ValueError):
        return False, "invalid_timestamp"

    if abs(time.time() - ts) > config.WIFI_TIMESTAMP_TOLERANCE_SEC:
        return False, "expired_timestamp"

    # Verify role & permission (RBAC)
    role = packet.get("role", "")
    if role != expected_role:
        return False, f"unauthorized_role:{role}"

    allowed_perms = ROLE_PERMISSIONS.get(role, set())
    if required_permission not in allowed_perms:
        return False, f"permission_denied:{required_permission}"

    # Anti-replay nonce check
    pkt_id = packet.get("id") or packet.get("ack")
    if check_replay and pkt_id:
        nonce_key = f"{role}:{pkt_id}"
        if nonce_key in _seen_nonces:
            return False, "replayed_packet_id"
        _seen_nonces.append(nonce_key)

    return True, "ok"
