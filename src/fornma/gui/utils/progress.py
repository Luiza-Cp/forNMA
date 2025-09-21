# src/fornma/gui/utils/progress.py
import json, os
from typing import Any, Dict

def _read(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _write(path: str, data: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)

def update_progress(path: str, **updates) -> None:
    if not path:
        return
    d = _read(path)
    d.update(updates)
    _write(path, d)

def cancel_requested(path: str | None) -> bool:
    if not path or not os.path.exists(path):
        return False
    return bool(_read(path).get("cancel"))
