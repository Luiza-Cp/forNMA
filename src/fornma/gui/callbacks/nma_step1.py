# src/fornma/gui/callbacks/nma_step1.py
from __future__ import annotations
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from fornma.gui.utils.nma_helpers import (
    load_controls_pool,
    ellipse_trace,
    compute_axis_ranges_from_all,
)
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

import pickle
from pathlib import Path
import dash
from dash import Input, Output, State, no_update, ctx

# seletor nativo do SO
import tkinter as tk
from tkinter import filedialog as tkfd


# ---------- helpers ----------
try:
    from fornma.gui.utils.nma_helpers import build_final_figure_from_payload  # opcional, se existir
except Exception:
    build_final_figure_from_payload = None

def _pkl_to_stores(pkl: dict, store_nma_in: dict | None = None) -> tuple[dict, dict, dict]:
    """
    Converte o PKL para stores, PRESERVANDO o dataset já carregado no store-nma.
    Se o PKL trouxer 'params' úteis, mescla também.
    """
    pkl = pkl or {}
    store_nma_in = store_nma_in or {}

    # ---- métricas centrais ----
    mean_nii = float(pkl.get("mean_NII", 0.0))
    mean_a   = float(pkl.get("mean_a", 0.0))
    std_nii  = float(pkl.get("std_NII", 1.0))
    std_a    = float(pkl.get("std_a", 1.0))
    sd_area  = float(pkl.get("sd_area", 1.0))
    sd_nii   = float(pkl.get("sd_NII", 1.0))

    rx = sd_nii * std_nii
    ry = sd_area * std_a

    gl = pkl.get("graph_limits") or (
        mean_a - 3*std_a, mean_a + 3*std_a, mean_nii - 3*std_nii, mean_nii + 3*std_nii
    )
    min_a, max_a, min_nii, max_nii = [float(x) for x in gl]
    axis = {"x": [min_nii, max_nii], "y": [min_a, max_a]}

    def _first(v, default=None):
        try: return float(v[0])
        except Exception: return default

    thresholds = {
        "v_up":    _first(pkl.get("v_upx"),   mean_nii + rx),
        "v_mid":   _first(pkl.get("v_midx"),  mean_nii + rx),
        "v_down":  _first(pkl.get("v_downx"), mean_nii),
        "v_down2": _first(pkl.get("v_downx2"), None),
        "y_low":   _first(pkl.get("h_y_down"), mean_a - ry),
        "y_high":  _first(pkl.get("h_y_up"),   mean_a + ry),

        # aliases
        "x_left":  _first(pkl.get("v_downx"), mean_nii),
        "x_mid":   _first(pkl.get("v_midx"),  mean_nii + rx),
        "x_right": _first(pkl.get("v_upx"),   mean_nii + rx),
    }

    # ---- store_step1 ----
    # Se o usuário já tinha escolhido colunas no app, mantenha-as:
    col_x = (store_nma_in.get("params") or {}).get("col_x") \
            or (store_nma_in.get("col_x")) \
            or "NII"
    col_y = (store_nma_in.get("params") or {}).get("col_y") \
            or (store_nma_in.get("col_y")) \
            or "Area"

    store_step1 = {
        "mu_x": mean_nii,
        "mu_y": mean_a,
        "std_nii": std_nii,
        "std_a": std_a,
        "sd_area": sd_area,
        "nii_sd_factor": sd_nii,
        "rx": rx,
        "ry": ry,
        "axis": axis,
        "col_x": col_x,
        "col_y": col_y,
        "control_label": (store_nma_in.get("params") or {}).get("control_label") or "control",
    }

    # ---- store_settings ----
    store_settings = {"thresholds": thresholds}

    # ---- store_nma_out: PRESERVA df/params já carregados ----
    store_nma_out = dict(store_nma_in)  # shallow copy
    # Se o PKL trouxer params adicionais, mescla:
    if "params" in pkl:
        merged_params = {**(store_nma_in.get("params") or {}), **(pkl["params"] or {})}
        store_nma_out["params"] = merged_params

    return store_nma_out, store_step1, store_settings


def _payload_to_stores(payload: dict) -> tuple[dict, dict, dict]:
    """
    Mapeia o payload carregado para os 3 stores usados no app.
    Ajuste os nomes das chaves conforme o schema do seu pickle.
    """
    payload = payload or {}

    # store-nma: costuma carregar "params" e/ou dados-base
    store_nma = {
        **(payload.get("store_nma") or {}),
    }
    if "params" in payload:
        store_nma["params"] = payload["params"]

    # store-nma-step1: tudo que seu step1 (colunas, ranges) precise para pular as telas
    store_step1 = {
        **(payload.get("step1") or {}),
    }

    # store-nma-settings: configurações refinadas do step2/3
    store_settings = {
        **(payload.get("settings") or {}),
    }

    return store_nma, store_step1, store_settings

def _make_step1_figure(df: pd.DataFrame | None, xcol: str, ycol: str,
                       xc: float, yc: float, rx: float, ry: float) -> go.Figure:
    fig = go.Figure()
    if df is not None and not df.empty:
        fig.add_trace(go.Scattergl(
            x=df[xcol], y=df[ycol],
            mode="markers",
            marker=dict(size=6, opacity=0.65, color="#2563eb"),
            name="Controls (sample)",
        ))
        fig.add_trace(ellipse_trace(xc, yc, rx, ry))
        title_txt = "Adjust here the threshold ellipse.<br><sup>Use the Area/NII SD sliders</sup>"
    else:
        title_txt = "No control data to preview.<br><sup>Mark at least one dataset as Control and click Create</sup>"

    fig.update_layout(
        autosize=False, width=640, height=640,
        margin=dict(l=60, r=10, t=70, b=60),
        title=dict(text=title_txt, x=0.5, xanchor="center"),
        xaxis_title="NII",
        yaxis_title=ycol or "Area",
    )
    return fig



# ---------- registro ----------

# ---------- registro ----------
def register(app):
    # A) Clique em "Create NMA Settings" → gera amostra, SDs e desenha figura inicial
    @app.callback(
        Output("nma-fig-ellipse", "figure"),
        Output("store-nma-step1", "data"),
        Output("nma-nii-sd", "value"),
        Output("nma-area-sd", "value"),
        Output("nma-step1-debug", "children"),
        Input("btn-nma-build", "n_clicks"),
        Input("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _step1_init(_n_clicks, store_nma):
        params = (store_nma or {}).get("params")
        if not params:
            if ctx.triggered_id == "btn-nma-build":
                return no_update, no_update, no_update, no_update, "aguardando params do botão…"
            return _make_step1_figure(None, "NII", "Area", 0, 0, 1, 1), {}, 1.0, 1.0, "params: vazio/nulo"

        pool, xcol, ycol, log = load_controls_pool(params)
        if pool is None or pool.empty:
            fig = _make_step1_figure(None, "NII", "Area", 0, 0, 1, 1)
            return fig, {}, 1.0, 1.0, log

        mu_x = float(pool[xcol].mean())
        sd_x = float(pool[xcol].std(ddof=1) or 1.0)
        mu_y = float(pool[ycol].mean())
        sd_y = float(pool[ycol].std(ddof=1) or 1.0)

        kx = 1.0
        ky = 1.0
        rx = kx * sd_x
        ry = ky * sd_y

        axis = compute_axis_ranges_from_all(params, k=3.0, headroom=0.05)

        fig = _make_step1_figure(pool, xcol, ycol, mu_x, mu_y, rx, ry)
        if axis and axis.get("x") and axis.get("y"):
            fig.update_layout(xaxis_range=axis["x"], yaxis_range=axis["y"])
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        store = {
            "xcol": xcol, "ycol": ycol,
            "mu_x": mu_x, "mu_y": mu_y,
            "sd_x": sd_x, "sd_y": sd_y,
            "kx": kx, "ky": ky,
            "rx": rx, "ry": ry,
            "axis": axis,
            "sample": {
                "x": pool[xcol].astype(float).tolist(),
                "y": pool[ycol].astype(float).tolist(),
            },
        }
        return fig, store, kx, ky, log

    # B) Sliders → redesenha elipse (usa amostra no store)
    @app.callback(
        Output("nma-fig-ellipse", "figure", allow_duplicate=True),
        Output("store-nma-step1", "data", allow_duplicate=True),
        Input("nma-nii-sd", "value"),
        Input("nma-area-sd", "value"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _step1_update(kx, ky, store):
        if not store:
            fig = _make_step1_figure(None, "NII", "Area", 0, 0, 1, 1)
            return fig, no_update

        xcol = store["xcol"]; ycol = store["ycol"]
        mu_x = store["mu_x"]; mu_y = store["mu_y"]
        sd_x = store["sd_x"]; sd_y = store["sd_y"]

        rx = float(kx) * sd_x
        ry = float(ky) * sd_y

        x = np.asarray(store["sample"]["x"], dtype=float)
        y = np.asarray(store["sample"]["y"], dtype=float)
        df = pd.DataFrame({xcol: x, ycol: y})

        fig = _make_step1_figure(df, xcol, ycol, mu_x, mu_y, rx, ry)

        axis = (store or {}).get("axis")
        if axis and axis.get("x") and axis.get("y"):
            fig.update_layout(xaxis_range=axis["x"], yaxis_range=axis["y"])

        new_store = dict(store)
        new_store.update({"kx": float(kx), "ky": float(ky), "rx": float(rx), "ry": float(ry), "axis": axis})
        return fig, new_store

    # C) 🔵 AUTO (DBSCAN) → detecta cluster “core” e ajusta elipse/sliders
    @app.callback(
        Output("nma-fig-ellipse", "figure", allow_duplicate=True),
        Output("store-nma-step1", "data", allow_duplicate=True),
        Output("nma-nii-sd", "value", allow_duplicate=True),
        Output("nma-area-sd", "value", allow_duplicate=True),
        Output("nma-step1-debug", "children", allow_duplicate=True),
        Input("nma-find-settings", "n_clicks"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _step1_auto_dbscan(n, store):
        if not n or not store or not store.get("sample"):
            raise Exception("Auto(DBSCAN): missing sample/store")

        xcol = store["xcol"];
        ycol = store["ycol"]
        # médias e DP globais (fixam o centro e a escala dos sliders)
        mu_x = float(store["mu_x"]);
        mu_y = float(store["mu_y"])
        sd_x_all = float(store.get("sd_x", 1.0) or 1.0)
        sd_y_all = float(store.get("sd_y", 1.0) or 1.0)

        import numpy as np, pandas as pd
        df = pd.DataFrame({
            xcol: np.asarray(store["sample"]["x"], dtype=float),
            ycol: np.asarray(store["sample"]["y"], dtype=float),
        }).dropna()

        log_parts = []
        # --- DBSCAN para detectar o core denso (sem mudar o centro) ---


        X = df[[xcol, ycol]].to_numpy(dtype=float)
        Xs = StandardScaler().fit_transform(X)

        k = min(10, max(2, int(0.01 * len(Xs)) or 2))
        nbrs = NearestNeighbors(n_neighbors=k).fit(Xs)
        dists, _ = nbrs.kneighbors(Xs)
        kdist = np.sort(dists[:, -1])
        eps = float(np.percentile(kdist, 90))  # ajuste aqui se quiser um DBSCAN mais “aberto”
        db = DBSCAN(eps=eps, min_samples=k).fit(Xs)
        labels = db.labels_
        vals, counts = np.unique(labels[labels >= 0], return_counts=True)
        if len(vals) == 0:
            raise RuntimeError("DBSCAN found no core clusters (all noise).")
        core_label = vals[np.argmax(counts)]
        core = df[labels == core_label].copy()
        log_parts.append(f"DBSCAN: eps≈{eps:.3f}, k={k}, core_size={len(core)}/{len(df)}")


        # ---- centro permanece nas médias globais; usamos o core só para limiares densos ----
        core_x = core[xcol].to_numpy(dtype=float)
        core_y = core[ycol].to_numpy(dtype=float)

        # (opção mais estável): percentil 95 da distância ao centro
        pctl = 90  # troque para 90/97/etc se quiser mais ou menos “aperto”
        max_x_dev = float(np.percentile(np.abs(core_x - mu_x), pctl))
        max_y_dev = float(np.percentile(np.abs(core_y - mu_y), pctl))

        # converte para fatores dos sliders (em DP globais)
        kx = max_x_dev / (sd_x_all or 1.0)
        ky = max_y_dev / (sd_y_all or 1.0)

        # raios reais da elipse
        rx = kx * sd_x_all
        ry = ky * sd_y_all

        # std do core (apenas informativo/compatibilidade com outros passos)
        std_x_core = float(core_x.std(ddof=1) or 1.0)
        std_y_core = float(core_y.std(ddof=1) or 1.0)

        # figura
        import plotly.graph_objects as go
        fig = _make_step1_figure(core, xcol, ycol, mu_x, mu_y, rx, ry)
        axis = (store or {}).get("axis")
        if axis and axis.get("x") and axis.get("y"):
            fig.update_layout(xaxis_range=axis["x"], yaxis_range=axis["y"])
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        new_store = dict(store)
        new_store.update({
            "mu_x": mu_x, "mu_y": mu_y,
            "kx": float(kx), "ky": float(ky),
            "rx": float(rx), "ry": float(ry),
            "std_x": std_x_core, "std_y": std_y_core,  # <- agora definido
            "sample_core_size": int(len(core)),
            "auto_pctl": int(pctl),
        })

        debug = "\n".join(log_parts + [
            f"center_fixed=({mu_x:.3g},{mu_y:.3g})",
            f"core_p{pctl} dev=({max_x_dev:.3g},{max_y_dev:.3g})",
            f"core_std=({std_x_core:.3g},{std_y_core:.3g})",
            f"sliders=(kx={kx:.3g}, ky={ky:.3g})  -> rx,ry=({rx:.3g},{ry:.3g})",
        ])

        return fig, new_store, float(kx), float(ky), debug



def register_load_settings_callbacks(app):
    """
    Registra o callback de 'Load settings' que:
      1) abre seletor de arquivo .pkl/.pickle
      2) carrega payload
      3) atualiza os stores
      4) exibe o resultado final (mostra result-pane e esconde step panes)
    """

    @app.callback(
        [
            Output("store-nma", "data", allow_duplicate=True),
            Output("store-nma-step1", "data", allow_duplicate=True),
            Output("store-nma-settings", "data", allow_duplicate=True),
            Output("nma-result-pane", "style", allow_duplicate=True),
            Output("nma-step1-pane", "style", allow_duplicate=True),
            Output("nma-step2-pane", "style", allow_duplicate=True),
            Output("nma-load-status", "children", allow_duplicate=True),
        ],
        [Input("btn-nma-load", "n_clicks")],
        [State("store-nma", "data")],  # 👈 preserva o que já existe
        prevent_initial_call=True,
    )
    def _on_click_load(n_clicks, store_nma_in):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        # 1) escolher arquivo
        root = tk.Tk();
        root.withdraw();
        root.attributes("-topmost", True)
        file_path = tkfd.askopenfilename(
            title="Selecione o arquivo de configurações NMA",
            filetypes=[("Pickle files", "*.pkl *.pickle"), ("All files", "*.*")],
        )
        root.destroy()
        if not file_path:
            raise dash.exceptions.PreventUpdate

        # 2) carregar pickle
        with open(file_path, "rb") as f:
            payload = pickle.load(f)

        # 3) converter p/ stores (sem mexer no df já carregado)
        store_nma_out, store_step1, store_settings = _pkl_to_stores(payload, store_nma_in)

        # 4) mostrar resultado e esconder steps
        show, hide = {"display": "block"}, {"display": "none"}
        status = f"✅ Settings carregadas de: {Path(file_path).name}"

        return (
            store_nma_out,  # 👈 mantém df_json/params já presentes
            store_step1,
            store_settings,
            show,
            hide,
            hide,
            status,
        )