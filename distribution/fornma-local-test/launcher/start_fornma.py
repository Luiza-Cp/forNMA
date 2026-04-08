from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


BACKEND_URL = "http://127.0.0.1:8000/health"
FRONTEND_URL = "http://127.0.0.1:4173/"
API_ROOT_URL = "http://127.0.0.1:8000"


def _wait_for_url(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def _check_runtime() -> list[str]:
    missing: list[str] = []
    modules = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("plotly", "plotly"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
    ]
    for import_name, label in modules:
        try:
            __import__(import_name)
        except Exception:
            missing.append(label)
    return missing


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dist_dir = root / "frontend" / "dist"
    if not (dist_dir / "index.html").exists():
        print("Could not find frontend/dist/index.html in the package.", file=sys.stderr)
        return 1

    missing = _check_runtime()
    if missing:
        print("Missing Python modules:", ", ".join(missing), file=sys.stderr)
        print("Run setup_venv.bat or setup_venv.sh first.", file=sys.stderr)
        return 1

    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(root / "src") + (os.pathsep + existing if existing else "")

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "fornma.api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    frontend_cmd = [
        sys.executable,
        "-m",
        "http.server",
        "4173",
        "--bind",
        "127.0.0.1",
        "--directory",
        str(dist_dir),
    ]

    print("Starting forNMA backend...")
    print(f"  API: {API_ROOT_URL}")
    backend = subprocess.Popen(backend_cmd, cwd=root, env=env)
    print("Starting local frontend server...")
    print(f"  Frontend: {FRONTEND_URL}")
    frontend = subprocess.Popen(frontend_cmd, cwd=root, env=env)

    processes = [frontend, backend]
    try:
        if not _wait_for_url(BACKEND_URL, timeout=45):
            print("Backend did not become ready in time.", file=sys.stderr)
            return 1
        if not _wait_for_url(FRONTEND_URL, timeout=20):
            print("Frontend did not become ready in time.", file=sys.stderr)
            return 1

        print(f"Opening {FRONTEND_URL}")
        webbrowser.open(FRONTEND_URL)
        print("forNMA is running.")
        print(f"  Frontend URL: {FRONTEND_URL}")
        print(f"  Backend URL: {API_ROOT_URL}")
        print("Press Ctrl+C in this window to stop it.")

        while True:
            for proc, name in ((backend, "backend"), (frontend, "frontend")):
                code = proc.poll()
                if code is not None:
                    print(f"The {name} process exited with code {code}.", file=sys.stderr)
                    return code or 1
            time.sleep(0.8)
    except KeyboardInterrupt:
        print("\nStopping forNMA...")
        return 0
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        deadline = time.time() + 5
        for proc in processes:
            if proc.poll() is None:
                remaining = max(0.1, deadline - time.time())
                try:
                    proc.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
