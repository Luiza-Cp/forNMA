"""Wrap the frozen Linux folder in a user-installable Debian package."""
from pathlib import Path
import argparse
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--version", default="0.1.0+cpu")
args = parser.parse_args()
bundle = root / "build" / "desktop-dist" / "forNMA"
if not (bundle / "forNMA").is_file():
    raise SystemExit("Build the frozen app before creating the .deb")
staging = root / "build" / "deb-root"
if staging.exists():
    shutil.rmtree(staging)
shutil.copytree(bundle, staging / "opt" / "fornma")
for directory in ("DEBIAN", "usr/bin", "usr/share/applications", "usr/share/icons/hicolor/256x256/apps"):
    (staging / directory).mkdir(parents=True, exist_ok=True)
(staging / "DEBIAN/control").write_text(f"""Package: fornma
Version: {args.version}
Architecture: amd64
Maintainer: Luiza Cherobini Pereira <luiza.cp1998@gmail.com>
Section: science
Priority: optional
Depends: libc6 (>= 2.35), libstdc++6, libgcc-s1, libgl1, libegl1, libx11-6, libxext6, libxrender1, libxkbcommon0, libxcb1, libxcb-cursor0, libxcb-xinerama0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-render-util0, libdbus-1-3, fontconfig, xdg-utils
Description: Single-cell image analysis with a local web interface (CPU)
 Includes Python, the analysis dependencies and Cellpose model weights.
""", encoding="utf-8")
launcher = staging / "usr/bin/fornma-desktop"
launcher.write_text('#!/bin/sh\nexec /opt/fornma/forNMA "$@"\n', encoding="utf-8")
launcher.chmod(0o755)
(staging / "usr/share/applications/fornma.desktop").write_text("""[Desktop Entry]
Type=Application
Name=forNMA (CPU)
Comment=Single-cell image analysis
Exec=fornma-desktop
Icon=fornma
Terminal=true
Categories=Science;Biology;
""", encoding="utf-8")
from PIL import Image
with Image.open(root / "frontend/public/fornma-logo-AP.png") as image:
    image.thumbnail((256, 256))
    image.save(staging / "usr/share/icons/hicolor/256x256/apps/fornma.png")
output = root / "release"
output.mkdir(exist_ok=True)
target = output / f"fornma_{args.version}_amd64.deb"
subprocess.run(["dpkg-deb", "--root-owner-group", "-Zgzip", "--build", str(staging), str(target)], check=True)
print(target)
