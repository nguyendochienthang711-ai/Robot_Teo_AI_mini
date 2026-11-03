"""
Group 2: Documents, Clipboard & Long-Term Personal Memory.
- Read aloud & summarize PDF/DOCX/PPTX/TXT/MD files with bookmarking.
- Clipboard Assistant (read/write system clipboard).
- Persistent Long-Term Memory (save, recall, search, delete facts in teo_memory.json).
"""

import re
import time
from pathlib import Path

import pyperclip

import config
from tools.common import _load_json_file, _save_json_file, _strip_accents


# --- Document Reading & Summarizing ---

def _resolve_doc_path(raw_path: str) -> Path | None:
    """Find absolute path of a document by name or partial path."""
    if not raw_path:
        return None
    p = Path(raw_path).expanduser()
    if p.is_file():
        return p.resolve()

    search_roots = [
        Path.cwd(),
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path.home() / "Desktop",
    ]
    for root in search_roots:
        if not root.exists():
            continue
        candidate = root / raw_path
        if candidate.is_file():
            return candidate.resolve()
        try:
            for f in root.glob(f"*{raw_path}*"):
                if f.is_file() and f.suffix.lower() in {".pdf", ".docx", ".pptx", ".txt", ".md"}:
                    return f.resolve()
        except Exception:
            pass
    return None


def _extract_document_text(file_path: Path) -> str:
    """Extract plain text from document using markitdown or direct read."""
    ext = file_path.suffix.lower()
    if ext in {".txt", ".md", ".csv", ".py", ".json"}:
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


def tool_doc_va_tom_tat_tai_lieu(args: dict) -> str:
    """Summarize or read documents with automatic bookmarking."""
    action = args.get("thao_tac", "tom_tat")
    raw_path = (args.get("duong_dan") or "").strip()
    num_sents = max(1, min(15, int(args.get("so_cau_doc", 5))))

    bookmarks: dict = _load_json_file(config.BOOKMARK_FILE, {"active_file": "", "files": {}})
    files_bm: dict = bookmarks.setdefault("files", {})

    file_path: Path | None = None
    if raw_path:
        file_path = _resolve_doc_path(raw_path)
        if not file_path:
            return f"Em không tìm thấy file '{raw_path}' trên máy của sếp."
    elif bookmarks.get("active_file"):
        cached = Path(bookmarks["active_file"])
        if cached.is_file():
            file_path = cached

    if action == "dung":
        active = bookmarks.get("active_file", "")
        if active and active in files_bm:
            idx = files_bm[active].get("index", 0)
            total = len(files_bm[active].get("sentences", []))
            return f"Đã dừng đọc file {Path(active).name} và lưu vị trí ở câu số {idx} trên tổng số {total} câu."
        return "Đã dừng đọc tài liệu."

    if action == "trang_thai":
        active = bookmarks.get("active_file", "")
        if not active or active not in files_bm:
            return "Hiện tại chưa có tài liệu nào đang được đánh dấu trang."
        info = files_bm[active]
        idx = info.get("index", 0)
        total = len(info.get("sentences", []))
        return f"Sếp đang đọc dở file {Path(active).name} tại câu số {idx} trên {total} câu."

    if not file_path:
        return "Sếp vui lòng cho em biết tên file cần đọc hoặc tóm tắt nhé."

    key = str(file_path)
    bookmarks["active_file"] = key

    try:
        full_text = _extract_document_text(file_path)
    except Exception as e:
        return f"Không thể trích xuất nội dung file {file_path.name}: {e}"

    if not full_text.strip():
        return f"File {file_path.name} không có nội dung văn bản đọc được."

    sentences = _split_into_sentences(full_text)
    if not sentences:
        return f"File {file_path.name} trống hoặc không có câu văn hợp lệ."

    if key not in files_bm or files_bm[key].get("total") != len(sentences):
        files_bm[key] = {
            "sentences": sentences,
            "index": 0,
            "total": len(sentences),
            "updated_at": time.strftime("%H:%M %d/%m/%Y"),
        }

    bm_entry = files_bm[key]

    if action == "tom_tat":
        _save_json_file(config.BOOKMARK_FILE, bookmarks)
        excerpt = " ".join(sentences)[:3500]
        print(f"📄 [Tool Call -> Document Summary]: Trích xuất {len(excerpt)} ký tự từ '{file_path.name}'")
        return (
            f"Nội dung trích xuất từ file {file_path.name} (hãy tóm tắt trong 3 câu ngắn gọn cho sếp): "
            f"{excerpt}"
        )

    if action == "doc_tu_dau":
        bm_entry["index"] = 0
    elif action == "doc_lai":
        bm_entry["index"] = max(0, bm_entry["index"] - num_sents)

    start_idx = bm_entry["index"]
    if start_idx >= len(sentences):
        bm_entry["index"] = 0
        _save_json_file(config.BOOKMARK_FILE, bookmarks)
        return f"Đã đọc hết toàn bộ {len(sentences)} câu của file {file_path.name}. Đã đặt lại bookmark về đầu file."

    end_idx = min(len(sentences), start_idx + num_sents)
    chunk_text = " ".join(sentences[start_idx:end_idx])
    bm_entry["index"] = end_idx
    bm_entry["updated_at"] = time.strftime("%H:%M %d/%m/%Y")
    _save_json_file(config.BOOKMARK_FILE, bookmarks)

    print(f"📖 [Tool Call -> Document Reader]: Đọc câu {start_idx + 1}..{end_idx}/{len(sentences)} của '{file_path.name}'")
    return (
        f"Đọc nguyên văn từ câu {start_idx + 1} đến câu {end_idx} trên tổng {len(sentences)} câu của file {file_path.name}: "
        f"{chunk_text}"
    )


# --- Clipboard Assistant ---

def tool_xu_ly_bo_nho_tam_clipboard(args: dict) -> str:
    """Read or write text to system clipboard (Ctrl+C)."""
    action = args.get("thao_tac", "doc")
    text_to_write = args.get("noi_dung_ghi") or ""

    if action == "ghi":
        if not text_to_write:
            return "Không có nội dung để chép vào bộ nhớ tạm."
        try:
            pyperclip.copy(text_to_write)
            print(f"📋 [Tool Call -> Clipboard Write]: Đã copy {len(text_to_write)} ký tự")
            return "Đã sao chép nội dung vào bộ nhớ tạm clipboard cho sếp."
        except Exception as e:
            return f"Không thể ghi vào clipboard: {e}"

    # Default: read clipboard
    try:
        clip_text = pyperclip.paste() or ""
    except Exception as e:
        return f"Không thể đọc bộ nhớ tạm clipboard: {e}"

    clip_text = clip_text.strip()
    if not clip_text:
        return "Bộ nhớ tạm clipboard của sếp hiện đang trống, sếp hãy bôi đen văn bản và bấm Ctrl C trước nhé."

    truncated = clip_text[:3000]
    print(f"📋 [Tool Call -> Clipboard Read]: Đọc {len(truncated)} ký tự từ clipboard")
    return f"Nội dung sếp vừa copy trong clipboard là: {truncated}"


# --- Long-Term Personal Memory ---

def tool_ghi_nho_thong_tin_dai_han(args: dict) -> str:
    """Save, search, view, or delete long-term facts in teo_memory.json."""
    action = args.get("thao_tac", "luu")
    key = (args.get("khoa") or "").strip()
    content = (args.get("noi_dung") or "").strip()
    memories: list[dict] = _load_json_file(config.MEMORY_FILE, [])

    if action == "luu":
        if not key and not content:
            return "Sếp chưa cung cấp thông tin cần ghi nhớ."
        topic = key or content[:40]
        val = content or key
        norm_topic = _strip_accents(topic)
        updated = False
        for m in memories:
            if _strip_accents(m.get("key", "")) == norm_topic:
                m["value"] = val
                m["updated_at"] = time.strftime("%H:%M %d/%m/%Y")
                updated = True
                break
        if not updated:
            memories.append(
                {
                    "key": topic,
                    "value": val,
                    "updated_at": time.strftime("%H:%M %d/%m/%Y"),
                }
            )
        _save_json_file(config.MEMORY_FILE, memories)
        print(f"🧠 [Tool Call -> Long-Term Memory]: Đã nhớ '{topic}' = '{val}'")
        return f"Em đã ghi nhớ vào bộ nhớ dài hạn: {topic} là {val}."

    elif action == "tim_kiem":
        if not key and not content:
            return "Sếp muốn tìm thông tin gì trong bộ nhớ dài hạn?"
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
        q_norm = _strip_accents(key)
        before_len = len(memories)
        memories = [m for m in memories if q_norm not in _strip_accents(m.get("key", ""))]
        if len(memories) == before_len:
            return f"Không tìm thấy mục ghi nhớ nào có từ khóa '{key}' để xóa."
        _save_json_file(config.MEMORY_FILE, memories)
        return f"Đã xóa thông tin '{key}' khỏi bộ nhớ dài hạn."

    # View all
    if not memories:
        return "Bộ nhớ dài hạn của em hiện đang trống."
    all_str = "; ".join(f"{m['key']}: {m['value']}" for m in memories)
    return f"Em đang ghi nhớ {len(memories)} thông tin của sếp: {all_str}."

