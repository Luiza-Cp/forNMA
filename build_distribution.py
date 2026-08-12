#!/usr/bin/env python3
"""
Regenerate the local-test distribution from the current source tree.

The `distribution/fornma-local-test/` package ships a *snapshot* of the backend
(`src/`) and a prebuilt frontend (`frontend/dist/`). Those go stale whenever the
real source changes, so a user who grabs the repo zip and runs setup/start would
run old code. This script re-syncs them in one step:

    1. copy  src/                -> distribution/fornma-local-test/src/
    2. build frontend (npm run build) and copy frontend/dist/ -> .../frontend/dist/

The distribution's own config (requirements-local-ui.txt, setup/start scripts)
is hand-tuned and intentionally NOT touched here.

Usage:
    python build_distribution.py               # sync src + build & copy frontend
    python build_distribution.py --skip-frontend   # sync src only (reuse existing dist)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "distribution" / "fornma-local-test"
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".pytest_cache")


def _replace_tree(src: Path, dst: Path) -> None:
    if not src.is_dir():
        raise SystemExit(f"Source folder not found: {src}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=_IGNORE)
    print(f"  synced {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")


def sync_backend() -> None:
    print("[1/2] Syncing backend source...")
    _replace_tree(ROOT / "src", DIST / "src")


def build_frontend(skip: bool) -> None:
    frontend = ROOT / "frontend"
    built = frontend / "dist"
    if skip:
        print("[2/2] Skipping frontend build (--skip-frontend); copying existing dist...")
    else:
        print("[2/2] Building frontend (npm run build)...")
        npm = shutil.which("npm")
        if not npm:
            raise SystemExit("npm not found on PATH. Install Node.js, or use --skip-frontend.")
        # shell=True on Windows so npm.cmd resolves; cwd is the frontend folder.
        res = subprocess.run(f'"{npm}" run build', cwd=frontend, shell=True)
        if res.returncode != 0:
            raise SystemExit("Frontend build failed. Run `npm install` in frontend/ and retry.")
    if not (built / "index.html").exists():
        raise SystemExit(f"No built frontend at {built} (expected index.html). Build first.")
    _replace_tree(built, DIST / "frontend" / "dist")


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate distribution/fornma-local-test from source.")
    ap.add_argument("--skip-frontend", action="store_true", help="Reuse existing frontend/dist instead of rebuilding.")
    args = ap.parse_args()

    if not DIST.is_dir():
        raise SystemExit(f"Distribution folder not found: {DIST}")

    sync_backend()
    build_frontend(args.skip_frontend)
    print(f"\nDone. Distribution refreshed at {DIST.relative_to(ROOT)}.")
    print("Commit the updated distribution/ folder so the branch zip ships current code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
