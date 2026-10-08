from __future__ import annotations

from pathlib import Path
import pickle
from typing import Dict
import threading
import uuid
import os
import json
import tempfile
import hashlib
import base64
import mimetypes
import shutil
from datetime import datetime
import subprocess
import sys
import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.colors import qualitative as qual_colors
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from fornma.core.NMA.plot_NMA import plot_NMA as run_nma_plot, NMA as NMAClass
from fornma.core.Segmentation.run import run as run_segmentation_pipeline
from fornma.core.Registration.registration import registration as run_registration_pipeline
from fornma.core.Tracking.tracking import (
    run_laptracker as run_tracking_laptracker,
    find_family as find_tracking_family,
    create_tree_nomenclature as create_tracking_nomenclature,
    draw_track as draw_tracking_frames,
)
from fornma.core.Segmentation.analyze import saving_images
from fornma.core.image_io import imread, imwrite
from fornma.shared.progress import update_progress

from fornma.shared.nma_helpers import (
    load_controls_pool,
    load_all_datasets,
    compute_axis_ranges_from_all,
    ellipse_trace,
    find_nma_measure_columns,
    _resolve_two_columns,
)
from .schemas import (
    NMAComputeRequest,
    NMAComputeResponse,
    NMAAutoDbscanRequest,
    NMAAutoDbscanResponse,
    NMASaveSettingsRequest,
    NMASaveSettingsResponse,
    NMASettingsResponse,
    NMAThresholds,
    NMAPreviewResponse,
    NMAFigureRequest,
    NMAFigureResponse,
    DatasetColumnsRequest,
    DatasetColumnsResponse,
    DatasetColumnValuesRequest,
    DatasetColumnValuesResponse,
    NMASettingsUploadResponse,
    NMAPlotRunRequest,
    NMAPlotStartResponse,
    NMAPlotStatusResponse,
    SegmentationStartRequest,
    SegmentationStartResponse,
    SegmentationStatusResponse,
    RegistrationStartRequest,
    RegistrationStartResponse,
    RegistrationStatusResponse,
    FociChannelsRequest,
    FociChannelsResponse,
    FociStartRequest,
    FociStartResponse,
    FociStatusResponse,
    GraphPreviewRequest,
    GraphPreviewResponse,
    GraphConditionsRequest,
    GraphConditionsResponse,
    UMAPPreviewRequest,
    UMAPPreviewResponse,
    ClusteringElbowResponse,
    StatsRunRequest,
    StatsRunResponse,
    StatsFilter,
    StatsTable,
    GatingPreviewRequest,
    GatingPreviewResponse,
    GatingApplyRequest,
    GatingApplyResponse,
    GatingBounds,
    TrackingRunRequest,
    TrackingSaveRequest,
    TrackingFrameRequest,
    TrackingSelection,
    TrackingPointSelectRequest,
    TrackingPointSelectResponse,
    TrackingMarkersRequest,
    TrackingMarkersResponse,
    TrackingMarker,
    TrackingDeleteRequest,
    TrackingLinkRequest,
    TrackingDivisionRequest,
    TrackingUnlinkRequest,
    TrackingCheckpointRequest,
    TrackingCheckpointResponse,
    TrackingRestoreRequest,
    TrackingProgressSaveRequest,
    TrackingProgressSaveResponse,
    TrackingRunResponse,
    TrackingPreviewResponse,
    TrackingEditResponse,
    TrackingSaveResponse,
    TrackingCurateLaunchRequest,
    TrackingCurateLaunchResponse,
)
from fornma.shared.params_builder import build_interface_params


APP_ROOT = Path(__file__).resolve().parent
NMA_SETTINGS_PATH = (APP_ROOT.parent / "core" / "NMA" / "control_parameters.pickle").resolve()

app = FastAPI(title="forNMA API")
PLOT_JOBS: Dict[str, Dict] = {}
PLOT_JOBS_LOCK = threading.Lock()
SEG_JOBS: Dict[str, Dict] = {}
SEG_JOBS_LOCK = threading.Lock()
SEG_THREADS: Dict[str, threading.Thread] = {}
REG_JOBS: Dict[str, Dict] = {}
REG_JOBS_LOCK = threading.Lock()
REG_THREADS: Dict[str, threading.Thread] = {}
FOCI_JOBS: Dict[str, Dict] = {}
FOCI_JOBS_LOCK = threading.Lock()
FOCI_THREADS: Dict[str, threading.Thread] = {}
CLUSTER_CACHE: Dict[str, Dict] = {}
CLUSTER_CACHE_LOCK = threading.Lock()
CLUSTER_CACHE_MAX_ITEMS = 6

# Allow local dev frontends (Vite) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def _is_display_column(name: str) -> bool:
    return "unnamed" not in str(name).strip().lower()


def _normalize_filter_value(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (np.integer, int)):
        return str(int(value))
    if isinstance(value, (np.floating, float)):
        value = float(value)
        if value.is_integer():
            return str(int(value))
        return format(value, "g")
    return str(value).strip()


@app.post("/nma/datasets/columns", response_model=DatasetColumnsResponse)
def nma_datasets_columns(req: DatasetColumnsRequest):
    try:
        df = pd.read_csv(req.path, nrows=2000)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV header: {e}")
    cols = [str(c) for c in df.columns.tolist() if _is_display_column(c)]
    categorical_cols = []
    for c in cols:
        s = df[c]
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_categorical_dtype(s) or pd.api.types.is_bool_dtype(s):
            categorical_cols.append(c)
            continue
        nun = int(s.nunique(dropna=True))
        if nun > 0 and nun <= 20:
            categorical_cols.append(c)
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    return DatasetColumnsResponse(
        columns=cols,
        categorical_columns=categorical_cols,
        numeric_columns=numeric_cols,
        area_columns=find_nma_measure_columns(cols, "Area"),
        nii_columns=find_nma_measure_columns(cols, "NII"),
    )


@app.post("/datasets/column-values", response_model=DatasetColumnValuesResponse)
def dataset_column_values(req: DatasetColumnValuesRequest):
    paths = [str(p).strip() for p in (req.paths or []) if str(p).strip()]
    if not paths:
        raise HTTPException(status_code=400, detail="Provide at least one CSV path.")
    column = str(req.column or "").strip()
    if not column:
        raise HTTPException(status_code=400, detail="Provide a column name.")

    values = set()
    limit = max(1, min(int(req.limit or 200), 1000))
    for raw_path in paths:
        try:
            df = pd.read_csv(raw_path, usecols=[column])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Column '{column}' was not found in {Path(raw_path).name}.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read values from {Path(raw_path).name}: {e}")

        for value in df[column].dropna().tolist():
            norm = _normalize_filter_value(value)
            if norm:
                values.add(norm)
            if len(values) >= limit:
                break
        if len(values) >= limit:
            break

    def _sort_key(item: str):
        try:
            return (0, float(item))
        except Exception:
            return (1, item.casefold())

    return DatasetColumnValuesResponse(column=column, values=sorted(values, key=_sort_key)[:limit])


@app.post("/system/pick-csv")
def system_pick_csv():
    script = textwrap.dedent(
        """
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Select dataset CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        root.destroy()
        print(path or "", end="")
        """
    )
    try:
        res = subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            capture_output=True,
            text=True,
        )
        path = (res.stdout or "").strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to open file picker: {e}")

    if not path:
        raise HTTPException(status_code=400, detail="No file selected.")
    return {"path": path}


@app.post("/system/pick-directory")
def system_pick_directory():
    script = textwrap.dedent(
        """
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory(title="Select output folder")
        root.destroy()
        print(path or "", end="")
        """
    )
    try:
        res = subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            capture_output=True,
            text=True,
        )
        path = (res.stdout or "").strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to open directory picker: {e}")

    if not path:
        raise HTTPException(status_code=400, detail="No directory selected.")
    return {"path": path}


def _png_files_in_dir(output_dir: Path) -> list[str]:
    return sorted([str(p.resolve()) for p in output_dir.glob("*.png") if p.is_file()])


def _set_plot_job(job_id: str, **fields):
    with PLOT_JOBS_LOCK:
        if job_id not in PLOT_JOBS:
            return
        PLOT_JOBS[job_id].update(fields)


def _set_seg_job(job_id: str, **fields):
    with SEG_JOBS_LOCK:
        if job_id not in SEG_JOBS:
            return
        SEG_JOBS[job_id].update(fields)


def _set_reg_job(job_id: str, **fields):
    with REG_JOBS_LOCK:
        if job_id not in REG_JOBS:
            return
        REG_JOBS[job_id].update(fields)


def _set_foci_job(job_id: str, **fields):
    with FOCI_JOBS_LOCK:
        if job_id not in FOCI_JOBS:
            return
        FOCI_JOBS[job_id].update(fields)


def _seg_thread_alive(job_id: str) -> bool:
    with SEG_JOBS_LOCK:
        t = SEG_THREADS.get(job_id)
    return bool(t and t.is_alive())


def _reg_thread_alive(job_id: str) -> bool:
    with REG_JOBS_LOCK:
        t = REG_THREADS.get(job_id)
    return bool(t and t.is_alive())


def _foci_thread_alive(job_id: str) -> bool:
    with FOCI_JOBS_LOCK:
        t = FOCI_THREADS.get(job_id)
    return bool(t and t.is_alive())


def _seg_job_is_active(job_id: str, job: Dict) -> bool:
    if job.get("status") not in {"queued", "running", "canceling", "starting"}:
        return False
    return _seg_thread_alive(job_id)


def _has_active_seg_job() -> bool:
    with SEG_JOBS_LOCK:
        snapshot = list(SEG_JOBS.items())
    return any(_seg_job_is_active(job_id, job) for job_id, job in snapshot)


def _safe_read_json(path: str | None) -> dict:
    if not path:
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _latest_active_job(jobs: Dict[str, Dict], active_states: set[str]) -> Dict | None:
    latest = None
    latest_started = ""
    for job in jobs.values():
        if job.get("status") not in active_states:
            continue
        pf = job.get("progress_file")
        started = ""
        if pf:
            started = str(_safe_read_json(pf).get("started_at", "") or "")
        if latest is None or started >= latest_started:
            latest = job
            latest_started = started
    return latest


def _run_plot_job(job_id: str, req: NMAPlotRunRequest):
    output_dir = Path(req.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    datasets = [d for d in req.params.datasets if str(d.path).strip()]
    if not datasets:
        _set_plot_job(job_id, status="failed", progress=100, error="No dataset paths provided.", message="No dataset paths provided.")
        return

    graph_type = "dot"
    single = False
    overtime = False
    col1 = None
    col2 = None
    sample_size = None
    palette = None
    hue_norm = None
    size_norm = None

    if (req.kind or "dot") == "heatmap":
        graph_type = "jointplot" if req.heatmap.jointplot else "heatmap"
        single = bool(req.heatmap.single)
        overtime = bool(req.heatmap.overtime)
        palette = req.heatmap.palette or "viridis"
    else:
        graph_type = "dot"
        single = bool(req.dot.single)
        overtime = bool(req.dot.overtime)
        col1 = req.dot.column1 or None
        col2 = req.dot.column2 or None
        sample_size = req.dot.sample_size if req.dot.sample_size and req.dot.sample_size > 0 else None
        palette = req.dot.palette or "rainbow"
        if req.dot.hue_min is not None and req.dot.hue_max is not None:
            hue_norm = [float(req.dot.hue_min), float(req.dot.hue_max)]
        if req.dot.size_min is not None and req.dot.size_max is not None:
            size_norm = [float(req.dot.size_min), float(req.dot.size_max)]

    _set_plot_job(job_id, status="running", progress=5, message="Starting NMA plotting...", output_dir=str(output_dir))

    original_save_figs = NMAClass.save_figs
    created_png_files: list[str] = []

    def _normalized_plot_paths() -> list[str]:
        normalized_dir = output_dir / ".nma-normalized-inputs"
        normalized_dir.mkdir(parents=True, exist_ok=True)
        normalized_paths = []
        for index, dataset in enumerate(datasets, start=1):
            raw_path = Path(dataset.path).expanduser()
            try:
                raw = pd.read_csv(raw_path)
            except Exception as e:
                raise RuntimeError(f"Failed to read NMA dataset '{raw_path}': {e}") from e
            area_col, nii_col = _resolve_two_columns(raw, dataset.area_col, dataset.nii_col)
            if not area_col or not nii_col:
                raise RuntimeError(
                    "Could not resolve Area/NII columns for "
                    f"'{raw_path}'. Choose explicit columns in NMA Settings."
                )
            normalized = raw.copy()
            normalized["Area"] = pd.to_numeric(normalized[area_col], errors="coerce")
            normalized["NII"] = pd.to_numeric(normalized[nii_col], errors="coerce")
            safe_name = hashlib.sha1(str(raw_path).encode("utf-8")).hexdigest()[:10]
            out_path = normalized_dir / f"{index:03d}-{safe_name}-Results.csv"
            normalized.to_csv(out_path, index=False)
            normalized_paths.append(str(out_path))
        return normalized_paths

    def _save_with_progress(self, fig, title):
        original_save_figs(self, fig, title)
        png_name = f"{title.lstrip()} {self.graph_type}.png"
        png_path = str((output_dir / png_name).resolve())
        if png_path not in created_png_files:
            created_png_files.append(png_path)
        prev = PLOT_JOBS.get(job_id, {})
        current = int(prev.get("progress", 5))
        next_progress = min(95, current + 8)
        _set_plot_job(
            job_id,
            progress=next_progress,
            message=f"Plotting... ({len(created_png_files)} image(s) saved)",
            files=created_png_files.copy(),
        )

    try:
        # Force non-interactive backend for server-side rendering.
        import matplotlib
        matplotlib.use("Agg", force=True)
        NMAClass.save_figs = _save_with_progress
        paths = _normalized_plot_paths()
        run_nma_plot(
            path_list=paths,
            saving_path=str(output_dir),
            graph_type=graph_type,
            col1=col1,
            col2=col2,
            sample_size=sample_size,
            single=single,
            overtime=overtime,
            palette=palette,
            hue_norm=hue_norm,
            size_norm=size_norm,
        )
        files = [p for p in created_png_files if Path(p).exists()]
        _set_plot_job(
            job_id,
            status="completed",
            progress=100,
            message=f"Plot generation finished successfully. {len(files)} image file(s) were saved to {output_dir}.",
            files=files,
            error=None,
        )
    except Exception as e:
        _set_plot_job(job_id, status="failed", progress=100, error=str(e), message=f"Plot generation failed. Details: {e}")
    finally:
        NMAClass.save_figs = original_save_figs


@app.post("/nma/plots/start", response_model=NMAPlotStartResponse)
def nma_plots_start(req: NMAPlotRunRequest):
    output_dir = Path(req.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not NMA_SETTINGS_PATH.exists():
        raise HTTPException(status_code=400, detail="NMA settings not found. Complete NMA settings first.")

    job_id = str(uuid.uuid4())
    with PLOT_JOBS_LOCK:
        PLOT_JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "Queued",
            "output_dir": str(output_dir),
            "files": [],
            "error": None,
        }

    t = threading.Thread(target=_run_plot_job, args=(job_id, req), daemon=True)
    t.start()
    return NMAPlotStartResponse(job_id=job_id, status="queued")


@app.get("/nma/plots/status/{job_id}", response_model=NMAPlotStatusResponse)
def nma_plots_status(job_id: str):
    with PLOT_JOBS_LOCK:
        job = PLOT_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Plot job not found.")
    return NMAPlotStatusResponse(**job)


@app.get("/nma/plots/active")
def nma_plots_active():
    with PLOT_JOBS_LOCK:
        active = [j for j in PLOT_JOBS.values() if j.get("status") in {"queued", "running"}]
    if not active:
        return {"job": None}
    # Keep deterministic behavior: latest inserted dict item from current memory snapshot.
    return {"job": active[-1]}


@app.get("/nma/plots/file")
def nma_plots_file(path: str = Query(...)):
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="Plot file not found.")
    return FileResponse(path=p, filename=p.name)


def _run_segmentation_job(job_id: str, images_data: dict, seg_data: dict, preview: bool, preview_index: int | None):
    # Force headless plotting in API worker threads (avoid Tk/Tcl backend usage).
    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
    except Exception:
        pass

    params, errs = build_interface_params(images_data, seg_data)
    if errs:
        _set_seg_job(
            job_id,
            status="failed",
            progress=100,
            message="Segmentation could not start because the setup is incomplete.",
            error="\n".join(sorted(set(errs))),
        )
        return

    progress_file = os.path.join(tempfile.gettempdir(), f"_fornma_progress_{uuid.uuid4().hex}.json")
    _set_seg_job(
        job_id,
        progress_file=progress_file,
        status="running",
        progress=0,
        message="Starting...",
        log="",
        preview_paths=[],
        preview_index=preview_index,
    )
    try:
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "status": "starting",
                    "total": 0,
                    "done": 0,
                    "percent": 0,
                    "cancel": False,
                    "started_at": datetime.now().isoformat(timespec="seconds"),
                    "preview_index": preview_index,
                },
                f,
            )
    except Exception:
        pass

    with SEG_JOBS_LOCK:
        stop_before_start = bool(SEG_JOBS.get(job_id, {}).get("cancel_requested"))
    if stop_before_start:
        update_progress(progress_file, status="canceled", cancel=True, message="Segmentation was canceled before processing started.")
        _set_seg_job(job_id, status="canceled", message="Segmentation was canceled before processing started.")
        with SEG_JOBS_LOCK:
            SEG_THREADS.pop(job_id, None)
        return

    try:
        os.environ["FORNMA_PROGRESS_FILE"] = progress_file
        run_segmentation_pipeline(params, preview=bool(preview), preview_index=preview_index)
        d = _safe_read_json(progress_file)
        st = d.get("status", "done")
        percent = int(d.get("percent", 100 if st == "done" else 0))
        _set_seg_job(
            job_id,
            status="completed" if st == "done" else ("canceled" if st == "canceled" else st),
            progress=percent,
            message=(
                f"Segmentation finished successfully. Outputs were saved to {params['global']['output_folder']}."
                if st == "done"
                else ("Segmentation stopped." if st == "canceled" else (d.get("message") or st))
            ),
            log=d.get("log_history") or d.get("log", "") or "",
            preview_path=d.get("preview_path"),
            preview_paths=d.get("preview_paths", []),
            preview_index=d.get("preview_index", preview_index),
            error=d.get("message") if st == "error" else None,
        )
    except Exception as e:
        try:
            if progress_file:
                d = _safe_read_json(progress_file)
                d.update({"status": "error", "message": str(e)})
                with open(progress_file, "w") as f:
                    json.dump(d, f)
        except Exception:
            pass
        _set_seg_job(job_id, status="failed", progress=100, message=f"Segmentation failed. Details: {e}", error=str(e))
    finally:
        with SEG_JOBS_LOCK:
            SEG_THREADS.pop(job_id, None)


@app.post("/segmentation/start", response_model=SegmentationStartResponse)
def segmentation_start(req: SegmentationStartRequest):
    if _has_active_seg_job():
        raise HTTPException(status_code=409, detail="A segmentation job is already running. Wait for it to finish, or click Stop before starting another one.")

    job_id = str(uuid.uuid4())
    with SEG_JOBS_LOCK:
        SEG_JOBS[job_id] = {
            "job_id": job_id,
            "status": "starting",
            "progress": 0,
            "message": "Starting",
            "log": "",
            "preview_path": None,
            "preview_paths": [],
            "preview_index": req.preview_index,
            "progress_file": None,
            "cancel_requested": False,
            "error": None,
        }
        t = threading.Thread(
            target=_run_segmentation_job,
            args=(job_id, req.images_data or {}, req.seg_data or {}, bool(req.preview), req.preview_index),
            daemon=True,
        )
        SEG_THREADS[job_id] = t
    t.start()
    return SegmentationStartResponse(job_id=job_id, status="starting")


@app.get("/segmentation/status/{job_id}", response_model=SegmentationStatusResponse)
def segmentation_status(job_id: str):
    with SEG_JOBS_LOCK:
        job = SEG_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Segmentation job not found.")

    progress_file = job.get("progress_file")
    d = _safe_read_json(progress_file)
    if d:
        st = d.get("status", job.get("status", "running"))
        mapped = {
            "starting": "running",
            "running": "running",
            "canceling": "canceling",
            "done": "completed",
            "error": "failed",
            "canceled": "canceled",
        }.get(st, job.get("status", "running"))
        _set_seg_job(
            job_id,
            status=mapped,
            progress=int(d.get("percent", job.get("progress", 0))),
            message=d.get("message", job.get("message", "")) or job.get("message", ""),
            log=d.get("log_history") or d.get("log", "") or "",
            preview_path=d.get("preview_path", job.get("preview_path")),
            preview_paths=d.get("preview_paths", job.get("preview_paths", [])),
            preview_index=d.get("preview_index", job.get("preview_index")),
            error=d.get("message") if st == "error" else job.get("error"),
        )
        with SEG_JOBS_LOCK:
            job = SEG_JOBS.get(job_id)
    elif _seg_job_is_active(job_id, job):
        # no progress file yet; keep current state while thread is alive
        pass

    if _seg_job_is_active(job_id, job) is False and job.get("status") in {"starting", "queued", "running", "canceling"}:
        cancel_flag = bool(d.get("cancel")) if d else False
        forced_status = "canceled" if cancel_flag else "failed"
        forced_message = (
            "Segmentation stopped."
            if cancel_flag
            else (job.get("message") or "Segmentation stopped unexpectedly before reporting completion. Check the log for the last processed image.")
        )
        _set_seg_job(
            job_id,
            status=forced_status,
            message=forced_message,
            error=None if cancel_flag else (job.get("error") or forced_message),
        )
        with SEG_JOBS_LOCK:
            job = SEG_JOBS.get(job_id)

    return SegmentationStatusResponse(**job)


@app.get("/segmentation/active")
def segmentation_active():
    with SEG_JOBS_LOCK:
        snapshot = list(SEG_JOBS.items())
    active = [(job_id, j) for job_id, j in snapshot if _seg_job_is_active(job_id, j)]
    job = active[-1][1] if active else None
    if not job:
        return {"job": None}
    # Reuse status updater to make sure log/progress are fresh.
    return {"job": segmentation_status(job["job_id"]).model_dump()}


@app.post("/segmentation/stop/{job_id}")
def segmentation_stop(job_id: str):
    with SEG_JOBS_LOCK:
        job = SEG_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Segmentation job not found.")
    _set_seg_job(job_id, cancel_requested=True, status="canceling", message="Stopping after current image...")
    pf = job.get("progress_file")
    if not _seg_thread_alive(job_id):
        _set_seg_job(job_id, status="canceled", message="Segmentation stopped.")
        return {"status": "canceled"}
    if not pf or not os.path.exists(pf):
        return {"status": "canceling"}
    d = _safe_read_json(pf)
    d.update({"cancel": True, "status": "canceling", "message": "Stopping after current image..."})
    try:
        with open(pf, "w") as f:
            json.dump(d, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to request stop: {e}")
    _set_seg_job(job_id, message="Stopping after current image...", status="canceling")
    return {"status": "canceling"}


@app.get("/segmentation/file")
def segmentation_file(path: str = Query(...)):
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path=p, filename=p.name)


@app.get("/tracking/file")
def tracking_file(path: str = Query(...)):
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    if p.suffix.lower() in {".tif", ".tiff"}:
        try:
            import cv2 as cv
            img = imread(p, cv.IMREAD_UNCHANGED)
            if img is None:
                raise HTTPException(status_code=500, detail="Failed to read image file.")
            ok, buf = cv.imencode(".png", img)
            if not ok:
                raise HTTPException(status_code=500, detail="Failed to encode image for preview.")
            return Response(content=buf.tobytes(), media_type="image/png")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to serve tracking preview image: {e}")
    return FileResponse(path=p, filename=p.name)


def _has_active_reg_job() -> bool:
    active_states = {"starting", "queued", "running", "canceling"}
    with REG_JOBS_LOCK:
        snapshot = list(REG_JOBS.items())
    return any((job.get("status") in active_states and _reg_thread_alive(job_id)) for job_id, job in snapshot)


def _run_registration_job(job_id: str, images_data: dict, reg_data: dict):
    rows = (images_data or {}).get("rows", []) or []
    channels_meta = (images_data or {}).get("channels", []) or []
    save_path = str((reg_data or {}).get("save_path") or "").strip()
    reference = (reg_data or {}).get("reference")
    moving = (reg_data or {}).get("moving") or []
    crop = bool((reg_data or {}).get("crop", True))

    id2name = {ch.get("id"): ch.get("name", ch.get("id")) for ch in channels_meta}

    errs = []
    if not save_path:
        errs.append("Choose a Saving path before running registration.")
    if not reference:
        errs.append("Select the reference channel to register. Extra moving channels are optional.")
    if not rows:
        errs.append("No image conditions are loaded. Click Load images and save the condition/channel table first.")
    selected_ids = [ch_id for ch_id in [reference] + list(moving or []) if ch_id]
    for idx, r in enumerate(rows, start=1):
        for ch_id in selected_ids:
            p = str(r.get(ch_id) or "").strip()
            if not p:
                errs.append(f"Row {idx}, {id2name.get(ch_id, ch_id)}: choose the image folder before running registration.")

    if errs:
        _set_reg_job(
            job_id,
            status="failed",
            progress=100,
            message="Registration could not start because the setup is incomplete.",
            log="\n".join(sorted(set(errs))),
            error="\n".join(sorted(set(errs))),
        )
        return

    os.makedirs(save_path, exist_ok=True)
    progress_file = os.path.join(tempfile.gettempdir(), f"_fornma_reg_progress_{uuid.uuid4().hex}.json")
    _set_reg_job(job_id, progress_file=progress_file, status="running", progress=0, done=0, total=len(rows), message="Starting...", log="")
    try:
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "status": "starting",
                    "total": len(rows),
                    "done": 0,
                    "percent": 0,
                    "cancel": False,
                    "started_at": datetime.now().isoformat(timespec="seconds"),
                    "log": "Starting registration...",
                    "log_history": "Starting registration...",
                },
                f,
            )
    except Exception:
        pass

    done = 0
    total = len(rows)
    try:
        for idx, r in enumerate(rows, start=1):
            d = _safe_read_json(progress_file)
            if d.get("cancel"):
                d.update({"status": "canceled", "message": f"Canceled at condition {idx}/{total}."})
                with open(progress_file, "w") as f:
                    json.dump(d, f)
                _set_reg_job(job_id, status="canceled", progress=int(d.get("percent", 0)), message=d.get("message", "Canceled"), log=d.get("log_history", ""))
                return

            cond_name = r.get("condition") or f"cond_{idx}"
            folders_to_register = [str(r.get(reference) or "").strip()] + [str(r.get(mid) or "").strip() for mid in moving]
            log_line = f"[{idx}/{total}] Registering '{cond_name}'..."
            hist = str(d.get("log_history", "") or "")
            d.update({"status": "running", "log": log_line, "log_history": f"{hist}\n{log_line}".strip() if hist else log_line})
            with open(progress_file, "w") as f:
                json.dump(d, f)

            run_registration_pipeline(folders_to_register=folders_to_register, path_to_save=save_path, crop=crop)
            done += 1
            pct = int(done * 100 / total) if total else 100
            done_line = f"[{idx}/{total}] Done '{cond_name}'."
            hist = str(d.get("log_history", "") or "")
            d.update({"done": done, "percent": pct, "log": done_line, "log_history": f"{hist}\n{done_line}".strip() if hist else done_line})
            with open(progress_file, "w") as f:
                json.dump(d, f)
            _set_reg_job(job_id, progress=pct, done=done, total=total, message=done_line, log=d.get("log_history", ""))

        d = _safe_read_json(progress_file)
        hist = str(d.get("log_history", "") or "")
        final_line = f"Registration finished successfully. Registered images were saved to {save_path}."
        d.update({"status": "done", "done": total, "percent": 100, "log": final_line, "log_history": f"{hist}\n{final_line}".strip() if hist else final_line})
        with open(progress_file, "w") as f:
            json.dump(d, f)
        _set_reg_job(job_id, status="completed", progress=100, done=total, total=total, message=final_line, log=d.get("log_history", ""))
    except Exception as e:
        d = _safe_read_json(progress_file)
        hist = str(d.get("log_history", "") or "")
        err_line = f"Registration failed. Details: {e}"
        d.update({"status": "error", "log": err_line, "log_history": f"{hist}\n{err_line}".strip() if hist else err_line, "message": str(e)})
        try:
            with open(progress_file, "w") as f:
                json.dump(d, f)
        except Exception:
            pass
        _set_reg_job(job_id, status="failed", progress=int(d.get("percent", 100)), done=int(d.get("done", done)), total=total, message=err_line, log=d.get("log_history", ""), error=str(e))
    finally:
        with REG_JOBS_LOCK:
            REG_THREADS.pop(job_id, None)


@app.post("/registration/start", response_model=RegistrationStartResponse)
def registration_start(req: RegistrationStartRequest):
    if _has_active_reg_job():
        raise HTTPException(status_code=409, detail="A registration job is already running. Wait for it to finish, or click Stop before starting another one.")
    job_id = str(uuid.uuid4())
    with REG_JOBS_LOCK:
        REG_JOBS[job_id] = {
            "job_id": job_id,
            "status": "starting",
            "progress": 0,
            "done": 0,
            "total": 0,
            "message": "Starting",
            "log": "",
            "progress_file": None,
            "error": None,
        }
        t = threading.Thread(target=_run_registration_job, args=(job_id, req.images_data or {}, req.reg_data or {}), daemon=True)
        REG_THREADS[job_id] = t
    t.start()
    return RegistrationStartResponse(job_id=job_id, status="starting")


@app.get("/registration/status/{job_id}", response_model=RegistrationStatusResponse)
def registration_status(job_id: str):
    with REG_JOBS_LOCK:
        job = REG_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Registration job not found.")

    d = _safe_read_json(job.get("progress_file"))
    if d:
        st = d.get("status", job.get("status", "running"))
        mapped = {"starting": "running", "running": "running", "done": "completed", "error": "failed", "canceled": "canceled"}.get(st, job.get("status", "running"))
        _set_reg_job(
            job_id,
            status=mapped,
            progress=int(d.get("percent", job.get("progress", 0))),
            done=int(d.get("done", job.get("done", 0))),
            total=int(d.get("total", job.get("total", 0))),
            message=d.get("message", d.get("log", job.get("message", ""))) or job.get("message", ""),
            log=d.get("log_history") or d.get("log", "") or "",
            error=d.get("message") if st == "error" else job.get("error"),
        )
        with REG_JOBS_LOCK:
            job = REG_JOBS.get(job_id)

    if not _reg_thread_alive(job_id) and job.get("status") in {"starting", "queued", "running", "canceling"}:
        _set_reg_job(job_id, status="failed", message=job.get("message") or "Registration stopped unexpectedly before reporting completion. Check the log for the last processed condition.")
        with REG_JOBS_LOCK:
            job = REG_JOBS.get(job_id)

    return RegistrationStatusResponse(**job)


@app.post("/registration/stop/{job_id}")
def registration_stop(job_id: str):
    with REG_JOBS_LOCK:
        job = REG_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Registration job not found.")
    pf = job.get("progress_file")
    if not _reg_thread_alive(job_id):
        _set_reg_job(job_id, status="canceled", message="Registration was canceled.")
        return {"status": "canceled"}
    if not pf or not os.path.exists(pf):
        _set_reg_job(job_id, status="canceled", message="Registration was canceled.")
        return {"status": "canceled"}
    d = _safe_read_json(pf)
    d.update({"cancel": True, "status": d.get("status", "running")})
    with open(pf, "w") as f:
        json.dump(d, f)
    _set_reg_job(job_id, status="canceling", message="Stop requested...")
    return {"status": "canceling"}


@app.get("/registration/active")
def registration_active():
    with REG_JOBS_LOCK:
        snapshot = list(REG_JOBS.items())
    active = [(job_id, j) for job_id, j in snapshot if j.get("status") in {"starting", "queued", "running", "canceling"} and _reg_thread_alive(job_id)]
    job = active[-1][1] if active else None
    if not job:
        return {"job": None}
    return {"job": registration_status(job["job_id"]).model_dump()}


def _extract_df_columns_from_pkl(pkl_path: str) -> list[str]:
    try:
        obj = pd.read_pickle(pkl_path)
    except Exception:
        return []

    if isinstance(obj, pd.DataFrame):
        return list(obj.columns)
    if isinstance(obj, dict):
        for key in ("df", "data", "table"):
            val = obj.get(key)
            if isinstance(val, pd.DataFrame):
                return list(val.columns)
        for val in obj.values():
            if isinstance(val, pd.DataFrame):
                return list(val.columns)
    if isinstance(obj, (list, tuple)) and obj and isinstance(obj[0], pd.DataFrame):
        return list(obj[0].columns)
    return []


@app.post("/foci/channels", response_model=FociChannelsResponse)
def foci_channels(req: FociChannelsRequest):
    p = Path(req.pkl_path).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=400, detail="Invalid .pkl folder path.")
    pkl_files = sorted([str(x) for x in p.glob("*.pkl") if x.is_file()])
    if not pkl_files:
        return FociChannelsResponse(channels=[])
    cols = _extract_df_columns_from_pkl(pkl_files[0])
    image_name_cols = [c for c in cols if str(c).startswith("Image_name_")]
    channels = [str(c).split("Image_name_")[-1] for c in image_name_cols]
    return FociChannelsResponse(channels=channels)


def _has_active_foci_job() -> bool:
    active_states = {"starting", "queued", "running", "canceling"}
    with FOCI_JOBS_LOCK:
        snapshot = list(FOCI_JOBS.items())
    return any((job.get("status") in active_states and _foci_thread_alive(job_id)) for job_id, job in snapshot)


def _run_foci_job(job_id: str, req: FociStartRequest):
    pkl_path = str(req.pkl_path or "").strip()
    save_path = str(req.save_path or "").strip() or pkl_path
    actions = list(req.actions or [])
    channels = list(req.channels or [])
    save_images = bool(req.save_images)

    errs = []
    if not pkl_path or not os.path.isdir(pkl_path):
        errs.append("Select a valid Pickles folder generated by the segmentation step.")
    if not actions:
        errs.append("Select at least one action: overlay images, intensity profiles, or both.")
    if errs:
        _set_foci_job(job_id, status="failed", progress=100, message="Foci overlay could not start because the setup is incomplete.", error="\n".join(errs), log="\n".join(errs))
        return

    os.makedirs(save_path, exist_ok=True)
    progress_file = os.path.join(tempfile.gettempdir(), f"_fornma_foci_progress_{uuid.uuid4().hex}.json")
    _set_foci_job(job_id, progress_file=progress_file, status="running", progress=0, message="Starting...", log="")
    try:
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "status": "running",
                    "percent": 0,
                    "cancel": False,
                    "started_at": datetime.now().isoformat(timespec="seconds"),
                    "log": "Starting...",
                    "log_history": "Starting...",
                },
                f,
            )
    except Exception:
        pass

    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
    except Exception:
        pass

    try:
        import importlib
        mod = importlib.import_module("fornma.core.Foci_overlay.foci_overlay")
        run_overlay_func = getattr(mod, "foci_overlay")
        plot_profiles_func = getattr(mod, "plot_profile")

        n = max(1, len(actions))
        span = max(1, 100 // n)
        base = 0
        for action in actions:
            d = _safe_read_json(progress_file)
            if d.get("cancel"):
                d.update({"status": "canceled", "log": "Canceled by user."})
                with open(progress_file, "w") as f:
                    json.dump(d, f)
                _set_foci_job(job_id, status="canceled", progress=int(d.get("percent", base)), message="Canceled by user.", log=d.get("log_history", "") or d.get("log", ""))
                return

            hist = str(d.get("log_history", "") or "")
            log_line = f"Running {action}..."
            d.update({"status": "running", "percent": base, "log": log_line, "log_history": f"{hist}\n{log_line}".strip() if hist else log_line})
            with open(progress_file, "w") as f:
                json.dump(d, f)
            _set_foci_job(job_id, progress=base, message=log_line, log=d.get("log_history", ""))

            if action == "overlay":
                run_overlay_func(
                    pkl_results_folder_path=pkl_path,
                    path_to_save=save_path,
                    channel_list=(channels or None),
                    save_images=save_images,
                    progress_file=progress_file,
                    pct_base=base,
                    pct_span=span,
                )
            elif action == "profiles":
                plot_profiles_func(
                    path_pickle_data=pkl_path,
                    path_save=save_path,
                    columns=(channels or None),
                    progress_file=progress_file,
                    pct_base=base,
                    pct_span=span,
                )
            base = min(100, base + span)
            d = _safe_read_json(progress_file)
            _set_foci_job(job_id, progress=int(d.get("percent", base)), message=d.get("log", f"Finished {action}"), log=d.get("log_history") or d.get("log", ""))

        d = _safe_read_json(progress_file)
        hist = str(d.get("log_history", "") or "")
        final_line = f"Foci overlay finished successfully. Output files were saved to {save_path}."
        d.update({"status": "done", "percent": 100, "log": final_line, "log_history": f"{hist}\n{final_line}".strip() if hist else final_line})
        with open(progress_file, "w") as f:
            json.dump(d, f)
        _set_foci_job(job_id, status="completed", progress=100, message=final_line, log=d.get("log_history", ""))
    except Exception as e:
        d = _safe_read_json(progress_file)
        hist = str(d.get("log_history", "") or "")
        err_line = f"Foci overlay failed. Details: {e}"
        d.update({"status": "error", "log": err_line, "message": str(e), "log_history": f"{hist}\n{err_line}".strip() if hist else err_line})
        try:
            with open(progress_file, "w") as f:
                json.dump(d, f)
        except Exception:
            pass
        _set_foci_job(job_id, status="failed", progress=int(d.get("percent", 100)), message=err_line, log=d.get("log_history", ""), error=str(e))
    finally:
        with FOCI_JOBS_LOCK:
            FOCI_THREADS.pop(job_id, None)


@app.post("/foci/start", response_model=FociStartResponse)
def foci_start(req: FociStartRequest):
    if _has_active_foci_job():
        raise HTTPException(status_code=409, detail="A foci overlay job is already running. Wait for it to finish, or click Stop before starting another one.")
    job_id = str(uuid.uuid4())
    with FOCI_JOBS_LOCK:
        FOCI_JOBS[job_id] = {
            "job_id": job_id,
            "status": "starting",
            "progress": 0,
            "message": "Starting",
            "log": "",
            "progress_file": None,
            "error": None,
        }
        t = threading.Thread(target=_run_foci_job, args=(job_id, req), daemon=True)
        FOCI_THREADS[job_id] = t
    t.start()
    return FociStartResponse(job_id=job_id, status="starting")


@app.get("/foci/status/{job_id}", response_model=FociStatusResponse)
def foci_status(job_id: str):
    with FOCI_JOBS_LOCK:
        job = FOCI_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Foci job not found.")

    d = _safe_read_json(job.get("progress_file"))
    if d:
        st = d.get("status", job.get("status", "running"))
        mapped = {"starting": "running", "running": "running", "done": "completed", "error": "failed", "canceled": "canceled"}.get(st, job.get("status", "running"))
        _set_foci_job(
            job_id,
            status=mapped,
            progress=int(d.get("percent", job.get("progress", 0))),
            message=d.get("message", d.get("log", job.get("message", ""))) or job.get("message", ""),
            log=d.get("log_history") or d.get("log", "") or "",
            error=d.get("message") if st == "error" else job.get("error"),
        )
        with FOCI_JOBS_LOCK:
            job = FOCI_JOBS.get(job_id)

    if not _foci_thread_alive(job_id) and job.get("status") in {"starting", "queued", "running", "canceling"}:
        _set_foci_job(job_id, status="failed", message=job.get("message") or "Foci overlay stopped unexpectedly before reporting completion. Check the log for the last completed action.")
        with FOCI_JOBS_LOCK:
            job = FOCI_JOBS.get(job_id)

    return FociStatusResponse(**job)


@app.post("/foci/stop/{job_id}")
def foci_stop(job_id: str):
    with FOCI_JOBS_LOCK:
        job = FOCI_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Foci job not found.")
    pf = job.get("progress_file")
    if not _foci_thread_alive(job_id):
        _set_foci_job(job_id, status="canceled", message="Foci overlay was canceled.")
        return {"status": "canceled"}
    if not pf or not os.path.exists(pf):
        _set_foci_job(job_id, status="canceled", message="Foci overlay was canceled.")
        return {"status": "canceled"}
    d = _safe_read_json(pf)
    d.update({"cancel": True, "status": d.get("status", "running")})
    with open(pf, "w") as f:
        json.dump(d, f)
    _set_foci_job(job_id, status="canceling", message="Stop requested...")
    return {"status": "canceling"}


@app.get("/foci/active")
def foci_active():
    with FOCI_JOBS_LOCK:
        snapshot = list(FOCI_JOBS.items())
    active = [(job_id, j) for job_id, j in snapshot if j.get("status") in {"starting", "queued", "running", "canceling"} and _foci_thread_alive(job_id)]
    job = active[-1][1] if active else None
    if not job:
        return {"job": None}
    return {"job": foci_status(job["job_id"]).model_dump()}


def _params_to_dict(req) -> Dict:
    return {"datasets": [d.model_dump() for d in req.params.datasets]}


def _has_control(params: Dict) -> bool:
    return any(ds.get("is_control") for ds in params.get("datasets", []))


def _require_controls(pool: pd.DataFrame | None, log: str):
    if pool is None or pool.empty:
        raise HTTPException(status_code=400, detail=f"No control data. Details:\n{log}")


def _compute_stats(pool: pd.DataFrame, xcol: str, ycol: str) -> Dict[str, float]:
    mu_x = float(pool[xcol].mean())
    mu_y = float(pool[ycol].mean())
    sd_x = float(pool[xcol].std(ddof=1) or 1.0)
    sd_y = float(pool[ycol].std(ddof=1) or 1.0)
    return {"mu_x": mu_x, "mu_y": mu_y, "sd_x": sd_x, "sd_y": sd_y}


def _clean_nma_xy(pool: pd.DataFrame, xcol: str, ycol: str) -> pd.DataFrame:
    clean = pool.copy()
    clean[xcol] = pd.to_numeric(clean[xcol], errors="coerce")
    clean[ycol] = pd.to_numeric(clean[ycol], errors="coerce")
    clean = clean.dropna(subset=[xcol, ycol])
    return clean


def _apply_control_gate(pool: pd.DataFrame, xcol: str, ycol: str, gate) -> tuple[pd.DataFrame, Dict | None]:
    clean = _clean_nma_xy(pool, xcol, ycol)
    if clean.empty:
        raise HTTPException(
            status_code=400,
            detail="The control data has no valid numeric rows for the selected Area and NII columns. Choose numeric columns or upload a CSV with measured cells.",
        )
    if gate is None or not gate.enabled:
        return clean, None

    base_stats = _compute_stats(clean, xcol, ycol)
    sd_span = float(gate.sd or 2.0)
    if not np.isfinite(sd_span) or sd_span <= 0:
        sd_span = 2.0

    x_min = float(gate.x_min) if gate.x_min is not None else base_stats["mu_x"] - sd_span * base_stats["sd_x"]
    x_max = float(gate.x_max) if gate.x_max is not None else base_stats["mu_x"] + sd_span * base_stats["sd_x"]
    y_min = float(gate.y_min) if gate.y_min is not None else base_stats["mu_y"] - sd_span * base_stats["sd_y"]
    y_max = float(gate.y_max) if gate.y_max is not None else base_stats["mu_y"] + sd_span * base_stats["sd_y"]
    if x_min > x_max:
        x_min, x_max = x_max, x_min
    if y_min > y_max:
        y_min, y_max = y_max, y_min

    keep_mask = (
        clean[xcol].between(x_min, x_max, inclusive="both")
        & clean[ycol].between(y_min, y_max, inclusive="both")
    )
    gated = clean.loc[keep_mask].copy()
    total = int(len(clean))
    kept = int(len(gated))
    if gated.empty:
        raise HTTPException(
            status_code=400,
            detail=(
                "The control gate removed every cell. Widen the gate limits or increase the SD range so Step 1 has a normal control population to draw the ellipse."
            ),
        )

    max_preview = min(total, 4000)
    preview = clean.sample(n=max_preview, random_state=42) if total > max_preview else clean
    preview_mask = (
        preview[xcol].between(x_min, x_max, inclusive="both")
        & preview[ycol].between(y_min, y_max, inclusive="both")
    )
    meta = {
        "enabled": True,
        "sd": float(sd_span),
        "bounds": {
            "x_min": float(x_min),
            "x_max": float(x_max),
            "y_min": float(y_min),
            "y_max": float(y_max),
        },
        "total": total,
        "kept": kept,
        "removed": total - kept,
        "kept_percent": float((kept / total) * 100.0) if total else 0.0,
        "preview": {
            "x": preview[xcol].astype(float).tolist(),
            "y": preview[ycol].astype(float).tolist(),
            "keep": preview_mask.astype(bool).tolist(),
        },
    }
    return gated, meta


def _json_safe(value):
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, (pd.Series, pd.Index)):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
        return value if np.isfinite(value) else None
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


@app.post("/graphs/preview", response_model=GraphPreviewResponse)
def graphs_preview(req: GraphPreviewRequest):
    datasets = req.datasets or [{"path": p, "name": Path(p).stem} for p in (req.paths or [])]
    datasets = [d for d in datasets if str(d.get("path", "")).strip()]
    if not datasets:
        raise HTTPException(status_code=400, detail="Provide at least one CSV path.")
    dfs = []
    base_cols = None
    for ds in datasets:
        p = str(ds.get("path", "")).strip()
        ds_name = str(ds.get("name", "")).strip() or Path(p).stem
        pth = Path(p).expanduser().resolve()
        if not pth.exists() or not pth.is_file():
            raise HTTPException(status_code=400, detail=f"CSV not found: {p}")
        try:
            df = pd.read_csv(pth)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read CSV '{p}': {e}")
        if "Condition" not in df.columns:
            df["Condition"] = ds_name
        else:
            cond = df["Condition"].astype(str)
            empty = cond.isna() | (cond.str.strip() == "") | (cond.str.lower() == "nan")
            if empty.any():
                df.loc[empty, "Condition"] = ds_name
        cols = tuple(str(c) for c in df.columns)
        if base_cols is None:
            base_cols = cols
        elif cols != base_cols:
            raise HTTPException(
                status_code=400,
                detail="All CSVs must have exactly the same columns (same names and order).",
            )
        df["__source__"] = ds_name
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)

    gt = (req.graph_type or "scatter").lower()
    x, y, hue, size = req.x, req.y, req.hue, req.size
    plot_overtime = bool(req.plot_overtime)
    if x and x not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{x}' was not found in CSV columns.")

    needs_xy = {"scatter"}
    needs_y = {"violin", "box", "dot", "bar", "line", "rolling-average"}
    if gt in needs_xy and (not x or not y):
        raise HTTPException(status_code=400, detail=f"{gt.title()} requires X and Y.")
    if gt in needs_y and not y:
        raise HTTPException(status_code=400, detail=f"{gt.title()} requires Y.")

    if req.conditions and "Condition" in df.columns:
        df = df[df["Condition"].isin(req.conditions)]
    if req.frames and "Frame" in df.columns:
        df = df[df["Frame"].isin(req.frames)]
    if df.empty:
        raise HTTPException(status_code=400, detail="No data left after filters.")

    def _category_x_col() -> str:
        if plot_overtime and "Frame" in df.columns:
            return "Frame"
        if "Condition" in df.columns:
            return "Condition"
        return "__source__"

    def _dynamic_width_for_categories(col_name: str | None) -> int | None:
        if not col_name or col_name not in df.columns:
            return None
        ncat = int(df[col_name].nunique(dropna=True))
        if ncat <= 0:
            return None
        # Grow width with category count, but keep bounded to viewport-friendly sizes.
        return max(700, min(1700, 220 + 75 * ncat))

    try:
        dynamic_width = None
        auc_summary = ""
        auc_lines: list[str] = []
        if gt == "scatter":
            fig = px.scatter(df, x=x, y=y, color=hue, size=size, hover_data=["__source__"] if "__source__" in df.columns else None)
        elif gt == "violin":
            x_col = req.x if req.x and req.x in df.columns else None
            dynamic_width = _dynamic_width_for_categories(x_col)
            fig = px.violin(
                df,
                x=x_col,
                y=y,
                color=hue,
                box=bool(req.violin_box),
                points="all" if req.violin_points else False,
            )
        elif gt == "box":
            x_col = req.x if req.x and req.x in df.columns else None
            dynamic_width = _dynamic_width_for_categories(x_col)
            box_points = "all" if req.dot else ("outliers" if req.box_outliers else False)
            fig = px.box(df, x=x_col, y=y, color=hue, points=box_points)
        elif gt == "dot":
            x_col = req.x if req.x and req.x in df.columns else None
            dynamic_width = _dynamic_width_for_categories(x_col)
            if size and size in df.columns:
                dot_df = df.copy()
                if not x_col:
                    dot_df["__dot_x__"] = "All"
                    x_col = "__dot_x__"
                fig = px.scatter(dot_df, x=x_col, y=y, color=hue, size=size)
            else:
                fig = px.strip(df, x=x_col, y=y, color=hue)
        elif gt == "bar":
            x_col = req.x if req.x and req.x in df.columns else None
            if not pd.api.types.is_numeric_dtype(df[y]):
                raise HTTPException(status_code=400, detail="Bar plot requires a numeric Y column.")
            if x_col:
                group_cols = [x_col] + ([hue] if hue else [])
                agg = df.groupby(group_cols, dropna=False)[y].mean().reset_index()
                dynamic_width = _dynamic_width_for_categories(x_col)
                fig = px.bar(agg, x=x_col, y=y, color=hue)
            elif hue and hue in df.columns:
                agg = df.groupby([hue], dropna=False)[y].mean().reset_index()
                dynamic_width = _dynamic_width_for_categories(hue)
                fig = px.bar(agg, x=hue, y=y, color=hue)
            else:
                agg = pd.DataFrame({"__bar_x__": ["All"], y: [float(df[y].mean())]})
                dynamic_width = 700
                fig = px.bar(agg, x="__bar_x__", y=y)
        elif gt == "line":
            x_col = req.x if req.x and req.x in df.columns else "Frame"
            if x_col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Line plot requires '{x_col}' column.")
            group_cols = [x_col] + ([hue] if hue else [])
            agg = df.groupby(group_cols, dropna=False)[y].mean().reset_index().sort_values([x_col])
            dynamic_width = _dynamic_width_for_categories(x_col)
            fig = px.line(agg, x=x_col, y=y, color=hue)
            if req.compute_auc:
                x_num = pd.to_numeric(agg[x_col], errors="coerce")
                if x_num.isna().any():
                    raise HTTPException(status_code=400, detail="AUC requires a numeric X axis.")
                tmp = agg.assign(__x_num__=x_num)
                key_col = hue if hue else "__all__"
                if key_col == "__all__":
                    tmp[key_col] = "all"
                for g, gdf in tmp.groupby(key_col, dropna=False):
                    auc_val = float(np.trapz(gdf[y].to_numpy(), gdf["__x_num__"].to_numpy()))
                    auc_lines.append(f"{g}: {auc_val:.3f}")
                auc_summary = " | AUC: " + "; ".join(auc_lines)
        elif gt == "rolling-average":
            if "Frame" not in df.columns:
                raise HTTPException(status_code=400, detail="Rolling average requires 'Frame' column.")
            window = int(req.n or 5)
            key = hue if hue and hue in df.columns else ("Condition" if "Condition" in df.columns else "__source__")
            agg = df.groupby([key, "Frame"], dropna=False)[y].mean().reset_index().sort_values(["Frame"])
            agg["rolling"] = agg.groupby(key)[y].transform(lambda s: s.rolling(window=window, min_periods=1).mean())
            dynamic_width = _dynamic_width_for_categories("Frame")
            fig = px.line(agg, x="Frame", y="rolling", color=key)
            if req.compute_auc:
                for g, gdf in agg.groupby(key, dropna=False):
                    auc_val = float(np.trapz(gdf["rolling"].to_numpy(), gdf["Frame"].to_numpy()))
                    auc_lines.append(f"{g}: {auc_val:.3f}")
                auc_summary = " | AUC (rolling): " + "; ".join(auc_lines)
        elif gt == "cpd":
            if "Frame" not in df.columns:
                raise HTTPException(status_code=400, detail="CPD requires 'Frame' column.")
            if "Condition" not in df.columns:
                raise HTTPException(status_code=400, detail="CPD requires 'Condition' column.")
            frames = [int(f) for f in req.frames] if req.frames else []
            if len(frames) < 2:
                raise HTTPException(status_code=400, detail="CPD requires at least 2 frames.")
            frames = sorted(dict.fromkeys(frames))
            df_cpd = df[df["Frame"].isin(frames)].copy()
            if df_cpd.empty:
                raise HTTPException(status_code=400, detail="No rows for selected frames.")
            conds = sorted(df_cpd["Condition"].dropna().astype(str).unique().tolist())
            if req.control and req.control in conds:
                conds.remove(req.control)
                conds.insert(0, req.control)
            out = []
            skipped = []
            for c in conds:
                sub = df_cpd[df_cpd["Condition"].astype(str) == c]
                counts = sub["Frame"].value_counts().reindex(frames, fill_value=0).astype(float).to_numpy()
                cpd_vals = [0.0]
                acc = 0.0
                for i in range(len(counts) - 1):
                    n0, n1 = counts[i], counts[i + 1]
                    if n0 <= 0 or n1 <= 0:
                        skipped.append(f"{c}[{frames[i]}->{frames[i + 1]}]")
                        cpd_vals.append(acc)
                        continue
                    acc += float(np.log2(n1 / n0))
                    cpd_vals.append(acc)
                out.extend({"Condition": c, "Frame": fr, "CPD": val} for fr, val in zip(frames, cpd_vals))
            cpd_df = pd.DataFrame(out)
            dynamic_width = _dynamic_width_for_categories("Frame")
            fig = px.line(cpd_df, x="Frame", y="CPD", color="Condition", markers=True)
            if skipped:
                auc_summary = " | CPD warnings: skipped intervals with zero counts: " + ", ".join(skipped[:8]) + ("..." if len(skipped) > 8 else "")
        else:
            raise HTTPException(status_code=400, detail=f"Graph type '{gt}' not implemented yet for interactive preview.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    fig.update_layout(margin=dict(l=50, r=20, t=50, b=50), template="plotly_white")
    if dynamic_width:
        fig.update_layout(width=dynamic_width)
    if auc_lines:
        fig.update_layout(margin=dict(l=50, r=20, t=110, b=50))
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.01,
            y=1.18,
            showarrow=False,
            align="left",
            text="AUC: " + " | ".join(auc_lines),
            font=dict(size=12, color="#0c1b2a"),
            bgcolor="rgba(245,248,251,0.92)",
            bordercolor="#dde6ef",
            borderwidth=1,
        )
    return GraphPreviewResponse(
        figure=json.loads(fig.to_json()),
        columns=[str(c) for c in df.columns if c != "__source__" and _is_display_column(c)],
        message=f"Preview generated for {len(df)} rows.{auc_summary}",
    )


@app.post("/graphs/conditions", response_model=GraphConditionsResponse)
def graphs_conditions(req: GraphConditionsRequest):
    datasets = req.datasets or [{"path": p, "name": Path(p).stem} for p in (req.paths or [])]
    datasets = [d for d in datasets if str(d.get("path", "")).strip()]
    if not datasets:
        return GraphConditionsResponse(conditions=[])

    out: list[str] = []
    seen: set[str] = set()
    for ds in datasets:
        p = str(ds.get("path", "")).strip()
        ds_name = str(ds.get("name", "")).strip() or Path(p).stem
        pth = Path(p).expanduser().resolve()
        if not pth.exists() or not pth.is_file():
            raise HTTPException(status_code=400, detail=f"CSV not found: {p}")

        conds: list[str] = []
        try:
            dfc = pd.read_csv(pth, usecols=["Condition"])
            vals = (
                dfc["Condition"]
                .dropna()
                .astype(str)
                .map(lambda s: s.strip())
                .tolist()
            )
            conds = [v for v in vals if v and v.lower() != "nan"]
        except Exception:
            conds = []

        if not conds:
            conds = [ds_name]

        for c in conds:
            if c not in seen:
                seen.add(c)
                out.append(c)

    return GraphConditionsResponse(conditions=out)


def _normalize_gate_datasets(datasets: list[dict] | None, paths: list[str] | None) -> list[dict]:
    raw = datasets or [{"path": p, "name": Path(p).stem} for p in (paths or [])]
    cleaned = []
    for ds in raw:
        if hasattr(ds, "model_dump"):
            ds = ds.model_dump()
        p = str(ds.get("path", "")).strip()
        if not p:
            continue
        name = str(ds.get("name", "")).strip() or Path(p).stem
        pkl_dir = str(ds.get("pkl_dir", "")).strip() or None
        cleaned.append({"path": p, "name": name, "pkl_dir": pkl_dir})
    return cleaned


def _load_gate_dataframe(req: GatingPreviewRequest):
    datasets = _normalize_gate_datasets(req.datasets, req.paths)
    if not datasets:
        raise HTTPException(status_code=400, detail="Provide at least one CSV path.")

    frames = []
    for ds in datasets:
        pth = Path(ds["path"]).expanduser().resolve()
        if not pth.exists() or not pth.is_file():
            raise HTTPException(status_code=400, detail=f"CSV not found: {ds['path']}")
        try:
            df = pd.read_csv(pth)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read CSV '{ds['path']}': {e}")
        if req.x_col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{req.x_col}' was not found in {pth.name}.")
        if req.y_col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{req.y_col}' was not found in {pth.name}.")
        if not pd.api.types.is_numeric_dtype(df[req.x_col]):
            raise HTTPException(status_code=400, detail=f"Column '{req.x_col}' must be numeric.")
        if not pd.api.types.is_numeric_dtype(df[req.y_col]):
            raise HTTPException(status_code=400, detail=f"Column '{req.y_col}' must be numeric.")

        tmp = df.copy()
        tmp["__source__"] = ds["name"]
        tmp["__source_path__"] = str(pth)
        frames.append(tmp)

    df_all = pd.concat(frames, ignore_index=True)
    valid = ~(df_all[req.x_col].isna() | df_all[req.y_col].isna())
    df_all = df_all.loc[valid].copy()
    if df_all.empty:
        raise HTTPException(status_code=400, detail="No valid rows after removing NaN in gating columns.")
    return df_all


def _resolve_gate_bounds(req: GatingPreviewRequest, df: pd.DataFrame) -> tuple[float, float, float, float]:
    q_low = float(req.q_low if req.q_low is not None else 0.05)
    q_high = float(req.q_high if req.q_high is not None else 0.95)
    q_low = max(0.0, min(0.49, q_low))
    q_high = max(0.51, min(1.0, q_high))
    if q_low >= q_high:
        raise HTTPException(status_code=400, detail="q_low must be lower than q_high.")

    x_min = float(req.x_min) if req.x_min is not None else float(df[req.x_col].quantile(q_low))
    x_max = float(req.x_max) if req.x_max is not None else float(df[req.x_col].quantile(q_high))
    y_min = float(req.y_min) if req.y_min is not None else float(df[req.y_col].quantile(q_low))
    y_max = float(req.y_max) if req.y_max is not None else float(df[req.y_col].quantile(q_high))
    if x_min >= x_max:
        raise HTTPException(status_code=400, detail="Invalid X bounds: x_min must be lower than x_max.")
    if y_min >= y_max:
        raise HTTPException(status_code=400, detail="Invalid Y bounds: y_min must be lower than y_max.")
    return x_min, x_max, y_min, y_max


def _apply_gate(df: pd.DataFrame, x_col: str, y_col: str, x_min: float, x_max: float, y_min: float, y_max: float) -> pd.Series:
    # Mirrors the legacy filter behavior (strict interval on both axes).
    return (df[x_col] > x_min) & (df[x_col] < x_max) & (df[y_col] > y_min) & (df[y_col] < y_max)


def _redraw_gated_images(kept: pd.DataFrame, datasets: list[dict], out_dir: Path) -> list[str]:
    files: list[str] = []
    dataset_by_source = {
        str(Path(ds["path"]).expanduser().resolve()): ds
        for ds in datasets
    }

    missing = []
    for ds in datasets:
        pkl_dir = str(ds.get("pkl_dir") or "").strip()
        if not pkl_dir:
            missing.append(ds["name"])
            continue
        pkl_path = Path(pkl_dir).expanduser().resolve()
        if not pkl_path.exists() or not pkl_path.is_dir():
            raise HTTPException(status_code=400, detail=f"PKL folder not found for dataset '{ds['name']}': {pkl_dir}")
    if missing:
        raise HTTPException(
            status_code=400,
            detail="PKL folder is required for every dataset when 'Apply gate to images' is enabled: "
                   + ", ".join(sorted(missing)),
        )

    for source_path, part in kept.groupby("__source_path__", sort=True):
        ds = dataset_by_source.get(str(source_path))
        if not ds:
            continue

        pkl_dir = Path(str(ds["pkl_dir"])).expanduser().resolve()
        pkl_files = sorted([p for p in pkl_dir.iterdir() if p.suffix.lower() == ".pkl"])
        if not pkl_files:
            raise HTTPException(status_code=400, detail=f"No .pkl files found in {pkl_dir}")

        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(ds["name"])).strip("_") or "dataset"
        redraw_root = (out_dir / f"{safe_name}_gated_images").resolve()
        filtered_pkl_dir = redraw_root / "pkl-data-filtered"
        filtered_pkl_dir.mkdir(parents=True, exist_ok=True)

        channel_names = [str(c).replace("Image_name_", "") for c in part.columns if str(c).startswith("Image_name_")]
        channel_names = list(dict.fromkeys(channel_names))
        files.append(str(redraw_root))
        files.append(str(filtered_pkl_dir))

        for pkl_file in pkl_files:
            try:
                df_draw = pd.read_pickle(pkl_file)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read pickle '{pkl_file.name}': {e}")

            if df_draw is None or len(df_draw) == 0 or "Frame" not in df_draw.columns or "Cell" not in df_draw.columns:
                continue

            frame_rows = part.loc[part["Frame"] == df_draw["Frame"].iloc[0]]
            if frame_rows.empty:
                continue

            cells_to_keep = set(frame_rows["Cell"].tolist())
            df_filtered = df_draw[df_draw["Cell"].isin(cells_to_keep)].copy()
            if df_filtered.empty:
                continue

            df_filtered.to_pickle(filtered_pkl_dir / pkl_file.name)
            use_cellpose = bool(df_draw["use_cellpose"].iloc[0]) if "use_cellpose" in df_draw.columns else False
            saving_images(df_filtered, str(redraw_root), channel_names, use_cellpose)

    return list(dict.fromkeys(files))


def _percentile_rank(series: pd.Series, value: float) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float((values <= value).mean() * 100.0)


def _gate_summary_row(
        df: pd.DataFrame,
        dataset: str,
        condition: str,
        req: GatingPreviewRequest,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
) -> dict:
    total = int(df["__gate_keep__"].shape[0])
    kept = int(df["__gate_keep__"].sum())
    removed = total - kept
    return {
        "dataset": dataset,
        "condition": condition,
        "total": total,
        "kept": kept,
        "removed": removed,
        "kept_pct": (kept * 100.0 / total) if total > 0 else 0.0,
        "removed_pct": (removed * 100.0 / total) if total > 0 else 0.0,
        f"{req.x_col}_min": x_min,
        f"{req.x_col}_min_percentile": _percentile_rank(df[req.x_col], x_min),
        f"{req.x_col}_max": x_max,
        f"{req.x_col}_max_percentile": _percentile_rank(df[req.x_col], x_max),
        f"{req.y_col}_min": y_min,
        f"{req.y_col}_min_percentile": _percentile_rank(df[req.y_col], y_min),
        f"{req.y_col}_max": y_max,
        f"{req.y_col}_max_percentile": _percentile_rank(df[req.y_col], y_max),
    }


def _gate_summary_table(
        df: pd.DataFrame,
        req: GatingPreviewRequest,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
) -> StatsTable:
    df_summary = df.copy()
    if "Condition" in df_summary.columns:
        df_summary["__gate_condition__"] = (
            df_summary["Condition"]
            .fillna("Unknown")
            .astype(str)
            .map(lambda value: value.strip() or "Unknown")
        )
    else:
        df_summary["__gate_condition__"] = "All conditions"

    rows = []
    for (dataset, condition), part in df_summary.groupby(["__source__", "__gate_condition__"], sort=False):
        rows.append(_gate_summary_row(part, str(dataset), str(condition), req, x_min, x_max, y_min, y_max))

    rows.append(_gate_summary_row(df_summary, "All datasets", "All conditions", req, x_min, x_max, y_min, y_max))
    full = pd.DataFrame(rows)
    rows = json.loads(full.to_json(orient="records"))
    return StatsTable(name="gating_summary", columns=[str(c) for c in full.columns], rows=rows)


def _gate_preview_figure(df: pd.DataFrame, req: GatingPreviewRequest, x_min: float, x_max: float, y_min: float, y_max: float) -> dict:
    max_points = max(1000, int(req.max_points or 12000))
    df_plot = df.sample(n=max_points, random_state=42) if len(df) > max_points else df
    df_plot = df_plot.copy()
    palette = list(qual_colors.Safe) or list(qual_colors.Plotly)
    fig = go.Figure()
    sources = [str(s) for s in pd.Series(df_plot["__source__"]).dropna().astype(str).unique()]
    for idx, source in enumerate(sources):
        color = palette[idx % len(palette)]
        source_df = df_plot[df_plot["__source__"].astype(str) == source]
        kept_df = source_df[source_df["__gate_keep__"]]
        removed_df = source_df[~source_df["__gate_keep__"]]
        if not kept_df.empty:
            fig.add_trace(go.Scattergl(
                x=kept_df[req.x_col],
                y=kept_df[req.y_col],
                mode="markers",
                name=f"{source} kept",
                legendgroup=source,
                marker=dict(color=color, size=6, opacity=0.78, symbol="circle"),
                customdata=np.stack([kept_df["__source__"].astype(str), np.full(len(kept_df), "kept")], axis=-1),
                hovertemplate=f"{req.x_col}: %{{x}}<br>{req.y_col}: %{{y}}<br>Dataset: %{{customdata[0]}}<br>Status: %{{customdata[1]}}<extra></extra>",
            ))
        if not removed_df.empty:
            fig.add_trace(go.Scattergl(
                x=removed_df[req.x_col],
                y=removed_df[req.y_col],
                mode="markers",
                name=f"{source} removed",
                legendgroup=source,
                showlegend=False,
                marker=dict(color=color, size=6, opacity=0.78, symbol="circle-open"),
                customdata=np.stack([removed_df["__source__"].astype(str), np.full(len(removed_df), "removed")], axis=-1),
                hovertemplate=f"{req.x_col}: %{{x}}<br>{req.y_col}: %{{y}}<br>Dataset: %{{customdata[0]}}<br>Status: %{{customdata[1]}}<extra></extra>",
            ))
    if not sources:
        fig.add_trace(go.Scattergl(
            x=df_plot[req.x_col],
            y=df_plot[req.y_col],
            mode="markers",
            name="Dataset",
            marker=dict(color="#3a6ea5", size=6, opacity=0.72),
            hovertemplate=f"{req.x_col}: %{{x}}<br>{req.y_col}: %{{y}}<extra></extra>",
        ))
    fig.add_shape(type="rect", x0=x_min, x1=x_max, y0=y_min, y1=y_max, line=dict(color="#0f5b96", width=2), fillcolor="rgba(15,91,150,0.08)")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=65, r=35, t=45, b=60),
        autosize=True,
        legend_title_text="Dataset",
        dragmode=False,
    )
    fig.update_xaxes(title_text=req.x_col, fixedrange=True)
    fig.update_yaxes(title_text=req.y_col, fixedrange=True)
    return json.loads(fig.to_json())


@app.post("/filters/preview", response_model=GatingPreviewResponse)
def filters_preview(req: GatingPreviewRequest):
    df = _load_gate_dataframe(req)
    x_min, x_max, y_min, y_max = _resolve_gate_bounds(req, df)
    df["__gate_keep__"] = _apply_gate(df, req.x_col, req.y_col, x_min, x_max, y_min, y_max)
    summary = _gate_summary_table(df, req, x_min, x_max, y_min, y_max)
    total = int(df["__gate_keep__"].shape[0])
    kept = int(df["__gate_keep__"].sum())
    return GatingPreviewResponse(
        figure=_gate_preview_figure(df, req, x_min, x_max, y_min, y_max),
        bounds=GatingBounds(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max),
        tables=[summary],
        message=f"Gating preview ready. Kept {kept}/{total} rows ({(kept * 100.0 / total):.1f}%).",
    )


@app.post("/filters/apply", response_model=GatingApplyResponse)
def filters_apply(req: GatingApplyRequest):
    out_dir = Path(req.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    datasets = _normalize_gate_datasets(req.datasets, req.paths)

    df = _load_gate_dataframe(req)
    x_min, x_max, y_min, y_max = _resolve_gate_bounds(req, df)
    df["__gate_keep__"] = _apply_gate(df, req.x_col, req.y_col, x_min, x_max, y_min, y_max)
    summary = _gate_summary_table(df, req, x_min, x_max, y_min, y_max)

    files = []
    kept = df.loc[df["__gate_keep__"]].copy()
    combined = kept.drop(columns=["__gate_keep__", "__source_path__"], errors="ignore")
    combined_path = (out_dir / "Gated results.csv").resolve()
    combined.to_csv(combined_path, index=False)
    files.append(str(combined_path))

    for src, part in kept.groupby("__source__", sort=True):
        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(src)).strip("_") or "dataset"
        p = (out_dir / f"{safe_name}_gated_results.csv").resolve()
        part.drop(columns=["__gate_keep__", "__source_path__"], errors="ignore").to_csv(p, index=False)
        files.append(str(p))

    if req.draw_images:
        files.extend(_redraw_gated_images(kept, datasets, out_dir))

    dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log = (
        f"\n\n{dt} - Gating filter applied:\n"
        f"{req.x_col} minimum: {x_min}\n"
        f"{req.x_col} maximum: {x_max}\n"
        f"{req.y_col} minimum: {y_min}\n"
        f"{req.y_col} maximum: {y_max}\n"
        f"Apply gate to images: {'yes' if req.draw_images else 'no'}\n"
    )
    with open(out_dir / "logs-fornma.txt", "a", encoding="utf-8") as logs:
        logs.write(log)

    total = int(df["__gate_keep__"].shape[0])
    kept_n = int(df["__gate_keep__"].sum())
    return GatingApplyResponse(
        bounds=GatingBounds(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max),
        tables=[summary],
        output_dir=str(out_dir),
        files=files,
        message=(
            f"Gating applied. Saved {len(files)} output item(s). "
            f"Kept {kept_n}/{total} rows ({(kept_n * 100.0 / total):.1f}%)."
        ),
    )


def _tracking_image_col(df: pd.DataFrame, override: str | None = None) -> str:
    cols = [str(c) for c in df.columns]
    if override:
        ov = str(override)
        if ov in cols:
            return ov
        ov_norm = ov.strip().casefold()
        for c in cols:
            if str(c).strip().casefold() == ov_norm:
                return c
    img_cols = [c for c in cols if "image_name" in str(c).strip().casefold()]
    if not img_cols:
        raise HTTPException(status_code=400, detail="Tracking table is missing image column (e.g., Image_name_*).")
    return img_cols[0]


def _tracking_basename(raw: str) -> str:
    return str(raw or "").strip().replace("\\", "/").split("/")[-1]


def _tracking_validate_image_mapping(df: pd.DataFrame, image_col: str, image_dir: str) -> None:
    if image_col not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Image column '{image_col}' was not found in the CSV table.",
        )

    img_dir = Path(image_dir).expanduser().resolve()
    if not img_dir.exists() or not img_dir.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Image folder not found or invalid: {image_dir}",
        )

    image_names = {
        p.name for p in img_dir.rglob("*")
        if p.is_file()
    }
    if not image_names:
        raise HTTPException(
            status_code=400,
            detail=f"No image files found in folder: {img_dir}",
        )

    raw_values = df[image_col].dropna().astype(str).map(str.strip)
    csv_names = sorted({_tracking_basename(v) for v in raw_values.tolist() if v})
    if not csv_names:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Column '{image_col}' is empty. It must contain image file names that match files in '{img_dir}'."
            ),
        )

    missing = [name for name in csv_names if name not in image_names]
    if missing:
        preview = ", ".join(missing[:5])
        suffix = "" if len(missing) <= 5 else f" ... (+{len(missing) - 5} more)"
        raise HTTPException(
            status_code=400,
            detail=(
                f"Image name mismatch: column '{image_col}' must match file names in '{img_dir}'. "
                f"Missing example(s): {preview}{suffix}"
            ),
        )


def _tracking_color_for_family(family) -> tuple[int, int, int]:
    seed = hash(str(family)) & 0xFFFFFFFF
    rng = np.random.default_rng(seed)
    # keep away from too-dark colors for readability
    rgb = rng.integers(50, 240, size=3).tolist()
    return int(rgb[0]), int(rgb[1]), int(rgb[2])


def _tracking_ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    needed = {"Frame", "Cell", "X", "Y", "track_id"}
    miss = needed - set(df.columns)
    if miss:
        raise HTTPException(status_code=400, detail=f"Tracking table missing required columns: {sorted(miss)}")

    out = df.copy()
    out["Frame"] = pd.to_numeric(out["Frame"], errors="coerce")
    out["Cell"] = pd.to_numeric(out["Cell"], errors="coerce")
    out["X"] = pd.to_numeric(out["X"], errors="coerce")
    out["Y"] = pd.to_numeric(out["Y"], errors="coerce")
    out["track_id"] = pd.to_numeric(out["track_id"], errors="coerce")
    out = out.dropna(subset=["Frame", "Cell", "X", "Y", "track_id"]).copy()
    out["Frame"] = out["Frame"].astype(int)
    out["Cell"] = out["Cell"].astype(int)
    out["track_id"] = out["track_id"].astype(int)

    if "family" not in out.columns:
        out["family"] = out["track_id"]
    if "family_name" not in out.columns:
        out["family_name"] = out["family"].astype(str) + "."
    if "previous_x" not in out.columns:
        out["previous_x"] = np.nan
    if "previous_y" not in out.columns:
        out["previous_y"] = np.nan
    if "family_color" not in out.columns:
        out["family_color"] = out["family"].map(lambda f: str(_tracking_color_for_family(f)))
    else:
        out["family_color"] = out["family_color"].fillna(out["family"].map(lambda f: str(_tracking_color_for_family(f))))
    return out


def _tracking_df_load(path: str) -> pd.DataFrame:
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=400, detail=f"Tracking table not found: {path}")
    try:
        df = pd.read_csv(p)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read tracking table: {e}")
    return _tracking_ensure_columns(df)


def _tracking_df_save(path: str, df: pd.DataFrame) -> None:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    save_df = df.copy()
    save_df["family_color"] = save_df["family_color"].astype(str)
    save_df.to_csv(p, index=False)


def _tracking_checkpoint_copy(table_path: str, label: str = "checkpoint") -> str:
    src = Path(table_path).expanduser().resolve()
    if not src.exists() or not src.is_file():
        raise HTTPException(status_code=400, detail=f"Tracked table not found: {table_path}")
    ckpt_dir = (Path(tempfile.gettempdir()) / "fornma_tracking_checkpoints").resolve()
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    dst = ckpt_dir / f"{src.stem}_{label}_{stamp}.csv"
    shutil.copy2(src, dst)
    return str(dst)


def _tracking_resolve_image_path(row: pd.Series, image_col: str, image_dir: str | None) -> Path | None:
    raw = str(row.get(image_col, "") or "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser()
    if p.is_absolute() and p.exists() and p.is_file():
        return p.resolve()
    if image_dir:
        pp = (Path(image_dir).expanduser().resolve() / raw)
        if pp.exists() and pp.is_file():
            return pp.resolve()
    # fallback relative to cwd
    pp = Path(raw).resolve()
    if pp.exists() and pp.is_file():
        return pp
    return None


def _tracking_draw_preview_image(
    df: pd.DataFrame,
    frame: int,
    image_col: str,
    image_dir: str | None,
    trail_window: int,
    show_complete_trail: bool,
    preview_cache_dir: str | None = None,
    force_redraw: bool = False,
):
    try:
        import cv2 as cv
    except Exception:
        return None, None

    if not image_dir:
        return None, None

    if preview_cache_dir:
        cache_dir = Path(preview_cache_dir).expanduser().resolve()
    else:
        cache_root = Path(tempfile.gettempdir()) / "fornma_tracking_preview"
        cache_root.mkdir(parents=True, exist_ok=True)
        key_raw = "||".join(
            [
                str(Path(image_dir).expanduser().resolve()),
                str(image_col),
                str(max(1, int(trail_window))),
                "complete" if show_complete_trail else "window",
                str(int(df["Frame"].min())),
                str(int(df["Frame"].max())),
                str(int(len(df))),
                str(int(df["track_id"].nunique())),
                str(
                    int(
                        pd.util.hash_pandas_object(
                            df[
                                [c for c in ["Frame", "Cell", "X", "Y", "track_id", "previous_x", "previous_y", "family", "family_name"] if c in df.columns]
                            ],
                            index=False,
                        ).sum()
                    )
                ),
            ]
        )
        cache_key = hashlib.sha1(key_raw.encode("utf-8")).hexdigest()[:16]
        cache_dir = cache_root / cache_key

    # Pre-render all tracked frames once into temp cache to keep frame navigation fast.
    if force_redraw and cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)
    if not cache_dir.exists() or not any(cache_dir.glob("*.tiff")):
        cache_dir.mkdir(parents=True, exist_ok=True)
        draw_tracking_frames(
            df=df.copy(),
            folder=str(Path(image_dir).expanduser().resolve()),
            save=str(cache_dir),
            img_col=image_col,
            trail_window=max(1, int(trail_window)),
        )

    # Build PNG mirrors once so browser viewer behaves consistently across environments.
    png_exists = any(cache_dir.glob("*.png"))
    if not png_exists:
        for tif in cache_dir.glob("*.tif*"):
            try:
                import cv2 as cv
                im = imread(tif, cv.IMREAD_UNCHANGED)
                if im is None:
                    continue
                out_png = tif.with_suffix(".png")
                imwrite(out_png, im)
            except Exception:
                continue

    frame_path = cache_dir / f"{int(frame):05d}.png"
    if not frame_path.exists():
        frame_path = cache_dir / f"{int(frame):05d}.tiff"
    if not frame_path.exists():
        return None, str(cache_dir)
    img = imread(frame_path)
    if img is None:
        return None, str(cache_dir)
    return cv.cvtColor(img, cv.COLOR_BGR2RGB), str(cache_dir)


def _tracking_preview_figure(
    df: pd.DataFrame,
    frame: int,
    image_col: str,
    image_dir: str | None,
    preview_cache_dir: str | None,
    trail_window: int,
    show_complete_trail: bool,
    force_redraw: bool = False,
) -> tuple[dict, str | None]:
    frame = int(frame)
    fr_min = int(df["Frame"].min())
    fr_max = int(df["Frame"].max())
    frame = max(fr_min, min(fr_max, frame))
    df_frame = df[df["Frame"] == frame].copy()

    fig = go.Figure()
    rendered, preview_cache_dir = _tracking_draw_preview_image(
        df=df,
        frame=frame,
        image_col=image_col,
        image_dir=image_dir,
        preview_cache_dir=preview_cache_dir,
        trail_window=trail_window,
        show_complete_trail=show_complete_trail,
        force_redraw=force_redraw,
    )
    if rendered is not None:
        fig.add_trace(go.Image(z=rendered))

    if not df_frame.empty:
        fig.add_trace(
            go.Scatter(
                x=df_frame["X"].astype(float),
                y=df_frame["Y"].astype(float),
                mode="markers",
                marker=dict(size=16, color="rgba(0,0,0,0.01)", line=dict(width=0)),
                customdata=np.stack(
                    [df_frame["Frame"].to_numpy(), df_frame["Cell"].to_numpy(), df_frame["track_id"].to_numpy()],
                    axis=1,
                ),
                hovertemplate="Frame=%{customdata[0]} Cell=%{customdata[1]} Track=%{customdata[2]}<extra></extra>",
                name="cells-hitbox",
                showlegend=False,
            )
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=35, b=20),
        title=f"Tracking preview - frame {frame}",
        dragmode="pan",
        showlegend=False,
    )
    fig.update_yaxes(autorange="reversed")
    return json.loads(fig.to_json()), preview_cache_dir


def _tracking_preview_response(
    table_path: str,
    frame: int,
    image_dir: str | None,
    image_col: str | None,
    trail_window: int,
    show_complete_trail: bool,
    message: str = "",
    preview_cache_dir: str | None = None,
    force_redraw: bool = False,
):
    df = _tracking_df_load(table_path)
    img_col = _tracking_image_col(df, image_col)
    fr_min = int(df["Frame"].min())
    fr_max = int(df["Frame"].max())
    frame = max(fr_min, min(fr_max, int(frame)))
    fig, cache_dir = _tracking_preview_figure(
        df,
        frame,
        img_col,
        image_dir,
        preview_cache_dir,
        trail_window,
        show_complete_trail,
        force_redraw,
    )
    preview_image_path = None
    if cache_dir:
        base = Path(cache_dir).expanduser().resolve()
        candidate = base / f"{int(frame):05d}.png"
        if not candidate.exists() or not candidate.is_file():
            candidate = base / f"{int(frame):05d}.tiff"
        if candidate.exists() and candidate.is_file():
            preview_image_path = str(candidate)

    return TrackingPreviewResponse(
        table_path=str(Path(table_path).expanduser().resolve()),
        image_col=img_col,
        preview_cache_dir=preview_cache_dir or cache_dir,
        preview_image_path=preview_image_path,
        frame=frame,
        max_frame=fr_max,
        total_rows=int(len(df)),
        total_tracks=int(df["track_id"].nunique()),
        figure=fig,
        message=message or f"Loaded frame {frame}.",
    )


def _tracking_find_rows_by_selection(df: pd.DataFrame, selections: list) -> pd.DataFrame:
    picked = []
    for idx, s in enumerate(selections):
        frame = int(s.frame)
        cell = int(s.cell)
        track_id = int(s.track_id)
        hit = df[(df["Frame"] == frame) & (df["Cell"] == cell) & (df["track_id"] == track_id)]
        if not hit.empty:
            row = hit.iloc[0].copy()
            row["__selection_order"] = idx
            picked.append(row)
    if not picked:
        return pd.DataFrame(columns=df.columns)
    return pd.DataFrame(picked)


def _tracking_family_name_prefix(value) -> str:
    text = str(value or "").strip()
    return text if text else ""


def _tracking_replace_family_prefix(value, old_prefix: str, new_prefix: str) -> str:
    text = str(value or "").strip()
    if not text:
        return new_prefix
    if old_prefix and text.startswith(old_prefix):
        return f"{new_prefix}{text[len(old_prefix):]}"
    return new_prefix


def _tracking_link_sort_key(row: pd.Series) -> tuple[int, int]:
    return int(row["Frame"]), int(row.get("__selection_order", 0))


def _tracking_collect_descendant_indices(df: pd.DataFrame, start_index: int) -> set[int]:
    """Follow the previous_x/previous_y chain from one selected row to all reachable descendants."""
    if start_index not in df.index:
        return set()

    collected: set[int] = set()
    queue = [start_index]

    while queue:
        idx = queue.pop(0)
        if idx in collected:
            continue
        collected.add(idx)
        row = df.loc[idx]
        frame = int(row["Frame"])
        x = float(row["X"])
        y = float(row["Y"])
        children = df[
            (df["Frame"] > frame)
            & np.isclose(pd.to_numeric(df["previous_x"], errors="coerce"), x, equal_nan=False)
            & np.isclose(pd.to_numeric(df["previous_y"], errors="coerce"), y, equal_nan=False)
        ]
        for child_idx in children.index.tolist():
            if child_idx not in collected:
                queue.append(child_idx)

    return collected


def _tracking_pick_by_point(df: pd.DataFrame, frame: int, x: float, y: float, max_distance: float) -> pd.Series | None:
    frame_df = df[df["Frame"] == int(frame)].copy()
    if frame_df.empty:
        return None
    frame_df["__dist__"] = np.sqrt((frame_df["X"].astype(float) - float(x)) ** 2 + (frame_df["Y"].astype(float) - float(y)) ** 2)
    best = frame_df.sort_values("__dist__").iloc[0]
    if float(best["__dist__"]) > float(max_distance):
        return None
    return best


@app.post("/tracking/run", response_model=TrackingRunResponse)
def tracking_run(req: TrackingRunRequest):
    source_path = Path(req.path_to_table).expanduser().resolve()
    if not source_path.exists() or not source_path.is_file():
        raise HTTPException(status_code=400, detail=f"CSV not found: {req.path_to_table}")
    if req.output_dir and str(req.output_dir).strip():
        out_dir = Path(req.output_dir).expanduser().resolve()
    else:
        out_dir = (Path(tempfile.gettempdir()) / "fornma_tracking_runs" / uuid.uuid4().hex[:12]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    original_df = pd.read_csv(source_path)
    img_col = _tracking_image_col(original_df, req.image_col)
    _tracking_validate_image_mapping(original_df, img_col, req.image_dir)

    tracked_df = run_tracking_laptracker(
        str(source_path),
        image_col=img_col,
        max_distance=int(req.max_distance),
        time_window=int(req.time_window),
        max_split_distance=int(req.max_split_distance),
        max_gap_closing_distance=int(req.max_gap_closing_distance),
    )
    min_frame = int(tracked_df["Frame"].min())
    tracked_df = find_tracking_family(tracked_df, min_frame=min_frame, max_distance=int(req.max_distance))
    tracked_df = create_tracking_nomenclature(tracked_df, int(req.max_gap_closing_distance))

    if img_col not in tracked_df.columns:
        tcols = [str(c) for c in tracked_df.columns]
        tgt_norm = str(img_col).strip().casefold()
        alt = next((c for c in tcols if str(c).strip().casefold() == tgt_norm), None)
        if alt:
            tracked_df = tracked_df.rename(columns={alt: img_col})
    merged = tracked_df.merge(original_df, on=["Frame", "Cell", "X", "Y", img_col], how="left")
    merged = _tracking_ensure_columns(merged)
    # Warm up preview cache right after automatic run to avoid first-view delay.
    _, warmed_cache_dir = _tracking_draw_preview_image(
        df=merged,
        frame=int(merged["Frame"].min()),
        image_col=img_col,
        image_dir=req.image_dir,
        trail_window=7,
        show_complete_trail=False,
        preview_cache_dir=None,
    )
    table_path = out_dir / "Tracked Results.csv"
    _tracking_df_save(str(table_path), merged)

    preview = _tracking_preview_response(
        table_path=str(table_path),
        frame=min_frame,
        image_dir=req.image_dir,
        image_col=img_col,
        trail_window=7,
        show_complete_trail=False,
        preview_cache_dir=warmed_cache_dir,
        message=f"Automatic tracking complete. {merged['track_id'].nunique()} tracks found.",
    )
    return TrackingRunResponse(**preview.dict(), output_dir=str(out_dir))


@app.post("/tracking/save-results", response_model=TrackingSaveResponse)
def tracking_save_results(req: TrackingSaveRequest):
    src_table = Path(req.table_path).expanduser().resolve()
    if not src_table.exists() or not src_table.is_file():
        raise HTTPException(status_code=400, detail=f"Tracked table not found: {req.table_path}")

    out_dir = Path(req.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    dst_table = out_dir / "Tracked Results.csv"
    shutil.copy2(src_table, dst_table)

    saved_images = 0
    images_dir = None
    if req.preview_cache_dir:
        cache_dir = Path(req.preview_cache_dir).expanduser().resolve()
        if cache_dir.exists() and cache_dir.is_dir():
            files = sorted([p for p in cache_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".tif", ".tiff"}])
            if files:
                out_imgs = out_dir / "tracked_images"
                out_imgs.mkdir(parents=True, exist_ok=True)
                for p in files:
                    shutil.copy2(p, out_imgs / p.name)
                saved_images = len(files)
                images_dir = str(out_imgs)

    msg = f"Saved tracked table to '{dst_table}'."
    if saved_images:
        msg += f" Saved {saved_images} image(s) to '{images_dir}'."
    else:
        msg += " No cached tracking images were found to copy."

    return TrackingSaveResponse(
        output_dir=str(out_dir),
        table_path=str(dst_table),
        images_dir=images_dir,
        saved_images=saved_images,
        message=msg,
    )


@app.post("/tracking/checkpoint/create", response_model=TrackingCheckpointResponse)
def tracking_checkpoint_create(req: TrackingCheckpointRequest):
    checkpoint_path = _tracking_checkpoint_copy(req.table_path)
    return TrackingCheckpointResponse(
        checkpoint_path=checkpoint_path,
        message="Undo checkpoint created.",
    )


@app.post("/tracking/checkpoint/restore", response_model=TrackingPreviewResponse)
def tracking_checkpoint_restore(req: TrackingRestoreRequest):
    checkpoint = Path(req.checkpoint_path).expanduser().resolve()
    if not checkpoint.exists() or not checkpoint.is_file():
        raise HTTPException(status_code=400, detail=f"Checkpoint not found: {req.checkpoint_path}")
    target = Path(req.table_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(checkpoint, target)
    return _tracking_preview_response(
        table_path=str(target),
        frame=req.frame,
        image_dir=req.image_dir,
        image_col=req.image_col,
        trail_window=req.trail_window,
        show_complete_trail=bool(req.show_complete_trail),
        preview_cache_dir=None,
        message="Last action undone.",
        force_redraw=True,
    )


@app.post("/tracking/progress/save", response_model=TrackingProgressSaveResponse)
def tracking_progress_save(req: TrackingProgressSaveRequest):
    saved_table_path = _tracking_checkpoint_copy(req.table_path, label="progress")
    preview = _tracking_preview_response(
        table_path=saved_table_path,
        frame=req.frame,
        image_dir=req.image_dir,
        image_col=req.image_col,
        trail_window=req.trail_window,
        show_complete_trail=bool(req.show_complete_trail),
        preview_cache_dir=None,
        message="Progress saved. Continuing from saved checkpoint.",
        force_redraw=True,
    )
    return TrackingProgressSaveResponse(**preview.dict(), saved_table_path=saved_table_path)


@app.post("/tracking/preview", response_model=TrackingPreviewResponse)
def tracking_preview(req: TrackingFrameRequest):
    return _tracking_preview_response(
        table_path=req.table_path,
        frame=req.frame,
        image_dir=req.image_dir,
        image_col=req.image_col,
        trail_window=req.trail_window,
        show_complete_trail=bool(req.show_complete_trail),
        preview_cache_dir=req.preview_cache_dir,
        message="Tracking preview updated.",
    )


@app.post("/tracking/select-point", response_model=TrackingPointSelectResponse)
def tracking_select_point(req: TrackingPointSelectRequest):
    df = _tracking_df_load(req.table_path)
    hit = _tracking_pick_by_point(df, req.frame, req.x, req.y, req.max_distance)
    if hit is None:
        raise HTTPException(status_code=400, detail="No track found near clicked point in this frame.")
    return TrackingPointSelectResponse(
        selection=TrackingSelection(
            frame=int(hit["Frame"]),
            cell=int(hit["Cell"]),
            track_id=int(hit["track_id"]),
        ),
        x=float(hit["X"]),
        y=float(hit["Y"]),
        distance=float(np.sqrt((float(hit["X"]) - float(req.x)) ** 2 + (float(hit["Y"]) - float(req.y)) ** 2)),
        message="Track selected.",
    )


@app.post("/tracking/markers", response_model=TrackingMarkersResponse)
def tracking_markers(req: TrackingMarkersRequest):
    df = _tracking_df_load(req.table_path)
    frame = int(req.frame)
    out = []
    for s in req.selections or []:
        tid = int(s.track_id)
        row = df[(df["Frame"] == frame) & (df["track_id"] == tid)].sort_values(["Cell", "X", "Y"])
        if row.empty:
            continue
        r = row.iloc[0]
        out.append(
            TrackingMarker(
                frame=int(r["Frame"]),
                cell=int(r["Cell"]),
                track_id=int(r["track_id"]),
                x=float(r["X"]),
                y=float(r["Y"]),
            )
        )
    return TrackingMarkersResponse(markers=out, message="Markers loaded.")


@app.post("/tracking/edit/delete", response_model=TrackingEditResponse)
def tracking_edit_delete(req: TrackingDeleteRequest):
    df = _tracking_df_load(req.table_path)
    sel = _tracking_find_rows_by_selection(df, req.selections)
    if sel.empty:
        raise HTTPException(status_code=400, detail="Select at least one point/track to delete.")

    family_prefixes = sorted(
        {
            _tracking_family_name_prefix(value)
            for value in sel["family_name"].astype(str).tolist()
            if str(value).strip()
        }
    )
    if not family_prefixes:
        raise HTTPException(status_code=400, detail="Could not determine the selected family to delete.")

    prev_n = len(df)
    mask = df["family_name"].astype(str).apply(
        lambda value: any(str(value).startswith(prefix) for prefix in family_prefixes)
    )
    df = df[~mask].copy()
    _tracking_df_save(req.table_path, df)
    preview = _tracking_preview_response(
        table_path=req.table_path,
        frame=req.frame,
        image_dir=req.image_dir,
        image_col=req.image_col,
        trail_window=req.trail_window,
        show_complete_trail=bool(req.show_complete_trail),
        preview_cache_dir=None,
        message=f"Deleted {len(family_prefixes)} track lineage(s).",
        force_redraw=True,
    )
    return TrackingEditResponse(**preview.dict(), edited_rows=int(prev_n - len(df)))


@app.post("/tracking/edit/link", response_model=TrackingEditResponse)
def tracking_edit_link(req: TrackingLinkRequest):
    df = _tracking_df_load(req.table_path)
    sel = _tracking_find_rows_by_selection(df, req.selections)
    if len(sel) < 2:
        raise HTTPException(status_code=400, detail="Select at least two points to link tracks.")
    sel = sel.sort_values(
        by=["Frame", "__selection_order"],
        kind="stable",
    ).reset_index(drop=True)

    base = sel.iloc[0]
    base_family = base["family"]
    base_family_name = str(base["family_name"])
    base_color = str(base["family_color"])
    edited = 0

    prev_x = float(base["X"])
    prev_y = float(base["Y"])
    for i in range(1, len(sel)):
        row = sel.iloc[i]
        old_track = int(row["track_id"])
        start_frame = int(row["Frame"])
        idx_target = df[(df["Frame"] == int(row["Frame"])) & (df["Cell"] == int(row["Cell"])) & (df["track_id"] == old_track)].index
        if len(idx_target):
            df.at[idx_target[0], "previous_x"] = prev_x
            df.at[idx_target[0], "previous_y"] = prev_y
            edited += 1
        mask = (df["track_id"] == old_track) & (df["Frame"] >= start_frame)
        if mask.any():
            old_family_name = str(df.loc[mask, "family_name"].iloc[0])
            df.loc[mask, "family"] = base_family
            df.loc[mask, "family_color"] = base_color
            df.loc[mask, "family_name"] = df.loc[mask, "family_name"].astype(str).apply(
                lambda x: _tracking_replace_family_prefix(x, old_family_name, base_family_name)
            )
            edited += int(mask.sum())
        prev_x = float(row["X"])
        prev_y = float(row["Y"])
    message = "Tracks linked successfully."

    _tracking_df_save(req.table_path, df)
    preview = _tracking_preview_response(
        table_path=req.table_path,
        frame=req.frame,
        image_dir=req.image_dir,
        image_col=req.image_col,
        trail_window=req.trail_window,
        show_complete_trail=bool(req.show_complete_trail),
        preview_cache_dir=None,
        message=message,
        force_redraw=True,
    )
    return TrackingEditResponse(**preview.dict(), edited_rows=edited)


@app.post("/tracking/edit/division", response_model=TrackingEditResponse)
def tracking_edit_division(req: TrackingDivisionRequest):
    df = _tracking_df_load(req.table_path)
    sel = _tracking_find_rows_by_selection(df, req.selections)
    if len(sel) != 3:
        raise HTTPException(status_code=400, detail="Cell division requires exactly 3 selected cells: mother and two daughters.")
    sel = sel.sort_values(by=["Frame", "__selection_order"], kind="stable").reset_index(drop=True)

    mother = sel.iloc[0]
    daughters = sel.iloc[1:].copy().sort_values(by=["__selection_order"], kind="stable").reset_index(drop=True)
    daughter_frames = daughters["Frame"].astype(int).tolist()
    if len(set(daughter_frames)) != 1:
        raise HTTPException(status_code=400, detail="The two daughter cells must be selected in the same frame.")
    if int(mother["Frame"]) >= int(daughters.iloc[0]["Frame"]):
        raise HTTPException(status_code=400, detail="The mother cell must be in an earlier frame than the two daughters.")

    mother_family = mother["family"]
    mother_family_name = _tracking_family_name_prefix(mother["family_name"])
    mother_color = str(mother["family_color"])
    edited = 0

    for i, (_, daughter) in enumerate(daughters.iterrows(), start=1):
        daughter_prefix = f"{mother_family_name}{i}."
        old_prefix = _tracking_family_name_prefix(daughter["family_name"])
        target_idx = df[
            (df["Frame"] == int(daughter["Frame"]))
            & (df["Cell"] == int(daughter["Cell"]))
            & (df["track_id"] == int(daughter["track_id"]))
        ].index
        if len(target_idx):
            df.at[target_idx[0], "previous_x"] = float(mother["X"])
            df.at[target_idx[0], "previous_y"] = float(mother["Y"])
            edited += 1
        mask = (df["track_id"] == int(daughter["track_id"])) & (df["Frame"] >= int(daughter["Frame"]))
        if mask.any():
            df.loc[mask, "family"] = mother_family
            df.loc[mask, "family_color"] = mother_color
            df.loc[mask, "family_name"] = df.loc[mask, "family_name"].astype(str).apply(
                lambda x, old_prefix=old_prefix, daughter_prefix=daughter_prefix: _tracking_replace_family_prefix(x, old_prefix, daughter_prefix)
            )
            edited += int(mask.sum())

    _tracking_df_save(req.table_path, df)
    preview = _tracking_preview_response(
        table_path=req.table_path,
        frame=req.frame,
        image_dir=req.image_dir,
        image_col=req.image_col,
        trail_window=req.trail_window,
        show_complete_trail=bool(req.show_complete_trail),
        preview_cache_dir=None,
        message="Cell division linked successfully.",
        force_redraw=True,
    )
    return TrackingEditResponse(**preview.dict(), edited_rows=edited)


@app.post("/tracking/edit/unlink", response_model=TrackingEditResponse)
def tracking_edit_unlink(req: TrackingUnlinkRequest):
    df = _tracking_df_load(req.table_path)
    sel = _tracking_find_rows_by_selection(df, req.selections)
    if sel.empty:
        raise HTTPException(status_code=400, detail="Select at least one point to unlink.")

    sel = sel.sort_values(by=["Frame", "__selection_order"], kind="stable").reset_index(drop=True)
    edited = 0
    frame_counts = sel["Frame"].astype(int).value_counts().to_dict()

    for _, picked in sel.iterrows():
        picked_frame = int(picked["Frame"])
        picked_cell = int(picked["Cell"])
        row_now = df[(df["Frame"] == picked_frame) & (df["Cell"] == picked_cell)].copy()
        if row_now.empty:
            continue
        current = row_now.iloc[0]
        current_idx = row_now.index[0]
        old_family_name = str(current["family_name"])
        same_frame_multi = int(frame_counts.get(picked_frame, 0)) > 1
        if same_frame_multi:
            mask = (df["Frame"] == picked_frame) & (df["Cell"] == picked_cell)
        else:
            descendant_indices = _tracking_collect_descendant_indices(df, current_idx)
            if not descendant_indices:
                descendant_indices = {current_idx}
            mask = df.index.isin(descendant_indices)
        if not mask.any():
            continue

        new_track_id = int(df["track_id"].max()) + 1
        new_family_color = str(_tracking_color_for_family(new_track_id))
        df.loc[mask, "track_id"] = new_track_id
        df.loc[mask, "family"] = new_track_id
        df.loc[mask, "family_color"] = new_family_color
        df.loc[mask, "family_name"] = df.loc[mask, "family_name"].astype(str).apply(
            lambda x: _tracking_replace_family_prefix(x, old_family_name, f"{new_track_id}.")
        )
        first_idx = df[(df["Frame"] == picked_frame) & (df["Cell"] == picked_cell) & (df["track_id"] == new_track_id)].index
        if len(first_idx):
            df.at[first_idx[0], "previous_x"] = np.nan
            df.at[first_idx[0], "previous_y"] = np.nan
        edited += int(mask.sum())

    _tracking_df_save(req.table_path, df)
    preview = _tracking_preview_response(
        table_path=req.table_path,
        frame=req.frame,
        image_dir=req.image_dir,
        image_col=req.image_col,
        trail_window=req.trail_window,
        show_complete_trail=bool(req.show_complete_trail),
        preview_cache_dir=None,
        message="Selected cells were unlinked into separate tracks.",
        force_redraw=True,
    )
    return TrackingEditResponse(**preview.dict(), edited_rows=edited)


def _link_or_copy_dir(src: Path, dst: Path) -> None:
    """Make dst point at src's contents cheaply: junction/symlink, else copy.

    Keeps the staging folder tiny — the one real image copy happens later when
    napari-TRACE builds its `_curated` working copy (it copytrees this folder).
    """
    if dst.exists():
        return
    try:
        if os.name == "nt":
            # ponytail: mklink /J (directory junction) needs no admin on Windows.
            subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)], check=True, capture_output=True)
        else:
            os.symlink(str(src), str(dst), target_is_directory=True)
    except Exception:
        shutil.copytree(src, dst)


@app.post("/tracking/curate/launch", response_model=TrackingCurateLaunchResponse)
def tracking_curate_launch(req: TrackingCurateLaunchRequest):
    from fornma.core.Tracking.mask_from_contours import build_label_mask

    table = Path(req.table_path).expanduser().resolve()
    if not table.exists() or not table.is_file():
        raise HTTPException(status_code=400, detail=f"Tracked table not found: {req.table_path}")
    pkl_dir = Path(req.pkl_dir).expanduser().resolve()
    if not pkl_dir.exists() or not pkl_dir.is_dir():
        raise HTTPException(status_code=400, detail="Select the segmentation 'pkl-data' folder (nuclear contours).")
    image_dir = Path(req.image_dir).expanduser().resolve()
    if not image_dir.exists() or not image_dir.is_dir():
        raise HTTPException(status_code=400, detail="Select the raw image frames folder used for tracking.")

    curator_dir = str(req.curator_dir or os.environ.get("FORNMA_CURATOR_DIR") or "").strip()
    curator_python = str(req.curator_python or os.environ.get("FORNMA_CURATOR_PYTHON") or sys.executable).strip()
    if curator_dir:
        # Dev override: run napari-TRACE from a source checkout.
        run_script = Path(curator_dir).expanduser().resolve() / "run_curator.py"
        if not run_script.exists():
            raise HTTPException(status_code=400, detail=f"run_curator.py not found in {curator_dir}.")
        launch_cmd = [curator_python, str(run_script), None]  # staging filled in below
    else:
        # Default: napari-TRACE is pip-installed in this environment (shipped with forNMA).
        # ponytail: find_spec checks the current env; only meaningful when curator_python == sys.executable.
        import importlib.util
        if importlib.util.find_spec("curator") is None:
            raise HTTPException(
                status_code=400,
                detail="napari-TRACE is not installed in this environment. Re-run the forNMA setup, or set FORNMA_CURATOR_DIR to a napari-TRACE source folder.",
            )
        launch_cmd = [curator_python, "-m", "curator.app", None]  # staging filled in below

    # One self-contained "Curation" folder next to the segmentation pkl-data.
    # Seeding curator_meta.json marks it as an already-set-up working copy, so
    # napari-TRACE opens it IN PLACE (no separate <name>_curated sibling) and
    # writes its exports/ inside it. If it already exists (re-launch), we leave it
    # untouched so prior curation resumes instead of being overwritten.
    staging = pkl_dir.parent / "Curation"
    meta_file = staging / "curator_meta.json"
    mask_path = staging / "mask.tif"
    if not meta_file.exists():
        staging.mkdir(parents=True, exist_ok=True)
        shutil.copy2(table, staging / "Tracked Results.csv")  # name matches napari's CSV discovery
        # ponytail: synchronous rasterization; wrap in a job thread if big movies feel slow.
        build_label_mask(str(table), str(pkl_dir), str(image_dir), str(mask_path))
        _link_or_copy_dir(image_dir, staging / "images")
        meta_file.write_text(json.dumps({"source_folder": str(staging), "version": 6}), encoding="utf-8")

    launch_cmd[-1] = str(staging)  # placeholder was None; the folder exists now
    try:
        subprocess.Popen(launch_cmd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch napari-TRACE: {e}")

    exports_dir = staging / "exports"
    return TrackingCurateLaunchResponse(
        status="launched",
        mask_path=str(mask_path),
        staging_dir=str(staging),
        curated_dir=str(staging),  # opened in place: the working folder IS this folder
        exports_dir=str(exports_dir),
        message=(
            "napari-TRACE is opening in a new window. Curate there, then SAVE ALL. "
            f"Curated results and exports will be in: {exports_dir}"
        ),
    )


def _prepare_clustering_input(req: UMAPPreviewRequest):
    datasets = req.datasets or [{"path": p, "name": Path(p).stem} for p in (req.paths or [])]
    datasets = [d for d in datasets if str(d.get("path", "")).strip()]
    if not datasets:
        raise HTTPException(status_code=400, detail="Provide at least one CSV path.")

    dfs = []
    base_cols = None
    for ds in datasets:
        p = str(ds.get("path", "")).strip()
        ds_name = str(ds.get("name", "")).strip() or Path(p).stem
        pth = Path(p).expanduser().resolve()
        if not pth.exists() or not pth.is_file():
            raise HTTPException(status_code=400, detail=f"CSV not found: {p}")
        try:
            df = pd.read_csv(pth)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read CSV '{p}': {e}")

        if "Condition" not in df.columns:
            df["Condition"] = ds_name
        else:
            cond = df["Condition"].astype(str)
            empty = cond.isna() | (cond.str.strip() == "") | (cond.str.lower() == "nan")
            if empty.any():
                df.loc[empty, "Condition"] = ds_name

        cols = tuple(str(c) for c in df.columns)
        if base_cols is None:
            base_cols = cols
        elif cols != base_cols:
            raise HTTPException(status_code=400, detail="All CSVs must have exactly the same columns (same names and order).")

        df["__source__"] = ds_name
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)
    numeric_cols = [c for c in df_all.columns if c != "__source__" and pd.api.types.is_numeric_dtype(df_all[c])]
    if not numeric_cols:
        raise HTTPException(status_code=400, detail="No numeric columns available for clustering.")

    feat_cols = req.columns or numeric_cols
    missing = [c for c in feat_cols if c not in df_all.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Selected columns not found: {missing}")
    non_numeric = [c for c in feat_cols if not pd.api.types.is_numeric_dtype(df_all[c])]
    if non_numeric:
        raise HTTPException(status_code=400, detail=f"Clustering features must be numeric. Invalid: {non_numeric}")

    valid = ~df_all[feat_cols].isna().any(axis=1)
    df_valid = df_all.loc[valid].copy()
    if df_valid.empty:
        raise HTTPException(status_code=400, detail="No valid rows after dropping NaN in selected features.")

    max_points = max(500, int(req.max_points or 12000))
    if len(df_valid) > max_points:
        df_valid = df_valid.sample(n=max_points, random_state=42)

    X = df_valid[feat_cols].to_numpy(dtype=float)
    if req.scale:
        X = StandardScaler().fit_transform(X)

    return df_all, df_valid, X, feat_cols, numeric_cols


def _compute_embedding(X: np.ndarray, req: UMAPPreviewRequest):
    method = (req.method or "umap").strip().lower()
    if method == "pca":
        pca = PCA(n_components=2, random_state=42)
        emb = pca.fit_transform(X)
        vr = getattr(pca, "explained_variance_ratio_", None)
        if vr is not None and len(vr) >= 2:
            c1 = f"PC1 ({float(vr[0]) * 100:.1f}%)"
            c2 = f"PC2 ({float(vr[1]) * 100:.1f}%)"
        else:
            c1, c2 = "PC1", "PC2"
        return emb, (c1, c2), "PCA"
    if method != "umap":
        raise HTTPException(status_code=400, detail=f"Unknown method '{req.method}'. Use 'umap' or 'pca'.")
    try:
        import umap
    except Exception:
        raise HTTPException(status_code=400, detail="Package 'umap-learn' is not installed in this environment.")
    reducer = umap.UMAP(
        n_neighbors=max(2, int(req.n_neighbors)),
        min_dist=float(req.min_dist),
        n_components=2,
        metric=(req.metric or "euclidean").lower(),
        random_state=42,
    )
    emb = reducer.fit_transform(X)
    return emb, ("UMAP1", "UMAP2"), "UMAP"


def _clustering_cache_key(req: UMAPPreviewRequest) -> str:
    datasets = req.datasets or [{"path": p, "name": Path(p).stem} for p in (req.paths or [])]
    normalized = []
    for ds in datasets:
        p = str(ds.get("path", "")).strip()
        if not p:
            continue
        pth = Path(p).expanduser().resolve()
        name = str(ds.get("name", "")).strip() or pth.stem
        try:
            st = pth.stat()
            sig = (str(pth), name, int(st.st_size), int(st.st_mtime))
        except Exception:
            sig = (str(pth), name, 0, 0)
        normalized.append(sig)
    normalized.sort()
    payload = {
        "datasets": normalized,
        "columns": sorted(req.columns or []),
        "method": (req.method or "umap").lower(),
        "n_neighbors": int(req.n_neighbors),
        "min_dist": float(req.min_dist),
        "metric": (req.metric or "euclidean").lower(),
        "scale": bool(req.scale),
        "max_points": int(req.max_points or 12000),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _cache_put_embedding(key: str, value: Dict):
    with CLUSTER_CACHE_LOCK:
        if key in CLUSTER_CACHE:
            CLUSTER_CACHE.pop(key, None)
        CLUSTER_CACHE[key] = value
        while len(CLUSTER_CACHE) > CLUSTER_CACHE_MAX_ITEMS:
            oldest = next(iter(CLUSTER_CACHE.keys()))
            CLUSTER_CACHE.pop(oldest, None)


def _df_to_stats_table(name: str, df: pd.DataFrame | None) -> StatsTable | None:
    if df is None:
        return None
    if not isinstance(df, pd.DataFrame):
        return None
    tmp = df.copy()
    if not isinstance(tmp.index, pd.RangeIndex) or tmp.index.start != 0 or tmp.index.step != 1:
        index_label = str(tmp.index.name) if tmp.index.name is not None else ""
        if index_label in tmp.columns:
            index_label = f"{index_label}_row"
        tmp.insert(0, index_label, tmp.index.astype(str))
    tmp.columns = [str(c) for c in tmp.columns]
    rows = json.loads(tmp.to_json(orient="records", date_format="iso"))
    return StatsTable(name=name, columns=[str(c) for c in tmp.columns], rows=rows)


def _apply_stats_filters(df: pd.DataFrame, filters: list[StatsFilter], helper) -> pd.DataFrame:
    active_filters = []
    for item in filters or []:
        column = str(item.column or "").strip()
        if not column:
            continue
        values = []
        for raw in item.values or []:
            norm = _normalize_filter_value(raw)
            if norm:
                values.append(norm)
        if not values:
            raise HTTPException(status_code=400, detail=f"Filter '{column}' has no selected values.")
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Filter column '{column}' was not found in the dataset.")
        active_filters.append((column, set(values)))

    if not active_filters:
        return df

    filtered = df.copy()
    helper.log("\nSubset filters:")
    for column, allowed in active_filters:
        before = len(filtered)
        filtered = filtered[filtered[column].map(_normalize_filter_value).isin(allowed)].copy()
        helper.log(f"- {column}: {', '.join(sorted(allowed))} ({before} -> {len(filtered)} rows)")

    if filtered.empty:
        raise HTTPException(status_code=400, detail="The selected filters removed all rows. Adjust the subset and try again.")

    helper.log(f"Rows kept after filtering: {len(filtered)} / {len(df)}")
    return filtered


@app.post("/clustering/umap/preview", response_model=UMAPPreviewResponse)
def clustering_umap_preview(req: UMAPPreviewRequest):
    key = _clustering_cache_key(req)
    with CLUSTER_CACHE_LOCK:
        cached = CLUSTER_CACHE.get(key)

    reused = bool(cached)
    if cached:
        df_valid = cached["df_valid"].copy()
        c1, c2 = cached["axes"]
        label = cached["label"]
        feat_cols = cached["feat_cols"]
        numeric_cols = cached["numeric_cols"]
        columns_all = cached["columns_all"]
        emb = df_valid[[c1, c2]].to_numpy(dtype=float)
    else:
        df_all, df_valid, X, feat_cols, numeric_cols = _prepare_clustering_input(req)
        emb, (c1, c2), label = _compute_embedding(X, req)
        df_valid[c1] = emb[:, 0]
        df_valid[c2] = emb[:, 1]
        columns_all = [str(c) for c in df_all.columns if c != "__source__" and _is_display_column(c)]
        _cache_put_embedding(
            key,
            {
                "df_valid": df_valid,
                "axes": (c1, c2),
                "label": label,
                "feat_cols": feat_cols,
                "numeric_cols": numeric_cols,
                "columns_all": columns_all,
            },
        )

    color_col = None
    if req.use_clusters:
        k = int(req.n_clusters or 8)
        if k < 1:
            raise HTTPException(status_code=400, detail="n_clusters must be >= 1.")
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(emb)
        df_valid["cluster"] = labels.astype(str)
        color_col = "cluster"
    elif req.color_by and req.color_by in df_valid.columns:
        color_col = req.color_by
    elif "Condition" in df_valid.columns:
        color_col = "Condition"
    elif "__source__" in df_valid.columns:
        color_col = "__source__"

    fig = px.scatter(
        df_valid,
        x=c1,
        y=c2,
        color=color_col,
        hover_data=["Condition", "__source__"] if "Condition" in df_valid.columns else ["__source__"],
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=45, r=20, t=45, b=45),
        width=max(760, min(1400, 700 + int(len(df_valid) / 40))),
    )
    return UMAPPreviewResponse(
        figure=json.loads(fig.to_json()),
        columns=columns_all,
        numeric_columns=[c for c in numeric_cols if _is_display_column(c)],
        message=f"{label} ready with {len(df_valid)} points and {len(feat_cols)} features." + (" Reused cached embedding." if reused else ""),
    )


@app.post("/clustering/elbow/preview", response_model=ClusteringElbowResponse)
def clustering_elbow_preview(req: UMAPPreviewRequest):
    key = _clustering_cache_key(req)
    with CLUSTER_CACHE_LOCK:
        cached = CLUSTER_CACHE.get(key)
    if cached:
        c1, c2 = cached["axes"]
        emb = cached["df_valid"][[c1, c2]].to_numpy(dtype=float)
        feat_cols = cached["feat_cols"]
        label = cached["label"]
    else:
        _, df_valid, X, feat_cols, numeric_cols = _prepare_clustering_input(req)
        emb, (c1, c2), label = _compute_embedding(X, req)
        df_valid[c1] = emb[:, 0]
        df_valid[c2] = emb[:, 1]
        _cache_put_embedding(
            key,
            {
                "df_valid": df_valid,
                "axes": (c1, c2),
                "label": label,
                "feat_cols": feat_cols,
                "numeric_cols": numeric_cols,
                "columns_all": [c for c in df_valid.columns if c != "__source__" and _is_display_column(c)],
            },
        )
    k_min = max(2, int(req.k_min or 2))
    k_max = max(k_min, int(req.k_max or 12))
    k_max = min(k_max, max(k_min, emb.shape[0] - 1))
    if k_min >= emb.shape[0]:
        raise HTTPException(status_code=400, detail="Not enough points to compute elbow for requested k range.")

    ks = list(range(k_min, k_max + 1))
    inertias = []
    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(emb)
        inertias.append(float(km.inertia_))

    fig = px.line(x=ks, y=inertias, markers=True, labels={"x": "k", "y": "Inertia"})
    fig.update_layout(
        template="plotly_white",
        title=f"Elbow Plot ({label})",
        margin=dict(l=45, r=20, t=55, b=45),
        width=860,
    )
    return ClusteringElbowResponse(
        figure=json.loads(fig.to_json()),
        message=f"Elbow ready using {label} embedding with {len(feat_cols)} features.",
    )


@app.post("/stats/run", response_model=StatsRunResponse)
def stats_run(req: StatsRunRequest):
    paths = [str(p).strip() for p in (req.paths or []) if str(p).strip()]
    if not paths:
        raise HTTPException(status_code=400, detail="Provide at least one CSV path.")

    # Lazy imports to keep API startup light.
    from fornma.core.Statistics.Helpers import AnalysisHelper

    tmp_log = tempfile.NamedTemporaryFile(prefix="fornma-stats-", suffix=".log", delete=False)
    tmp_log_path = tmp_log.name
    tmp_log.close()
    helper = AnalysisHelper(alpha=float(req.alpha), log_file=tmp_log_path)
    df = helper.load_and_concat(paths)
    df = _apply_stats_filters(df, req.filters, helper)
    method = (req.method or "oneway").strip().lower()
    tables: list[StatsTable] = []

    def _parse_pairs(raw_pairs: list[str]) -> list[tuple[str, str]]:
        out = []
        for item in raw_pairs or []:
            txt = str(item).strip()
            if not txt:
                continue
            if "|" in txt:
                a, b = txt.split("|", 1)
            elif "," in txt:
                a, b = txt.split(",", 1)
            else:
                parts = txt.split()
                if len(parts) >= 2:
                    a, b = parts[0], parts[1]
                else:
                    continue
            out.append((a.strip(), b.strip()))
        return out

    if method == "oneway":
        if not req.numeric_col or not req.group_col:
            raise HTTPException(status_code=400, detail="oneway requires numeric_col and group_col.")
        group_count = int(df[[req.group_col, req.numeric_col]].dropna().groupby(req.group_col).size().gt(0).sum())
        if group_count < 2:
            raise HTTPException(status_code=400, detail=f"At least two non-empty groups are required in '{req.group_col}'.")
        from fornma.core.Statistics.OneWayAnalysis import OneWayAnalysis
        ana = OneWayAnalysis(
            df=df,
            numeric_col=req.numeric_col,
            group_col=req.group_col,
            alpha=float(req.alpha),
            pairs_of_interest=_parse_pairs(req.pairs_of_interest),
            helper=helper,
        )
        results = ana.run()
        main = results.get("main_result")
        test_used = "One-way ANOVA" if isinstance(main, pd.DataFrame) else "Kruskal-Wallis"
        if isinstance(main, tuple) and len(main) == 2:
            main_df = pd.DataFrame([{"test_used": test_used, "stat": float(main[0]), "p_value": float(main[1])}])
        else:
            if isinstance(main, pd.DataFrame):
                main_df = main.copy()
                if "test_used" not in main_df.columns:
                    main_df.insert(0, "test_used", test_used)
            else:
                main_df = None
        for t in [
            _df_to_stats_table("main_result", main_df),
            _df_to_stats_table("posthoc", results.get("posthoc")),
            _df_to_stats_table("summary", results.get("summary")),
        ]:
            if t:
                tables.append(t)

    elif method == "twoway":
        if not req.numeric_col or not req.group_col1 or not req.group_col2:
            raise HTTPException(status_code=400, detail="twoway requires numeric_col, group_col1 and group_col2.")
        from fornma.core.Statistics.TwoWayAnalysis import TwoWayAnalysis
        ana = TwoWayAnalysis(
            df=df,
            numeric_col=req.numeric_col,
            group_col1=req.group_col1,
            group_col2=req.group_col2,
            alpha=float(req.alpha),
            pairs_of_interest=_parse_pairs(req.pairs_of_interest),
            helper=helper,
        )
        results = ana.run()
        main_obj = results.get("main_result")
        test_used = "Two-way ANOVA"
        if isinstance(main_obj, pd.DataFrame):
            cols_lower = [str(c).lower() for c in main_obj.columns]
            if "h_adj" in cols_lower or "p_chi2" in cols_lower:
                test_used = "Scheirer-Ray-Hare"
        main_df = main_obj.copy() if isinstance(main_obj, pd.DataFrame) else None
        if main_df is not None:
            main_df.insert(0, "test_used", test_used)
        for t in [
            _df_to_stats_table("main_result", main_df),
            _df_to_stats_table("posthoc", results.get("posthoc")),
            _df_to_stats_table("summary", results.get("summary")),
        ]:
            if t:
                tables.append(t)

    elif method == "chi2":
        if not req.group_col or not req.category_col:
            raise HTTPException(status_code=400, detail="chi2 requires group_col and category_col.")
        from fornma.core.Statistics.ChiSquareAnalyzer import ChiSquareAnalyzer
        ana = ChiSquareAnalyzer(expected_min=float(req.expected_min), use_exact=True, helper=helper)
        g = ana.global_test(df, req.group_col, req.category_col)
        post = ana.pairwise_posthoc(g.contingency_table, correction_method=req.correction_method or "auto")
        main_df = pd.DataFrame([{"test_used": "Chi-square / exact fallback", "chi2": float(g.chi2), "p_value": float(g.p_value)}])
        exp_df = None
        if g.expected is not None:
            exp_df = pd.DataFrame(g.expected, index=g.contingency_table.index, columns=g.contingency_table.columns).reset_index()
        for t in [
            _df_to_stats_table("main_result", main_df),
            _df_to_stats_table("contingency", g.contingency_table.reset_index()),
            _df_to_stats_table("percentages", g.percentages.reset_index()),
            _df_to_stats_table("expected", exp_df),
            _df_to_stats_table("posthoc", post),
        ]:
            if t:
                tables.append(t)

    elif method == "chi2-subgroups":
        if not req.group_col or not req.condition_col:
            raise HTTPException(status_code=400, detail="chi2-subgroups requires group_col and condition_col.")
        from fornma.core.Statistics.ChiSquareSubgroupComparator import ChiSquareSubgroupComparator
        ana = ChiSquareSubgroupComparator(
            expected_min=float(req.expected_min),
            correction_method=req.correction_method or "bonferroni",
            helper=helper,
        )
        df_results, prop_table = ana.compare(df=df, group_col=req.group_col, condition_col=req.condition_col)
        for t in [
            _df_to_stats_table("subgroup_results", df_results),
            _df_to_stats_table("proportions", prop_table.reset_index()),
        ]:
            if t:
                tables.append(t)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown stats method '{req.method}'.")

    log_text = ""
    try:
        log_text = Path(tmp_log_path).read_text(encoding="utf-8")
    except Exception:
        log_text = ""
    finally:
        try:
            Path(tmp_log_path).unlink(missing_ok=True)
        except Exception:
            pass

    return StatsRunResponse(method=method, message=f"{method} analysis complete.", log=log_text, tables=tables)


def _default_thresholds(mean_nii: float, std_nii: float, mean_area: float, std_area: float,
                        sd_nii: float, sd_area: float) -> Dict[str, float]:
    # Mimics NMA_settings.get_vertical_lines + calc_lines
    upper_line_x = mean_nii + 1.5 * sd_nii * std_nii
    v_up = float(upper_line_x)
    v_mid = float(upper_line_x)
    v_down = float(mean_nii)
    v_down2 = float(upper_line_x)
    y_high = float(mean_area + sd_area * std_area)
    y_low = float(mean_area - sd_area * std_area)
    return {
        "v_up": v_up,
        "v_mid": v_mid,
        "v_down": v_down,
        "v_down2": v_down2,
        "y_high": y_high,
        "y_low": y_low,
    }


def _graph_limits_from_axis(axis: Dict | None, stats: Dict[str, float]) -> list[float]:
    if axis and axis.get("x") and axis.get("y"):
        return [axis["y"][0], axis["y"][1], axis["x"][0], axis["x"][1]]
    return [
        stats["mu_y"] - 3 * stats["sd_y"],
        stats["mu_y"] + 3 * stats["sd_y"],
        stats["mu_x"] - 3 * stats["sd_x"],
        stats["mu_x"] + 3 * stats["sd_x"],
    ]


def _build_plotly_figure(df: pd.DataFrame | None, xcol: str, ycol: str,
                         stats: Dict[str, float], graph_limits: list[float],
                         thresholds: Dict[str, float]) -> go.Figure:
    fig = go.Figure()

    if df is not None and not df.empty:
        if "__ds__" in df.columns:
            palette = qual_colors.Plotly
            for i, (name, grp) in enumerate(df.groupby("__ds__")):
                fig.add_trace(go.Scattergl(
                    x=grp[xcol],
                    y=grp[ycol],
                    mode="markers",
                    marker=dict(size=6, opacity=0.65, color=palette[i % len(palette)]),
                    name=str(name),
                ))
        else:
            fig.add_trace(go.Scattergl(
                x=df[xcol],
                y=df[ycol],
                mode="markers",
                marker=dict(size=6, opacity=0.65, color="#2563eb"),
                name="Controls (sample)",
            ))

    rx = float(thresholds["v_up"] - stats["mu_x"]) / 1.5 if stats["sd_x"] else 1.0
    ry = float(thresholds["y_high"] - stats["mu_y"]) if stats["sd_y"] else 1.0

    fig.add_trace(ellipse_trace(stats["mu_x"], stats["mu_y"], rx, ry))

    # horizontal lines
    fig.add_trace(go.Scatter(x=[graph_limits[2], graph_limits[3]], y=[thresholds["y_high"], thresholds["y_high"]],
                             mode="lines", line=dict(color="black", width=2), name="y_high"))
    fig.add_trace(go.Scatter(x=[graph_limits[2], graph_limits[3]], y=[thresholds["y_low"], thresholds["y_low"]],
                             mode="lines", line=dict(color="black", width=2), name="y_low"))

    # vertical lines
    for key in ["v_up", "v_mid", "v_down", "v_down2"]:
        fig.add_trace(go.Scatter(x=[thresholds[key], thresholds[key]], y=[graph_limits[0], graph_limits[1]],
                                 mode="lines", line=dict(color="#12c7e5", width=3), name=key))

    fig.update_layout(
        autosize=False,
        width=640,
        height=640,
        margin=dict(l=60, r=10, t=50, b=60),
        title=dict(text="NMA thresholds", x=0.5, xanchor="center"),
        xaxis_title=xcol,
        yaxis_title=ycol,
        xaxis_range=[graph_limits[2], graph_limits[3]],
        yaxis_range=[graph_limits[0], graph_limits[1]],
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _save_settings(req: NMASaveSettingsRequest) -> Path:
    mean_nii = req.mean_nii
    std_nii = req.std_nii
    mean_area = req.mean_area
    std_area = req.std_area
    sd_nii = req.sd_nii
    sd_area = req.sd_area

    thresholds = req.thresholds

    # horizontal lines
    h_x = [mean_nii - sd_nii * std_nii, mean_nii + 3 * sd_nii * std_nii]
    h_y_up = [thresholds.y_high, thresholds.y_high]
    h_y_down = [thresholds.y_low, thresholds.y_low]

    # vertical lines
    v_upx = [thresholds.v_up, thresholds.v_up]
    v_midx = [thresholds.v_mid, thresholds.v_mid]
    v_downx = [thresholds.v_down, thresholds.v_down]
    v_downx2 = [thresholds.v_down2, thresholds.v_down2]

    v_upy = [int(mean_area + sd_area * std_area), int(mean_area + (2 + sd_area) * std_area)]
    v_midy = [int(mean_area - sd_area * std_area), v_upy[0]]
    v_downy = [int(mean_area - (1 + sd_area) * std_area), v_midy[0]]

    nma_parameters = {
        "name": req.name,
        "sd_area": sd_area,
        "sd_NII": sd_nii,
        "mean_NII": mean_nii,
        "std_NII": std_nii,
        "mean_a": mean_area,
        "std_a": std_area,
        "circle": np.linspace(0, 2 * np.pi, 100),
        "graph_limits": req.graph_limits,
        "ellipse": None,
        "h_x": h_x,
        "h_y_up": h_y_up,
        "h_y_down": h_y_down,
        "graph_box": dict(boxstyle="round,pad=0.3", fc="#dedcdc", alpha=0.7, ec="#bdbbbb", lw=1),
        "v_upx": v_upx,
        "v_upy": v_upy,
        "v_midx": v_midx,
        "v_midy": v_midy,
        "v_downx": v_downx,
        "v_downy": v_downy,
        "v_downx2": v_downx2,
        "fig": None,
    }

    NMA_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(NMA_SETTINGS_PATH, "wb") as handle:
        pickle.dump(nma_parameters, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return NMA_SETTINGS_PATH


@app.post("/nma/settings/compute", response_model=NMAComputeResponse)
def nma_settings_compute(req: NMAComputeRequest):
    params = _params_to_dict(req)
    pool, xcol, ycol, log = load_controls_pool(params, sample_per_ds=req.sample_per_ds)
    _require_controls(pool, log)

    pool_stats, gate_meta = _apply_control_gate(pool, xcol, ycol, req.control_gate)
    stats = _compute_stats(pool_stats, xcol, ycol)

    axis = compute_axis_ranges_from_all(
        params,
        k=req.axis_k,
        headroom=req.axis_headroom,
        use_quantile=req.axis_quantile,
        k_neg=req.axis_k_neg,
    )

    graph_limits = _graph_limits_from_axis(axis, stats)
    thresholds = _default_thresholds(
        mean_nii=stats["mu_x"],
        std_nii=stats["sd_x"],
        mean_area=stats["mu_y"],
        std_area=stats["sd_y"],
        sd_nii=1.0,
        sd_area=1.0,
    )

    fig = _build_plotly_figure(pool_stats, xcol, ycol, stats, graph_limits, thresholds)

    sample = {
        "x": pool_stats[xcol].astype(float).tolist(),
        "y": pool_stats[ycol].astype(float).tolist(),
    }

    return NMAComputeResponse(
        log=log,
        stats=stats,
        axis=axis,
        sample=sample,
        sd_factors={"sd_nii": 1.0, "sd_area": 1.0},
        figure=_json_safe(fig.to_dict()),
        gate=_json_safe(gate_meta),
    )


@app.post("/nma/settings/preview", response_model=NMAPreviewResponse)
def nma_settings_preview(req: NMAComputeRequest):
    params = _params_to_dict(req)
    pool, xcol, ycol, log = load_controls_pool(params, sample_per_ds=req.sample_per_ds)
    _require_controls(pool, log)

    pool_stats, gate_meta = _apply_control_gate(pool, xcol, ycol, req.control_gate)
    stats = _compute_stats(pool_stats, xcol, ycol)

    axis = compute_axis_ranges_from_all(
        params,
        k=req.axis_k,
        headroom=req.axis_headroom,
        use_quantile=req.axis_quantile,
        k_neg=req.axis_k_neg,
    )

    graph_limits = _graph_limits_from_axis(axis, stats)

    thresholds = _default_thresholds(
        mean_nii=stats["mu_x"],
        std_nii=stats["sd_x"],
        mean_area=stats["mu_y"],
        std_area=stats["sd_y"],
        sd_nii=1.0,
        sd_area=1.0,
    )

    return NMAPreviewResponse(
        stats=stats,
        sd_factors={"sd_nii": 1.0, "sd_area": 1.0},
        graph_limits=[float(x) for x in graph_limits],
        thresholds=NMAThresholds(**thresholds),
        gate=_json_safe(gate_meta),
    )


@app.post("/nma/settings/figure", response_model=NMAFigureResponse)
def nma_settings_figure(req: NMAFigureRequest):
    params = _params_to_dict(req)
    if not _has_control(params):
        raise HTTPException(status_code=400, detail="At least one dataset must be marked as control.")

    pool_ctrl, xcol, ycol, log = load_controls_pool(params, sample_per_ds=req.sample_per_ds)
    _require_controls(pool_ctrl, log)

    pool_stats, gate_meta = _apply_control_gate(pool_ctrl, xcol, ycol, req.control_gate)
    stats = _compute_stats(pool_stats, xcol, ycol)

    axis = compute_axis_ranges_from_all(
        params,
        k=req.axis_k,
        headroom=req.axis_headroom,
        use_quantile=req.axis_quantile,
        k_neg=req.axis_k_neg,
    )

    graph_limits = _graph_limits_from_axis(axis, stats)

    thresholds = req.thresholds.model_dump() if req.thresholds else _default_thresholds(
        mean_nii=stats["mu_x"],
        std_nii=stats["sd_x"],
        mean_area=stats["mu_y"],
        std_area=stats["sd_y"],
        sd_nii=req.sd_nii,
        sd_area=req.sd_area,
    )

    df_plot = None
    if req.include_sample:
        if req.include_all_datasets:
            pool_all, xcol_all, ycol_all, log_all = load_all_datasets(
                params,
                sample_per_ds=req.sample_per_ds_all,
            )
            if pool_all is None or pool_all.empty:
                raise HTTPException(status_code=400, detail=f"No datasets loaded. Details:\n{log_all}")
            df_plot = pool_all
            xcol = xcol_all
            ycol = ycol_all
        else:
            df_plot = pool_stats

    fig = _build_plotly_figure(df_plot, xcol, ycol, stats, graph_limits, thresholds)

    return NMAFigureResponse(
        figure=_json_safe(fig.to_dict()),
        stats=stats,
        graph_limits=[float(x) for x in graph_limits],
    )


@app.post("/nma/settings/auto-dbscan", response_model=NMAAutoDbscanResponse)
def nma_settings_auto_dbscan(req: NMAAutoDbscanRequest):
    params = _params_to_dict(req)
    pool, xcol, ycol, log = load_controls_pool(params, sample_per_ds=req.sample_per_ds)
    _require_controls(pool, log)

    pool_stats, _gate_meta = _apply_control_gate(pool, xcol, ycol, req.control_gate)
    stats = _compute_stats(pool_stats, xcol, ycol)
    mu_x = stats["mu_x"]
    mu_y = stats["mu_y"]
    sd_x_all = stats["sd_x"]
    sd_y_all = stats["sd_y"]

    df = pool_stats[[xcol, ycol]].copy().dropna()

    X = df[[xcol, ycol]].to_numpy(dtype=float)
    Xs = StandardScaler().fit_transform(X)

    k = min(10, max(2, int(0.01 * len(Xs)) or 2))
    nbrs = NearestNeighbors(n_neighbors=k).fit(Xs)
    dists, _ = nbrs.kneighbors(Xs)
    kdist = np.sort(dists[:, -1])
    eps = float(np.percentile(kdist, req.eps_percentile))

    db = DBSCAN(eps=eps, min_samples=k).fit(Xs)
    labels = db.labels_
    vals, counts = np.unique(labels[labels >= 0], return_counts=True)
    if len(vals) == 0:
        raise HTTPException(status_code=400, detail="DBSCAN found no core clusters (all noise).")

    core_label = vals[np.argmax(counts)]
    core = df[labels == core_label].copy()

    core_x = core[xcol].to_numpy(dtype=float)
    core_y = core[ycol].to_numpy(dtype=float)

    max_x_dev = float(np.percentile(np.abs(core_x - mu_x), req.pctl))
    max_y_dev = float(np.percentile(np.abs(core_y - mu_y), req.pctl))

    kx = max_x_dev / (sd_x_all or 1.0)
    ky = max_y_dev / (sd_y_all or 1.0)

    rx = kx * sd_x_all
    ry = ky * sd_y_all

    log_out = "\n".join([
        log,
        f"DBSCAN: eps≈{eps:.3f}, k={k}, core_size={len(core)}/{len(df)}",
        f"center_fixed=({mu_x:.3g},{mu_y:.3g})",
        f"core_p{req.pctl} dev=({max_x_dev:.3g},{max_y_dev:.3g})",
        f"sliders=(sd_nii={kx:.3g}, sd_area={ky:.3g}) -> rx,ry=({rx:.3g},{ry:.3g})",
    ])

    return NMAAutoDbscanResponse(
        log=log_out,
        stats=stats,
        sd_factors={"sd_nii": float(kx), "sd_area": float(ky)},
        ellipse={"rx": float(rx), "ry": float(ry)},
    )


@app.post("/nma/settings/save", response_model=NMASaveSettingsResponse)
def nma_settings_save(req: NMASaveSettingsRequest):
    if len(req.graph_limits) != 4:
        raise HTTPException(status_code=400, detail="graph_limits must have 4 values: [ymin, ymax, xmin, xmax]")

    _save_settings(req)
    return NMASaveSettingsResponse(status="ok", settings_path=str(NMA_SETTINGS_PATH))


@app.get("/nma/settings", response_model=NMASettingsResponse)
def nma_settings_get():
    if not NMA_SETTINGS_PATH.exists():
        raise HTTPException(status_code=404, detail="NMA settings not found")

    with open(NMA_SETTINGS_PATH, "rb") as f:
        pkl = pickle.load(f)

    def _first(v, default=None):
        try:
            return float(v[0]) if isinstance(v, (list, tuple)) else float(v)
        except Exception:
            return default

    thresholds = NMAThresholds(
        v_up=_first(pkl.get("v_upx"), 0.0),
        v_mid=_first(pkl.get("v_midx"), 0.0),
        v_down=_first(pkl.get("v_downx"), 0.0),
        v_down2=_first(pkl.get("v_downx2"), 0.0),
        y_high=_first(pkl.get("h_y_up"), 0.0),
        y_low=_first(pkl.get("h_y_down"), 0.0),
    )

    return NMASettingsResponse(
        name=pkl.get("name", ""),
        sd_area=float(pkl.get("sd_area", 0.0)),
        sd_nii=float(pkl.get("sd_NII", 0.0)),
        mean_nii=float(pkl.get("mean_NII", 0.0)),
        std_nii=float(pkl.get("std_NII", 0.0)),
        mean_area=float(pkl.get("mean_a", 0.0)),
        std_area=float(pkl.get("std_a", 0.0)),
        graph_limits=[float(x) for x in (pkl.get("graph_limits") or [0, 0, 0, 0])],
        thresholds=thresholds,
    )


@app.get("/nma/settings/download")
def nma_settings_download():
    if not NMA_SETTINGS_PATH.exists():
        raise HTTPException(status_code=404, detail="NMA settings not found")
    return FileResponse(
        path=NMA_SETTINGS_PATH,
        filename="nma_settings.pickle",
        media_type="application/octet-stream",
    )


@app.post("/nma/settings/upload", response_model=NMASettingsUploadResponse)
async def nma_settings_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pkl = pickle.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read settings file: {e}")

    def _first(v, default=None):
        try:
            return float(v[0]) if isinstance(v, (list, tuple)) else float(v)
        except Exception:
            return default

    thresholds = NMAThresholds(
        v_up=_first(pkl.get("v_upx"), 0.0),
        v_mid=_first(pkl.get("v_midx"), 0.0),
        v_down=_first(pkl.get("v_downx"), 0.0),
        v_down2=_first(pkl.get("v_downx2"), 0.0),
        y_high=_first(pkl.get("h_y_up"), 0.0),
        y_low=_first(pkl.get("h_y_down"), 0.0),
    )

    name = pkl.get("name") or (file.filename or "control")
    resp = NMASettingsUploadResponse(
        name=name,
        sd_area=float(pkl.get("sd_area", 0.0)),
        sd_nii=float(pkl.get("sd_NII", 0.0)),
        mean_nii=float(pkl.get("mean_NII", 0.0)),
        std_nii=float(pkl.get("std_NII", 0.0)),
        mean_area=float(pkl.get("mean_a", 0.0)),
        std_area=float(pkl.get("std_a", 0.0)),
        graph_limits=[float(x) for x in (pkl.get("graph_limits") or [0, 0, 0, 0])],
        thresholds=thresholds,
    )

    # Persist uploaded settings for download consistency
    try:
        NMA_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(NMA_SETTINGS_PATH, "wb") as handle:
            pickle.dump(pkl, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass

    return resp
