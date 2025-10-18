# src/fornma/gui/callbacks/nma_step1.py
from __future__ import annotations
from dash import Input, Output, State, ctx, no_update
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from fornma.gui.utils.nma_helpers import (
    load_controls_pool,
    ellipse_trace,
    compute_axis_ranges_from_all,
)

# ---------- helpers ----------

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
def register(app):
    # A) Clique em "Create NMA Settings" → gera amostra, SDs e desenha figura inicial

    @app.callback(
        Output("nma-fig-ellipse", "figure"),
        Output("store-nma-step1", "data"),
        Output("nma-nii-sd", "value"),
        Output("nma-area-sd", "value"),
        Output("nma-step1-debug", "children"),  # pode estar oculto no layout
        Input("btn-nma-build", "n_clicks"),
        Input("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _step1_init(_n_clicks, store_nma):
        """
        Inicializa Step 1 quando o usuário clica em Create NMA Settings
        (ou quando o store-nma muda). Só prossegue se houver params.
        """
        params = (store_nma or {}).get("params")
        if not params:
            if ctx.triggered_id == "btn-nma-build":
                return no_update, no_update, no_update, no_update, "aguardando params do botão…"
            return _make_step1_figure(None, "NII", "Area", 0, 0, 1, 1), {}, 1.0, 1.0, "params: vazio/nulo"

        # carrega controles (amostra)
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

        # Ranges globais (todos os datasets) = média ± 3*sd
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
            "axis": axis,  # guarda ranges globais para reuso
            "sample": {
                "x": pool[xcol].astype(float).tolist(),
                "y": pool[ycol].astype(float).tolist(),
            },
        }
        return fig, store, kx, ky, log

    # B) Sliders → redesenha apenas a elipse (usa a amostra guardada no store)

    @app.callback(
        Output("nma-fig-ellipse", "figure", allow_duplicate=True),
        Output("store-nma-step1", "data", allow_duplicate=True),
        Input("nma-nii-sd", "value"),
        Input("nma-area-sd", "value"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _step1_update(kx, ky, store):
        # precisa existir store; se não, não fazemos nada
        if not store:
            fig = _make_step1_figure(None, "NII", "Area", 0, 0, 1, 1)
            return fig, no_update

        xcol = store["xcol"];
        ycol = store["ycol"]
        mu_x = store["mu_x"];
        mu_y = store["mu_y"]
        sd_x = store["sd_x"];
        sd_y = store["sd_y"]

        rx = float(kx) * sd_x
        ry = float(ky) * sd_y

        # reconstrói df a partir do sample
        x = np.asarray(store["sample"]["x"], dtype=float)
        y = np.asarray(store["sample"]["y"], dtype=float)
        df = pd.DataFrame({xcol: x, ycol: y})

        fig = _make_step1_figure(df, xcol, ycol, mu_x, mu_y, rx, ry)

        # reaplica ranges globais guardados
        axis = (store or {}).get("axis")
        if axis and axis.get("x") and axis.get("y"):
            fig.update_layout(xaxis_range=axis["x"], yaxis_range=axis["y"])

        new_store = dict(store)
        new_store.update({"kx": float(kx), "ky": float(ky), "rx": float(rx), "ry": float(ry), "axis": axis})
        return fig, new_store
