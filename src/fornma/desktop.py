"""Desktop entry point: one local server for the API and compiled web UI."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import runpy
import shutil
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

from fornma.runtime import data_dir, setup_runtime


def asset_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def seed_models() -> None:
    source = asset_root() / "models"
    if not getattr(sys, "frozen", False):
        source = asset_root() / "build" / "desktop-models"
    destination = data_dir() / "models"
    if source.is_dir():
        for model in source.iterdir():
            if model.is_file() and not (destination / model.name).exists():
                shutil.copy2(model, destination / model.name)


def run_helper(action: str, args: list[str]) -> int:
    if action == "curator":
        sys.argv = ["curator.app", *args]
        # Dynamic entry point is also collected by the desktop PyInstaller spec.
        runpy.run_module("curator.app", run_name="__main__")
        return 0
    if action not in {"pick-csv", "pick-directory"}:
        raise ValueError(f"Unknown helper: {action}")
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        if action == "pick-csv":
            path = filedialog.askopenfilename(
                title="Select dataset CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )
        else:
            path = filedialog.askdirectory(title="Select folder")
    finally:
        root.destroy()
    print(path or "", end="")
    return 0


def create_desktop_app(frontend: Path):
    from fastapi.staticfiles import StaticFiles
    from fornma.api.main import app

    if not (frontend / "index.html").is_file():
        raise RuntimeError(f"Compiled interface is missing: {frontend}")
    # Mount last so /tracking, /segmentation and all API routes take precedence.
    app.mount("/", StaticFiles(directory=frontend, html=True), name="desktop-ui")
    return app


def reserve_socket(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        if not port:
            sock.close()
            raise
        # Reserve the fallback immediately, avoiding a find-free-port race.
        sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    return sock


def open_when_ready(url: str, server, timeout: float = 180) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not server.should_exit:
        try:
            with opener.open(f"{url}/health", timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (OSError, ValueError):
            time.sleep(0.25)
    logging.error("The interface could not open automatically. Open %s", url)


def self_test() -> int:
    """Exercise bundled imports, CPU inference, assets and native dialog imports."""
    import numpy as np
    import torch
    import tkinter
    # Importing curator.app creates a QApplication. Keep it out of normal startup.
    import curator.app
    import scikit_posthocs
    from fornma.core.Statistics.OneWayAnalysis import OneWayAnalysis
    from fornma.core.Statistics.TwoWayAnalysis import TwoWayAnalysis
    from fornma.core.Segmentation.segmentation.cellpose_integration import get_cellpose_model
    from fornma.core.Tracking.tracking import run_laptracker
    from fornma.core.UMAP import umap_tools
    from fornma.api.main import app

    if torch.version.cuda is not None:
        raise RuntimeError(f"This package includes CUDA: {torch.__version__}")
    assert tkinter.Tcl().eval("info library")
    posthoc = scikit_posthocs.posthoc_dunn([[1, 2, 3], [8, 9, 10]])
    assert posthoc.shape == (2, 2)
    model = get_cellpose_model("nuclei", use_gpu=True)
    if model.gpu:
        raise RuntimeError("Cellpose must use CPU even with a legacy GPU parameter")
    y, x = np.mgrid[:64, :64]
    image = np.exp(-((x - 32) ** 2 + (y - 32) ** 2) / 80).astype(np.float32)
    masks, *_ = model.eval(image, channels=[0, 0], diameter=20)
    assert masks.shape == image.shape
    frontend = asset_root() / "frontend" / "dist"
    assert (frontend / "index.html").is_file()
    print(json.dumps({"status": "ok", "torch": torch.__version__, "device": str(model.device),
                      "routes": len(app.routes), "frontend": str(frontend)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="forNMA desktop (CPU)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--helper", choices=["pick-csv", "pick-directory", "curator"])
    parser.add_argument("helper_args", nargs="*")
    args = parser.parse_args(argv)
    setup_runtime()
    seed_models()
    if args.helper:
        return run_helper(args.helper, args.helper_args)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(data_dir() / "desktop.log", encoding="utf-8")],
    )
    if args.self_test:
        return self_test()
    import uvicorn

    frontend = asset_root() / "frontend" / "dist"
    sock = reserve_socket(args.port)
    try:
        url = f"http://127.0.0.1:{sock.getsockname()[1]}"
        print(f"Starting forNMA (CPU): {url}\nKeep this window open. Press Ctrl+C to stop.", flush=True)
        app = create_desktop_app(frontend)
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", log_level="info", loop="asyncio"))
        if not args.no_browser:
            threading.Thread(target=open_when_ready, args=(url, server), daemon=True).start()
        server.run(sockets=[sock])
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
