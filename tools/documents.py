"""
Group 2: Documents, Clipboard & Long-Term Personal Memory.
- Read aloud & summarize PDF/DOCX/PPTX/TXT/MD files with sentence caching & bookmarking (TL-01, TL-08).
- Clipboard Assistant with secret filtering & untrusted data wrapping (TL-06).
- Long-Term Memory with exact matching & multi-match disambiguation (TL-10).
"""

import hashlib
import json
import logging
import re
import time
from pathlib import Path

import pyperclip

import config
from tools.common import _strip_accents, load_json, update_json
from tools.policy import ToolResult, wrap_untrusted

log = logging.getLogger("teo.documents")

MAX_MEMORIES = 200
MAX_MEMORY_VAL_LEN = 300


# --- Document Reading & Summarizing (TL-01, TL-08) ---

def _is_allowed(p: Path) -> bool:
    """Verify document path is strictly within allowed directories with permitted extensions (TL-01)."""
    try:
        rp = p.resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    if not rp.is_file() or rp.name.startswith("."):
        return False
    if rp.suffix.lower() not in config.ALLOWED_EXTS or rp.stat().st_size > config.MAX_DOC_BYTES:
        return False
    return any(rp.is_relative_to(d.resolve()) for d in config.ALLOWED_DOC_DIRS if d.exists())


def _resolve_doc_path(raw_path: str) -> Path | None:
    """Resolve file path strictly through allowlist without arbitrary traversal (TL-01)."""
    raw = (raw_path or "").strip()
    if not raw or any(c in raw for c in '*?<>|"'):
        return None
    p = Path(raw).expanduser()
    if p.is_absolute() and _is_allowed(p):
        return p.resolve()

    name_norm = _strip_accents(Path(raw).name)
    for root in config.ALLOWED_DOC_DIRS:
        if not root.exists():
            continue
        try:
            for f in root.iterdir():
                if f.is_file() and name_norm in _strip_accents(f.name) and _is_allowed(f):
                    return f.resolve()
        except OSError:
            pass
    return None


def _extract_document_text(file_path: Path) -> str:
    """Extract plain text from allowed documents. Excludes executable/config files (.py, .json) (TL-01)."""
    ext = file_path.suffix.lower()
    if ext in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    from markitdown import MarkItDown

    md = MarkItDown()
    result = md.convert(str(file_path))
    return (result.text_content or "").strip()


def _split_into_sentences(text: str) -> list[str]:
    """Split extracted text into clean, readable sentences."""
    cleaned = re.sub(r"[#*`_~>|]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []
    raw_sents = re.split(r"(?<=[.!?])\s+", cleaned)
    return [s.strip() for s in raw_sents if len(s.strip()) >= 3]


def _wrap_long(s: str, limit: int = 180) -> list[str]:
    """Wrap long sentences exceeding limit into natural sub-phrases (TL-08)."""
    if len(s) <= limit:
        return [s]
    parts, cur = [], ""
    for piece in re.split(r"(?<=[,;:])\s+", s):
        if cur and len(cur) + len(piece) + 1 > limit:
            parts.append(cur)
            cur = piece
        else:
            cur = f"{cur} {piece}".strip()
    if cur:
        parts.append(cur)
    return [p[i : i + limit] for p in parts for i in range(0, len(p), limit)]


def _load_sentences(path: Path) -> list[str]:
    """Load cached sentences by file hash or parse & cache if not cached (TL-08)."""
    st = path.stat()
    key = hashlib.sha1(f"{path}|{st.st_mtime_ns}|{st.st_size}".encode()).hexdigest()[:16]
    cache = config.CACHE_DIR / f"doc_{key}.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass

    full_text = _extract_document_text(path)
    raw_sents = _split_into_sentences(full_text)
    sents = [p for s in raw_sents for p in _wrap_long(s)]
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(sents, ensure_ascii=False), encoding="utf-8")
    return sents


def tool_doc_va_tom_tat_tai_lieu(args: dict) -> ToolResult | str:
    """Summarize or read documents with automatic bookmarking and direct TTS output (TL-08)."""
    action = args.get("thao_tac", "tom_tat")
    raw_path = (args.get("duong_dan") or "").strip()
    num_sents = max(1, min(15, int(args.get("so_cau_doc", 5))))

    bookmarks = load_json(config.BOOKMARK_FILE, {"active_file": "", "files": {}})
    files_bm = bookmarks.setdefault("files", {})

    file_path: Path | None = None
    if raw_path:
        file_path = _resolve_doc_path(raw_path)
        if not file_path:
            return f"Em không tìm thấy file '{raw_path}' trong các thư mục cho phép (Documents, Downloads, Desktop, tai_lieu)."
    elif bookmarks.get("active_file"):
        cached = Path(bookmarks["active_file"])
        if cached.is_file() and _is_allowed(cached):
            file_path = cached

    if action == "dung":
        active = bookmarks.get("active_file", "")
        if active and active in files_bm:
            idx = files_bm[active].get("index", 0)
            total = files_bm[active].get("total", 0)
            return ToolResult(
                text=f"Đã dừng đọc file {Path(active).name} và lưu vị trí ở câu số {idx} trên tổng số {total} câu.",
                tainted=False,
            )
        return ToolResult(text="Đã dừng đọc tài liệu.", tainted=False)

    if action == "trang_thai":
        active = bookmarks.get("active_file", "")
        if not active or active not in files_bm:
            return "Hiện tại chưa có tài liệu nào đang được đánh dấu trang."
        info = files_bm[active]
        idx = info.get("index", 0)
        total = info.get("total", 0)
        return f"Sếp đang đọc dở file {Path(active).name} tại câu số {idx} trên {total} câu."

    if not file_path:
        return "Sếp vui lòng cho em biết tên file cần đọc hoặc tóm tắt nhé."

    key = str(file_path)
    bookmarks["active_file"] = key

    try:
        sentences = _load_sentences(file_path)
    except Exception as e:
        log.exception("Failed to extract text from %s", file_path)
        return f"Không thể trích xuất nội dung file {file_path.name}: {e}"

    if not sentences:
        return f"File {file_path.name} trống hoặc không có nội dung văn bản hợp lệ."

    if key not in files_bm or files_bm[key].get("total") != len(sentences):
        files_bm[key] = {
            "index": 0,
            "total": len(sentences),
            "updated_at": time.strftime("%H:%M %d/%m/%Y"),
        }

    bm_entry = files_bm[key]

    if action == "tom_tat":
        update_json(config.BOOKMARK_FILE, {"active_file": "", "files": {}}, lambda b: b.update(bookmarks))
        all_text = " ".join(sentences)
        truncated_note = ""
        if len(all_text) > 3500:
            truncated_note = " [Đã cắt: chỉ trích xuất 3500 ký tự đầu]"
        excerpt = all_text[:3500]
        wrapped = wrap_untrusted(file_path.name, excerpt)
        return ToolResult(
            text=(
                f"Nội dung trích xuất từ file {file_path.name}{truncated_note} "
                f"(hãy tóm tắt trong 3 câu ngắn gọn cho sếp):\n{wrapped}"
            ),
            tainted=True,
        )

    if action == "doc_tu_dau":
        bm_entry["index"] = 0
    elif action == "doc_lai":
        bm_entry["index"] = max(0, bm_entry["index"] - num_sents)

    start_idx = bm_entry["index"]
    if start_idx >= len(sentences):
        bm_entry["index"] = 0
        update_json(config.BOOKMARK_FILE, {"active_file": "", "files": {}}, lambda b: b.update(bookmarks))
        return ToolResult(
            text=f"Đã đọc hết toàn bộ {len(sentences)} câu của file {file_path.name}. Đã đặt lại bookmark về đầu file.",
            tainted=True,
        )

    end_idx = min(len(sentences), start_idx + num_sents)
    chunk_text = " ".join(sentences[start_idx:end_idx])

    def commit_bookmark():
        def mutate(b):
            files = b.setdefault("files", {})
            f_entry = files.setdefault(key, {})
            f_entry["index"] = end_idx
            f_entry["total"] = len(sentences)
            f_entry["updated_at"] = time.strftime("%H:%M %d/%m/%Y")
            b["active_file"] = key

        update_json(config.BOOKMARK_FILE, {"active_file": "", "files": {}}, mutate)

    # Pre-advance for state consistency while saving on commit
    bm_entry["index"] = end_idx
    bm_entry["updated_at"] = time.strftime("%H:%M %d/%m/%Y")
    update_json(config.BOOKMARK_FILE, {"active_file": "", "files": {}}, lambda b: b.update(bookmarks))

    return ToolResult(
        text=(
            f"Đọc nguyên văn từ câu {start_idx + 1} đến câu {end_idx} trên tổng {len(sentences)} câu của file {file_path.name}: "
            f"{chunk_text}"
        ),
        speak=chunk_text,
        commit=commit_bookmark,
        tainted=True,
    )


# --- Clipboard Assistant (TL-06) ---

def tool_xu_ly_bo_nho_tam_clipboard(args: dict) -> ToolResult | str:
    """Read or write text to system clipboard with privacy checks (TL-06)."""
    action = args.get("thao_tac", "doc")
    text_to_write = args.get("noi_dung_ghi") or ""

    if action == "ghi":
        if not text_to_write:
            return "Không có nội dung để chép vào bộ nhớ tạm."
        try:
            pyperclip.copy(text_to_write)
            return "Đã sao chép nội dung vào bộ nhớ tạm clipboard cho sếp."
        except Exception as e:
            return f"Không thể ghi vào clipboard: {e}"

    # Default: read clipboard
    try:
        clip_text = (pyperclip.paste() or "").strip()
    except Exception as e:
        return f"Không thể đọc bộ nhớ tạm clipboard: {e}"

    if not clip_text:
        return "Bộ nhớ tạm clipboard của sếp hiện đang trống, sếp hãy bôi đen văn bản và bấm Ctrl C trước nhé."

    # Privacy filtering for sensitive API keys/passwords (TL-06)
    if any(re.search(p, clip_text, re.MULTILINE) for p in config.SECRET_PATTERNS):
        return "Clipboard có vẻ chứa khóa hoặc mật khẩu nên em không đọc."

    wrapped = wrap_untrusted("clipboard", clip_text[:3000])
    return ToolResult(
        text=f"Nội dung sếp vừa copy trong clipboard là: {clip_text[:3000]}",
        tainted=True,
    )


# --- Long-Term Personal Memory (TL-10) ---

def tool_ghi_nho_thong_tin_dai_han(args: dict) -> str:
    """Save, search, view, or delete long-term facts in teo_memory.json (TL-10)."""
    action = args.get("thao_tac", "luu")
    key = (args.get("khoa") or "").strip()
    content = (args.get("noi_dung") or "").strip()

    if action == "luu":
        if not key and not content:
            return "Sếp chưa cung cấp thông tin cần ghi nhớ."
        topic = (key or content[:40]).strip()
        val = (content or key).strip()[:MAX_MEMORY_VAL_LEN]

        def mutate_save(memories: list[dict]):
            if len(memories) >= MAX_MEMORIES:
                return "FULL"
            norm_topic = _strip_accents(topic)
            for m in memories:
                if _strip_accents(m.get("key", "")) == norm_topic:
                    m["value"] = val
                    m["updated_at"] = time.strftime("%H:%M %d/%m/%Y")
                    return "UPDATED"
            memories.append({
                "key": topic,
                "value": val,
                "updated_at": time.strftime("%H:%M %d/%m/%Y"),
            })
            return "SAVED"

        res = update_json(config.MEMORY_FILE, [], mutate_save)
        if res == "FULL":
            return f"Bộ nhớ dài hạn đã đạt giới hạn tối đa {MAX_MEMORIES} mục. Sếp hãy xóa bớt thông tin cũ nhé."
        return f"Em đã ghi nhớ vào bộ nhớ dài hạn: {topic} là {val}."

    elif action == "tim_kiem":
        if not key and not content:
            return "Sếp muốn tìm thông tin gì trong bộ nhớ dài hạn?"
        memories = load_json(config.MEMORY_FILE, [])
        q_norm = _strip_accents(key or content)
        matches = [
            f"{m['key']}: {m['value']}"
            for m in memories
            if q_norm in _strip_accents(m.get("key", ""))
            or q_norm in _strip_accents(m.get("value", ""))
        ]
        if not matches:
            return f"Trong bộ nhớ dài hạn của em chưa có thông tin nào khớp với '{key or content}'."
        return "Thông tin em nhớ được là: " + "; ".join(matches) + "."

    elif action == "xoa":
        if not key:
            return "Sếp cần nói rõ từ khóa mục ghi nhớ muốn xóa."
        q = _strip_accents(key)

        def mutate_del(memories: list[dict]):
            exact = [i for i, m in enumerate(memories) if _strip_accents(m.get("key", "")) == q]
            cands = exact or [i for i, m in enumerate(memories) if q and q in _strip_accents(m.get("key", ""))]
            if not cands:
                return ("NOT_FOUND", None)
            if len(cands) > 1:
                names = "; ".join(memories[i]["key"] for i in cands[:5])
                return ("MULTI", names, len(cands))
            removed = memories.pop(cands[0])
            return ("OK", removed["key"])

        res = update_json(config.MEMORY_FILE, [], mutate_del)
        status = res[0]
        if status == "NOT_FOUND":
            return f"Không có mục nào tên '{key}'."
        elif status == "MULTI":
            return f"Có {res[2]} mục khớp: {res[1]}. Sếp nói rõ mục nào để em xóa."
        return f"Đã xóa thông tin '{res[1]}' khỏi bộ nhớ dài hạn."

    # View all
    memories = load_json(config.MEMORY_FILE, [])
    if not memories:
        return "Bộ nhớ dài hạn của em hiện đang trống."
    all_str = "; ".join(f"{m['key']}: {m['value']}" for m in memories)
    return f"Em đang ghi nhớ {len(memories)} thông tin của sếp: {all_str}."
