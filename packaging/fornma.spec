"""Build on the target OS in the isolated CPU environment."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).parent
datas = [(str(root / "frontend" / "dist"), "frontend/dist"),
         (str(root / "build" / "desktop-models"), "models")]
datas += collect_data_files("fornma", includes=["resources/*.toml", "core/Segmentation/parameters.toml"])
binaries = []
hiddenimports = [name for name in collect_submodules("fornma")
                 if name == "fornma" or name.split(".")[1] in
                 {"core", "api", "shared", "runtime", "desktop", "cli", "utils"}]
hiddenimports += ["tkinter", "tkinter.filedialog", "uvicorn.logging", "uvicorn.loops.asyncio",
                  "uvicorn.protocols.http.h11_impl", "uvicorn.lifespan.on", "curator.app"]
# napari and Cellpose use dynamic imports and package resources.
for package in ("curator", "napari", "cellpose", "umap"):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports
for distribution in ("napari-TRACE", "napari", "magicgui", "app-model", "npe2"):
    datas += copy_metadata(distribution)

a = Analysis([str(root / "packaging" / "desktop_entry.py")],
             pathex=[str(root / "src")], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports,
             excludes=["tensorflow", "PySide6", "PyQt6"],
             hooksconfig={"matplotlib": {"backends": ["Agg", "TkAgg"]}},
             noarchive=False,
             module_collection_mode={"cellpose": "py", "numba": "py", "umap": "py"})
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="forNMA", debug=False,
          strip=False, upx=False, console=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="forNMA")
