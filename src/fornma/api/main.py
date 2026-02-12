from __future__ import annotations

from pathlib import Path
import pickle
from typing import Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative as qual_colors
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from fornma.gui.utils.nma_helpers import (
    load_controls_pool,
    load_all_datasets,
    compute_axis_ranges_from_all,
    ellipse_trace,
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
)


APP_ROOT = Path(__file__).resolve().parent
NMA_SETTINGS_PATH = (APP_ROOT.parent / "core" / "NMA" / "control_parameters.pickle").resolve()

app = FastAPI(title="forNMA API")

# Allow local dev frontends (Vite) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/nma/datasets/columns", response_model=DatasetColumnsResponse)
def nma_datasets_columns(req: DatasetColumnsRequest):
    try:
        df = pd.read_csv(req.path, nrows=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV header: {e}")
    cols = [str(c) for c in df.columns.tolist()]
    return DatasetColumnsResponse(columns=cols)


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
        xaxis_title="NII",
        yaxis_title="Area",
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

    stats = _compute_stats(pool, xcol, ycol)

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

    fig = _build_plotly_figure(pool, xcol, ycol, stats, graph_limits, thresholds)

    sample = {
        "x": pool[xcol].astype(float).tolist(),
        "y": pool[ycol].astype(float).tolist(),
    }

    return NMAComputeResponse(
        log=log,
        stats=stats,
        axis=axis,
        sample=sample,
        sd_factors={"sd_nii": 1.0, "sd_area": 1.0},
        figure=fig.to_dict(),
    )


@app.post("/nma/settings/preview", response_model=NMAPreviewResponse)
def nma_settings_preview(req: NMAComputeRequest):
    params = _params_to_dict(req)
    pool, xcol, ycol, log = load_controls_pool(params, sample_per_ds=req.sample_per_ds)
    _require_controls(pool, log)

    stats = _compute_stats(pool, xcol, ycol)

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
    )


@app.post("/nma/settings/figure", response_model=NMAFigureResponse)
def nma_settings_figure(req: NMAFigureRequest):
    params = _params_to_dict(req)
    if not _has_control(params):
        raise HTTPException(status_code=400, detail="At least one dataset must be marked as control.")

    pool_ctrl, xcol, ycol, log = load_controls_pool(params, sample_per_ds=req.sample_per_ds)
    _require_controls(pool_ctrl, log)

    stats = _compute_stats(pool_ctrl, xcol, ycol)

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
            df_plot = pool_ctrl

    fig = _build_plotly_figure(df_plot, xcol, ycol, stats, graph_limits, thresholds)

    return NMAFigureResponse(
        figure=fig.to_dict(),
        stats=stats,
        graph_limits=[float(x) for x in graph_limits],
    )


@app.post("/nma/settings/auto-dbscan", response_model=NMAAutoDbscanResponse)
def nma_settings_auto_dbscan(req: NMAAutoDbscanRequest):
    params = _params_to_dict(req)
    pool, xcol, ycol, log = load_controls_pool(params, sample_per_ds=req.sample_per_ds)
    _require_controls(pool, log)

    stats = _compute_stats(pool, xcol, ycol)
    mu_x = stats["mu_x"]
    mu_y = stats["mu_y"]
    sd_x_all = stats["sd_x"]
    sd_y_all = stats["sd_y"]

    df = pool[[xcol, ycol]].copy().dropna()

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
