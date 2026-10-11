# forNMA desktop CPU

This build includes Python, the compiled React interface, CPU-only PyTorch,
the four Cellpose model weights, and napari-TRACE as an alternative curator.
The target computer does not need Python, Node, Conda or CUDA.

## Build

Use Python 3.11 and Node 20+ on the target OS:

```sh
python packaging/build_desktop.py
```

The build creates an isolated `.venv-desktop`, downloads CPU dependencies and
model weights, builds the frontend, freezes Python, runs a packaged smoke test,
and writes installers to `release/`. Linux builds use the dependency lock in
`packaging/linux/requirements-lock.txt`. Windows builds resolve compatible
platform-specific wheels and save the exact dependency list in `release/`.

On Linux, build on Ubuntu 22.04 amd64 with `dpkg-deb` available. The `.deb` is
intended for Ubuntu 22.04+ and compatible Debian systems with glibc >= 2.35;
other distributions require separate validation. On Windows, install Inno Setup
6 before building. Each platform must build and test its own installer.

The manual GitHub Actions workflow `Desktop CPU installers` performs these
steps independently on Linux and Windows and uploads the generated artifacts.
Windows installers are unsigned until a code-signing certificate is configured.

## Install and run

Linux:

```sh
sudo apt install ./fornma_0.1.0+cpu_amd64.deb
fornma-desktop
```

Windows: run `forNMA-Setup-0.1.0-cpu-windows-x64.exe` and open the new shortcut.

The launcher opens the default browser after the local server is ready. Keep
the terminal window open while working; Ctrl+C stops the server. Closing a
browser tab does not stop running analyses. API and frontend use the same local
address. Port 8000 is preferred; an occupied port gets a reserved fallback.

Settings, logs and model copies are written under `%LOCALAPPDATA%/forNMA` on
Windows and `$XDG_DATA_HOME/forNMA` (normally `~/.local/share/forNMA`) on Linux.
`FORNMA_DATA_DIR` can override the location. Analysis outputs remain in the
folders chosen by the user. Previous source-tree NMA settings can be imported
with the existing settings upload control.

The build includes the models so the first CPU segmentation can run offline.
Internet is needed for building, not for routine local analysis. The native
correction editor and napari are both included. Native file dialogs need a
graphical desktop; napari additionally needs working OpenGL support.

## Validation

`packaging/smoke_test.py` launches the frozen executable from another working
directory, deliberately occupies its requested port, checks health and every
frontend JS/CSS asset, reads CSV columns, runs tracking on a synthetic movie,
renders its preview and exports the table. `--self-test` additionally verifies
the CPU Torch build, native dialog imports, napari imports and Cellpose inference.
This is technical packaging validation, not a replacement for reviewing real
scientific datasets or testing the installer on clean target machines.
