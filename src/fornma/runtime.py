"""Writable locations and subprocess commands for source and frozen builds."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("FORNMA_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "forNMA"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/forNMA"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "forNMA"


def nma_settings_path() -> Path:
    return data_dir() / "control_parameters.pickle"


def helper_command(action: str, *args: str) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--helper", action, *args]
    return [sys.executable, "-m", "fornma.desktop", "--helper", action, *args]


def setup_runtime() -> None:
    root = data_dir()
    root.mkdir(parents=True, exist_ok=True)
    for variable, folder in (
        ("MPLCONFIGDIR", "matplotlib"),
        ("NUMBA_CACHE_DIR", "numba"),
        ("CELLPOSE_LOCAL_MODELS_PATH", "models"),
    ):
        target = root / folder
        target.mkdir(exist_ok=True)
        os.environ[variable] = str(target)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["MPLBACKEND"] = "Agg"
