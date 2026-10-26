"""Wrap the native PyInstaller app in a drag-to-Applications disk image."""
import argparse
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("Build the .dmg on macOS")
    arch = {"arm64": "arm64", "x86_64": "x64"}.get(platform.machine())
    if arch is None:
        raise SystemExit(f"Unsupported Mac architecture: {platform.machine()}")
    root = Path(__file__).resolve().parents[2]
    bundle = root / "build/desktop-dist/forNMA.app"
    if not (bundle / "Contents/MacOS/forNMA").is_file():
        raise SystemExit("Build the frozen macOS app before creating the .dmg")
    staging = root / "build/dmg-root"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    shutil.copytree(bundle, staging / bundle.name, symlinks=True)
    (staging / "Applications").symlink_to("/Applications", target_is_directory=True)
    (staging / "READ-ME.txt").write_text(
        "Drag forNMA.app to Applications, then open it.\n"
        "The interface opens in your default browser. Closing the tab does not stop the server.\n"
        "To stop forNMA, quit its process in Activity Monitor.\n"
        "Settings and logs: ~/Library/Application Support/forNMA\n"
        "This test build is not Developer ID signed or notarized.\n",
        encoding="utf-8",
    )
    release = root / "release"
    release.mkdir(exist_ok=True)
    target = release / f"forNMA-{args.version}-cpu-macos-{arch}.dmg"
    subprocess.run(["hdiutil", "create", "-volname", "forNMA (CPU)",
                    "-srcfolder", str(staging), "-format", "UDZO", "-ov", str(target)], check=True)
    subprocess.run(["hdiutil", "verify", str(target)], check=True)
    print(target)


if __name__ == "__main__":
    main()
