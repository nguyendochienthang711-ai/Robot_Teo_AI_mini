import json
import unicodedata
from pathlib import Path


def _strip_accents(text: str) -> str:
    """Strip Vietnamese accents for case-insensitive and accent-insensitive search."""
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    ).lower()


def _load_json_file(path: Path, default):
    """Safely load JSON data from disk or return default value."""
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _save_json_file(path: Path, data):
    """Save data to JSON file with UTF-8 encoding and indentation."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

