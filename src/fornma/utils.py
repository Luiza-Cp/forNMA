from importlib.resources import files
from pathlib import Path
import shutil

def export_parameters_toml(dest: str):
    src = files("fornma.resources") / "parameters.toml"
    dest_path = Path(dest)
    if dest_path.is_dir():
        dest_path = dest_path / "parameters.toml"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest_path)
    print(f"Parameters TOML copiado para: {dest_path}")
