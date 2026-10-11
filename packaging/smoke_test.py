"""Run the actual frozen executable from a different working directory."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("executable", type=Path)
args = parser.parse_args()
executable = args.executable.resolve()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request(base, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=60) as response:
        content = response.read()
        return json.loads(content) if "application/json" in response.headers.get("Content-Type", "") else content


with tempfile.TemporaryDirectory(prefix="fornma-package-test-") as temporary:
    root = Path(temporary)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["FORNMA_DATA_DIR"] = str(root / "user-data")
    env["XDG_CACHE_HOME"] = str(root / "cache")
    env["QT_QPA_PLATFORM"] = "offscreen"
    # Test a port collision: the launcher must reserve a fallback and print its URL.
    occupied = socket.socket()
    occupied.bind(("127.0.0.1", 0))
    occupied.listen()
    with (root / "server.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([str(executable), "--no-browser", "--port", str(occupied.getsockname()[1])],
                                   cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 180
            base = None
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError((root / "server.log").read_text())
                match = re.search(r"Starting forNMA \(CPU\): (http://127\.0\.0\.1:\d+)",
                                  (root / "server.log").read_text())
                if match:
                    base = match[1]
                    try:
                        if request(base, "/health")["status"] == "ok":
                            break
                    except OSError:
                        pass
                time.sleep(0.4)
            else:
                raise RuntimeError("Packaged server did not become ready")
            assert base != f"http://127.0.0.1:{occupied.getsockname()[1]}"
            html = request(base, "/").decode()
            for asset in re.findall(r'(?:src|href)="(/assets/[^\"]+)"', html):
                assert len(request(base, asset)) > 0
            table = root / "example.csv"
            table.write_text("Condition,Nuc_Area,Nuc_NII\nControl,100,0.1\nTreatment,120,0.2\n")
            columns = request(base, "/nma/datasets/columns", {"path": str(table)})
            assert "Nuc_Area" in columns["columns"]
            # Tiny three-frame movie, enough to exercise linking, rendering and export.
            from PIL import Image
            images = root / "images"
            images.mkdir()
            tracking = root / "tracking.csv"
            with tracking.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Cell", "X", "Y", "Frame", "Image_name_DAPI"])
                for frame in range(3):
                    name = f"frame{frame}.tif"
                    Image.new("L", (64, 64), color=80).save(images / name)
                    writer.writerow([1, 20 + frame, 25, frame, name])
                    writer.writerow([2, 45, 40 + frame, frame, name])
            tracked = request(base, "/tracking/run", {"path_to_table": str(tracking),
                              "image_dir": str(images), "image_col": "Image_name_DAPI",
                              "output_dir": str(root / "tracks")})
            assert Path(tracked["table_path"]).is_file()
            assert Path(tracked["preview_image_path"]).is_file()
            saved = request(base, "/tracking/save-results", {"table_path": tracked["table_path"],
                            "output_dir": str(root / "export"), "include_images": False})
            assert Path(saved["table_path"]).is_file(), saved
            print("PASS: frozen server, occupied-port fallback, frontend assets, CSV, tracking preview/export")
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            occupied.close()
    subprocess.run([str(executable), "--self-test"], cwd=root, env=env, check=True, timeout=240)
