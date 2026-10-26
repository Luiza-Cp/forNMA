"""Repeatable CPU build using a dedicated virtual environment on the target OS."""
import argparse
import json
from pathlib import Path
import os
import platform
import subprocess
import sys
import venv

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--skip-install", action="store_true", help="Use the current Python environment")
parser.add_argument("--skip-frontend", action="store_true")
args = parser.parse_args()
if sys.platform not in {"linux", "win32", "darwin"}:
    raise SystemExit("Desktop installer targets are Windows, Linux and macOS")
python = Path(sys.executable)
if not args.skip_install:
    environment = root / ".venv-desktop"
    venv.create(environment, with_pip=True)
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(command, **kwargs):
    subprocess.run([str(item) for item in command], cwd=root, check=True, **kwargs)


if not args.skip_install:
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    if sys.platform != "darwin":
        run([python, "-m", "pip", "install", "torch==2.5.1+cpu", "--index-url", "https://download.pytorch.org/whl/cpu"])
    if sys.platform == "linux":
        run([python, "-m", "pip", "install", "-r", "packaging/linux/requirements-lock.txt"])
    run([python, "-m", "pip", "install", "-r", "packaging/requirements-cpu.txt", "."])
    run([python, "-m", "pip", "check"])
if not args.skip_frontend:
    import shutil
    npm = shutil.which("npm")
    if not npm:
        raise SystemExit("Node/npm is required for building, but not for running the installed app")
    subprocess.run([npm, "ci"], cwd=root / "frontend", check=True, shell=sys.platform == "win32")
    subprocess.run([npm, "run", "build"], cwd=root / "frontend", check=True, shell=sys.platform == "win32")
environment = os.environ.copy()
environment["PYTHONPATH"] = str(root / "src")
environment["XDG_CACHE_HOME"] = str(root / "build" / "cache")
environment["MPLCONFIGDIR"] = str(root / "build" / "matplotlib")
environment["NUMBA_CACHE_DIR"] = str(root / "build" / "numba")
environment["QT_QPA_PLATFORM"] = "offscreen"
run([python, "packaging/prepare_models.py"], env=environment)
run([python, "-m", "PyInstaller", "--noconfirm", "--distpath", "build/desktop-dist",
     "--workpath", "build/desktop-work", "packaging/fornma.spec"], env=environment)
binary = root / "build/desktop-dist/forNMA" / ("forNMA.exe" if sys.platform == "win32" else "forNMA")
if sys.platform == "darwin":
    binary = root / "build/desktop-dist/forNMA.app/Contents/MacOS/forNMA"
run([python, "packaging/smoke_test.py", binary], env=environment)
release = root / "release"
release.mkdir(exist_ok=True)
dependency_platform = f"darwin-{platform.machine()}" if sys.platform == "darwin" else sys.platform
with (release / f"dependencies-{dependency_platform}-cpu.txt").open("w") as handle:
    subprocess.run([str(python), "-m", "pip", "freeze"], stdout=handle, check=True)
if sys.platform == "linux":
    run([python, "packaging/linux/package_deb.py"])
elif sys.platform == "win32":
    compiler = Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Inno Setup 6/ISCC.exe"
    run([compiler, "packaging/windows/fornma.iss"])
elif sys.platform == "darwin":
    run([python, "packaging/macos/package_dmg.py"])
