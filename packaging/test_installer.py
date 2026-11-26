"""Validate the payload of the final installer on its native build runner."""
from pathlib import Path
import argparse
import os
import subprocess
import sys
import tempfile


def run(command):
    subprocess.run([str(value) for value in command], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("installer", type=Path)
    args = parser.parse_args()
    installer = args.installer.resolve()
    smoke = Path(__file__).with_name("smoke_test.py")
    with tempfile.TemporaryDirectory(prefix="forNMA installed payload ") as temporary:
        destination = Path(temporary)
        if sys.platform == "linux":
            run(["dpkg-deb", "--extract", installer, destination])
            binary = destination / "opt/fornma/forNMA"
            # Run with an immutable installation directory, as under /opt.
            for item in (destination / "opt").rglob("*"):
                if not item.is_symlink():
                    item.chmod(item.stat().st_mode & ~0o222)
            try:
                run([sys.executable, smoke, binary])
            finally:
                for item in (destination / "opt").rglob("*"):
                    if not item.is_symlink():
                        item.chmod(item.stat().st_mode | 0o200)
        elif sys.platform == "win32":
            target = destination / "app"
            run([installer, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                 "/SP-", f"/DIR={target}", f"/LOG={destination / 'setup.log'}"])
            run([sys.executable, smoke, target / "forNMA.exe"])
        elif sys.platform == "darwin":
            mount = destination / "mounted"
            mount.mkdir()
            run(["hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint", mount, installer])
            try:
                run([sys.executable, smoke, mount / "forNMA.app/Contents/MacOS/forNMA"])
            finally:
                run(["hdiutil", "detach", mount])
        else:
            raise SystemExit(f"Unsupported platform: {sys.platform}")
    print(f"PASS: final installer payload: {installer.name}", flush=True)


if __name__ == "__main__":
    main()
