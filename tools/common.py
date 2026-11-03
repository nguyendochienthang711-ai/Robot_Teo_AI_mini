import copy
import json
import logging
import os
import threading
import time
import unicodedata
from pathlib import Path

log = logging.getLogger("teo.common")
_io_lock = threading.RLock()


def _strip_accents(s: str) -> str:
    """Strip Vietnamese accents for resilient matching."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def load_json(path: Path, default):
    """Load JSON file safely with type verification and corrupt backup (TL-05)."""
    with _io_lock:
        if not path.exists():
            return copy.deepcopy(default)
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            if default is not None and not isinstance(data, type(default)):
                raise ValueError(f"unexpected JSON type in {path}: expected {type(default)}, got {type(data)}")
            return data
        except (OSError, ValueError) as err:
            bak = path.with_name(f"{path.stem}.corrupt-{int(time.time())}{path.suffix}")
            try:
                path.replace(bak)
                log.error("Corrupted JSON %s backed up to %s (error: %s)", path, bak, err)
            except OSError:
                pass
            return copy.deepcopy(default)


def save_json(path: Path, data) -> None:
    """Atomic write via temporary file replacement (TL-05)."""
    with _io_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)


def update_json(path: Path, default, mutate):
    """Read-modify-write in an atomic thread-safe lock (TL-05)."""
    with _io_lock:
        data = load_json(path, default)
        result = mutate(data)
        save_json(path, data)
        return result


def _load_json_file(file_path: Path, default=None):
    """Backward compatibility wrapper."""
    if default is None:
        default = []
    return load_json(file_path, default)


def _save_json_file(file_path: Path, data):
    """Backward compatibility wrapper."""
    save_json(file_path, data)
