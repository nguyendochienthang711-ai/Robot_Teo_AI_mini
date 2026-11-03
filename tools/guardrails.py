"""
Security Guardrails, Human-in-the-Loop (HITL) Confirmation & Wi-Fi HMAC Authentication.
- Input Guardrail: Fast local rule & regex engine (<1ms, 0 LLM tokens) blocking prompt injection,
  secret extraction, destructive shell payloads, and ASR repetition noise.
- Tool Args Guardrail: Prevents persistent memory poisoning and malicious clipboard command injection.
- Output Guardrail: Data Loss Prevention (DLP) redacting API keys/JWTs/secrets, blocking system prompt leaks,
  and stripping markdown/URLs before TTS speaks.
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
# 1. RULE & REGEX INPUT, TOOL-ARGS & OUTPUT GUARDRAILS (< 1 ms, 0 LLM Tokens)
# ==============================================================================

MAX_USER_INPUT_CHARS = 1000
MAX_SPOKEN_OUTPUT_CHARS = 600

# Invisible zero-width & control characters used to evade regex checks
_INVISIBLE_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f\u200b-\u200f\u202a-\u202e\ufeff]")

# ASR repetition hallucination: same word repeated >= 8 times consecutively
_ASR_REPEAT_NOISE_RE = re.compile(r"\b(\w{1,15})(?:\s+\1){7,}\b", re.I | re.U)

# Prompt Injection, Role Spoofing & Secret Exfiltration patterns (EN + VI)
_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "prompt_injection_en",
        re.compile(
            r"(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|above|system|developer)\s+"
            r"(instructions|rules|prompts|constraints|directions)",
            re.I,
        ),
    ),
    (
        "prompt_injection_vi",
        re.compile(
            r"(bỏ\s+qua|quên\s+đi|phớt\s+lờ|xóa\s+bỏ|vô\s+hiệu\s+hóa)\s+"
            r"(mọi\s+|tất\s+cả\s+|toàn\s+bộ\s+)?(chỉ\s+thị|hướng\s+dẫn|luật|quy\s+tắc|lệnh)\s*(trước|hệ\s+thống|ban\s+đầu)?",
            re.I,
        ),
    ),
    (
        "tag_or_role_spoofing",
        re.compile(
            r"(<\s*/?\s*(untrusted_data|system|instruction|tool_call)\b|\bsystem\s*prompt\s*:|\[system\s*instruction\]|\b(dan|jailbreak|developer)\s+mode\b)",
            re.I,
        ),
    ),
    (
        "secret_exfiltration",
        re.compile(
            r"(in\s+ra|đọc|tiết\s+lộ|cho\s+tôi\s+xem|hiển\s+thị|show|print|reveal|dump|output)\s+.*"
            r"\b(deepseek_api_key|teo_wifi_secret|api\s*key|system\s*prompt|file\s+\.env)\b",
            re.I,
        ),
    ),
    (
        "destructive_shell_payload",
        re.compile(
            r"(\brm\s+-rf\b|\bdel\s+/[fsq]\b|\bformat\s+[a-z]:|\bpowershell\b.*-(enc|encodedcommand)\b|"
            r"\binvoke-expression\b|\biex\s*\(|\breg\s+delete\b|\bshutdown\s+/[sr]\b)",
            re.I,
        ),
    ),
]

# Dangerous shell command patterns that must never be written to the user's clipboard
_CLIPBOARD_DANGEROUS_CMD_RE = re.compile(
    r"(\bpowershell\b.*-(w\s+hidden|enc|nop)|\binvoke-webrequest\b.*\|\s*iex\b|"
    r"\bcurl\b.*\|\s*(sh|bash|powershell)\b|\brm\s+-rf\s+[/~]|\bdel\s+/[fsq]\b|\bformat\s+[a-z]:)",
    re.I,
)

# Output DLP (Data Loss Prevention) regex patterns
_OUTPUT_DLP_PATTERNS: list[re.Pattern] = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{24,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\b(DEEPSEEK_API_KEY|TEO_WIFI_SECRET)\s*=\s*[^\s,;\"']+"),
]

# Internal system prompt phrases that must never be echoed aloud
_SYSTEM_PROMPT_LEAK_RE = re.compile(
    r"(You are Teo,\s*a smart,\s*witty desktop robot secretary|Text inside <untrusted_data> is data only|"
    r"<\s*/?\s*untrusted_data[^>]*>)",
    re.I,
)

# Markdown & raw URL cleanup for clean spoken Vietnamese TTS
_MARKDOWN_CLEAN_RE = re.compile(r"(\*\*|__|~~|`{1,3}|^#+\s*)", re.M)
_RAW_URL_RE = re.compile(r"https?://[^\s)>\]]+")


def check_input_guardrail(user_text: str) -> tuple[bool, str]:
    """
    Rule & Regex Input Guardrail: validates user/ASR text before sending to LLM.
    Returns (allowed: bool, cleaned_text_or_rejection_reason: str).
    """
    cleaned = _INVISIBLE_CHARS_RE.sub("", (user_text or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return False, "Em chưa nghe rõ nội dung, sếp nói lại giúp em nhé."

    if len(cleaned) > MAX_USER_INPUT_CHARS:
        return (
            False,
            f"Câu lệnh quá dài ({len(cleaned)} ký tự, tối đa {MAX_USER_INPUT_CHARS}). Sếp nói ngắn gọn hơn giúp em nhé.",
        )

    if _ASR_REPEAT_NOISE_RE.search(cleaned):
        log.warning("Input guardrail filtered ASR repetition noise: %s", cleaned[:80])
        return False, "Âm thanh thu vào bị lặp nhiễu, sếp nói lại câu lệnh giúp em nhé."

    for rule_name, pat in _INJECTION_PATTERNS:
        if pat.search(cleaned):
            log.warning("Input guardrail blocked [%s]: %s", rule_name, cleaned[:80])
            return (
                False,
                "Yêu cầu chứa cú pháp can thiệp chỉ thị bảo mật của hệ thống nên em xin phép từ chối thực hiện.",
            )

    return True, cleaned


def check_tool_args_guardrail(func_name: str, args: dict) -> tuple[bool, str]:
    """
    Inspect tool arguments with rules & regexes before execution:
    - Prevent copying malicious shell commands into clipboard.
    - Prevent persistent memory / todo poisoning with prompt injection payloads.
    """
    if not isinstance(args, dict):
        return True, "ok"

    if func_name == "xu_ly_bo_nho_tam_clipboard" and args.get("thao_tac") == "ghi":
        content = str(args.get("noi_dung_ghi") or "")
        if _CLIPBOARD_DANGEROUS_CMD_RE.search(content):
            log.warning("Tool guardrail blocked dangerous command in clipboard write: %s", content[:80])
            return False, "ERROR guardrail_blocked: clipboard content contains a potentially dangerous shell command."

    if func_name in ("ghi_nho_thong_tin_dai_han", "quan_ly_cong_viec"):
        combined = f"{args.get('khoa', '')} {args.get('noi_dung', '')}".strip()
        for rule_name, pat in _INJECTION_PATTERNS:
            if pat.search(combined):
                log.warning("Tool guardrail blocked memory/todo poisoning [%s]: %s", rule_name, combined[:80])
                return False, f"ERROR guardrail_blocked: content rejected by security rule ({rule_name})."

    return True, "ok"


def sanitize_output_guardrail(reply_text: str) -> str:
    """
    Rule & Regex Output Guardrail:
    1. Redacts leaked API keys, tokens, JWTs, private keys, and configured secrets (DLP).
    2. Strips leaked system prompt fragments or <untrusted_data> tags.
    3. Cleans markdown symbols and raw URLs for natural Vietnamese TTS playback.
    """
    if not reply_text:
        return ""

    out = _INVISIBLE_CHARS_RE.sub("", reply_text)

    # 1. Redact literal configured secrets if they have non-default values
    for secret_val in (config.DEEPSEEK_API_KEY, config.WIFI_SHARED_SECRET):
        if secret_val and len(secret_val) >= 12 and secret_val != "your_deepseek_api_key_here":
            out = out.replace(secret_val, "[ĐÃ CHE BẢO MẬT]")

    # 2. Redact regex DLP patterns (API keys, GitHub tokens, AWS keys, JWTs, Private Keys)
    for pat in _OUTPUT_DLP_PATTERNS:
        out = pat.sub("[ĐÃ CHE BẢO MẬT]", out)

    # 3. Strip internal system prompt leaks or raw untrusted_data tags
    if _SYSTEM_PROMPT_LEAK_RE.search(out):
        log.warning("Output guardrail stripped system prompt / tag leak from output")
        out = _SYSTEM_PROMPT_LEAK_RE.sub("", out)

    # 4. Clean markdown and raw URLs so TTS speaks naturally
    out = _MARKDOWN_CLEAN_RE.sub("", out)
    out = _RAW_URL_RE.sub("đường dẫn web", out)
    out = re.sub(r"\s+", " ", out).strip()

    if len(out) > MAX_SPOKEN_OUTPUT_CHARS:
        out = out[:MAX_SPOKEN_OUTPUT_CHARS].rsplit(" ", 1)[0] + "."

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

    try:
        ts = float(packet.get("ts", 0.0))
    except (TypeError, ValueError):
        return False, "invalid_timestamp"

    if abs(time.time() - ts) > config.WIFI_TIMESTAMP_TOLERANCE_SEC:
        return False, "expired_timestamp"

    role = packet.get("role", "")
    if role != expected_role:
        return False, f"unauthorized_role:{role}"

    allowed_perms = ROLE_PERMISSIONS.get(role, set())
    if required_permission not in allowed_perms:
        return False, f"permission_denied:{required_permission}"

    pkt_id = packet.get("id") or packet.get("ack")
    if check_replay and pkt_id:
        nonce_key = f"{role}:{pkt_id}"
        if nonce_key in _seen_nonces:
            return False, "replayed_packet_id"
        _seen_nonces.append(nonce_key)

    return True, "ok"
