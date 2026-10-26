# Development

## Python environment

Run commands from the repository root. Python 3.10–3.12 is supported; use
Python 3.11 for desktop installer builds.

```sh
python -m venv .venv
# Linux / macOS:
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[test]'
```

Alternatively, use `conda env create -f environment.yml`, then
`conda activate fornma`. That environment also includes napari-TRACE for the
alternative curator. A graphical desktop and working OpenGL are required for
napari. The application CLI is available as `fornma`.

Runtime dependencies and package metadata are defined in `pyproject.toml`.
`requirements.txt` installs that same project, and `environment.yml` provides
a portable Conda setup. The previous Linux Conda export is preserved under
`packaging/legacy/` for reference; current CPU installer dependencies are defined
under `packaging/`.

## Web interface

Use Node 20 or later:

```sh
cd frontend
npm ci
npm run build
```

`frontend/node_modules/` and `frontend/dist/` are generated locally and ignored
by Git. Commit changes to `frontend/package-lock.json` when dependencies change.

For development, start the API from the repository root:

```sh
python -m uvicorn fornma.api.main:app --host 127.0.0.1 --port 8000
```

In another terminal, run `npm run dev` inside `frontend/`, then open
`http://localhost:5173`.

## Validation

Run `python -m pytest` from the repository root. Some older integration tests
use local datasets under `tests/data/`, which are not distributed with the
source. Keep those datasets and generated `tests/results/` out of Git.
Tests using synthetic data or temporary directories can run without those
private datasets. Report which tests and datasets were used when contributing.

Desktop builds use a dedicated environment and packaged smoke tests. See
[packaging/README.md](packaging/README.md) for platform requirements and commands.

## Repository contents

Keep source code, tests, documentation, build scripts and dependency lockfiles
in Git. Keep virtual environments, caches, generated distributions, analysis
outputs and local assistant/editor configuration out of Git.

Installers belong in GitHub Releases. The local `release/` directory holds
installers, checksums and validation notes and is ignored by Git. Older local
`distribution/` snapshots and their legacy generator are also ignored; current
installers are built with `packaging/build_desktop.py`.
