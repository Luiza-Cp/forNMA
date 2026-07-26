# src/fornma/shared/progress.py
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
    # Optional append-only log stream for UI consoles.
    append_log = updates.pop("append_log", None)
    append_preview_path = updates.pop("append_preview_path", None)
    if append_log:
        prev = str(d.get("log_history", "") or "")
        line = str(append_log).rstrip()
        if line:
            d["log_history"] = f"{prev}\n{line}".strip() if prev else line
    if append_preview_path:
        prev_paths = d.get("preview_paths") or []
        p = str(append_preview_path)
        if p and p not in prev_paths:
            prev_paths.append(p)
        d["preview_paths"] = prev_paths
    d.update(updates)
    _write(path, d)

def cancel_requested(path: str | None) -> bool:
    if not path or not os.path.exists(path):
        return False
    return bool(_read(path).get("cancel"))
