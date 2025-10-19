# src/fornma/gui/callbacks/nma_step2.py
from __future__ import annotations
from dash import Input, Output, State, no_update
import dash  # <- necessário para dash.exceptions.PreventUpdate
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from fornma.gui.utils.nma_helpers import (
    load_all_datasets,
    ellipse_trace,
    compute_axis_ranges_from_all,
)
import io, os, pickle
from pathlib import Path
import matplotlib.patches as mp
import io, os, pickle
from pathlib import Path
import matplotlib.patches as mp  # para mp.Ellipse no payload
# para o seletor de pastas (abre o diálogo do SO no backend/local)
import tkinter as tk
from tkinter import filedialog as tkfd


# ---------- utilidades ----------
def _to_num(s: pd.Series) -> pd.Series:
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")
def build_pkl_payload(settings: dict, step1: dict, store_nma: dict) -> dict:
    """
    Constrói um dicionário com o MESMO schema usado no NMA_settings.py (control_parameters.pickle).
    Chaves: name, sd_area, sd_NII, mean_NII, std_NII, mean_a, std_a, circle, graph_limits,
            ellipse, h_x, h_y_up, h_y_down, graph_box, v_upx, v_upy, v_midx, v_midy,
            v_downx, v_downy, v_downx2, fig(None).
    """
    settings = settings or {}
    step1    = step1 or {}
    params   = (store_nma or {}).get("params")

    # --- 1) parâmetros geométricos do Step 1 ---
    mean_NII = float(step1.get("mean_nii", step1.get("mu_x", 0.0)))
    mean_a   = float(step1.get("mean_area", step1.get("mu_y", 0.0)))
    std_NII  = float(step1.get("std_nii",  step1.get("std_x", 1.0)))
    std_a    = float(step1.get("std_a",    step1.get("std_y", 1.0)))
    sd_area  = float(step1.get("sd_area", step1.get("area_sd_factor", 1.0)))   # nº de SD (slider Área)
    sd_NII   = float(step1.get("nii_sd_factor", step1.get("sd_nii", 1.0)))      # nº de SD (slider NII)

    rx = sd_NII * std_NII
    ry = sd_area * std_a

    # --- 2) horizontais (iguais às do NMA_settings.py) ---
    h_x      = [mean_NII - rx, mean_NII + 3.0 * rx]
    h_y_up   = [mean_a + ry, mean_a + ry]
    h_y_down = [mean_a - ry, mean_a - ry]

    # --- 3) elipse (objeto matplotlib) e circle (linspace) ---
    circle  = np.linspace(0, 2 * np.pi, 100)
    ellipse = mp.Ellipse((mean_NII, mean_a),
                         2 * rx,            # width
                         2 * ry,            # height
                         ec='black', fc=None, fill=False)

    # --- 4) limites do gráfico (como calc_area_NII_lims) ---
    # usa função global se disponível, senão degrada para ranges do step1
    try:
        # preferir ±3sd globais + headroom, depois converter ao estilo min/max
        axis = step1.get("axis")
        if not (axis and axis.get("x") and axis.get("y")):
            axis = compute_axis_ranges_from_all(params, k=3.0, headroom=0.0)
        min_a, max_a = float(axis["y"][0]), float(axis["y"][1])
        min_NII, max_NII = float(axis["x"][0]), float(axis["x"][1])
        # pequeno ajuste no "min" (segue ideia do código original menos 1/3 do min)
        min_a = min_a - (min_a / 3.0) if min_a > 0 else min_a
        min_NII = min_NII - (min_NII / 3.0) if min_NII > 0 else min_NII
        graph_limits = (min_a, max_a, min_NII, max_NII)
    except Exception:
        graph_limits = (mean_a - 3*std_a, mean_a + 3*std_a,
                        mean_NII - 3*std_NII, mean_NII + 3*std_NII)

    # --- 5) verticais do usuário (por nome), convertendo para o formato do PKL ---
    thr      = (settings.get("thresholds") or {})
    v_upx_x  = thr.get("v_up",   thr.get("x_right", mean_NII + 1.5*rx))
    v_midx_x = thr.get("v_mid",  thr.get("x_mid",   mean_NII + 1.5*rx))
    v_downx_x= thr.get("v_down", thr.get("x_left",  mean_NII))
    v_downx2_x = thr.get("v_down2", None)

    # y spans iguais ao script original:
    #   v_upy:   [mean_a + sd_area*std_a, mean_a + (2+sd_area)*std_a]
    #   v_midy:  [mean_a - sd_area*std_a, v_upy[0]]
    #   v_downy: [mean_a - (1+sd_area)*std_a, mean_a - sd_area*std_a]
    v_upy   = [int(mean_a + sd_area*std_a),            int(mean_a + (2.0 + sd_area)*std_a)]
    v_midy  = [int(mean_a - sd_area*std_a),            int(v_upy[0])]
    v_downy = [int(mean_a - (1.0 + sd_area)*std_a),    int(mean_a - sd_area*std_a)]

    v_upx    = [float(v_upx_x),    float(v_upx_x)]
    v_midx   = [float(v_midx_x),   float(v_midx_x)]
    v_downx  = [float(v_downx_x),  float(v_downx_x)]
    v_downx2 = [float(v_downx2_x), float(v_downx2_x)] if v_downx2_x is not None else [float(v_upx_x), float(v_upx_x)]

    # --- 6) rótulos/estilo da caixa (igual ao original) ---
    graph_box = dict(boxstyle="round,pad=0.3", fc="#dedcdc", alpha=0.7, ec="#bdbbbb", lw=1)

    # --- 7) nome do dataset (quando houver) ---
    name = (params or {}).get("name") or (step1.get("dataset_name") or "Dataset 1")

    # --- 8) figura matplotlib (no nosso fluxo não existe aqui) ---
    fig = None

    return {
        "name": name,
        "sd_area": sd_area,
        "sd_NII": sd_NII,
        "mean_NII": mean_NII,
        "std_NII": std_NII,
        "mean_a": mean_a,
        "std_a": std_a,
        "circle": circle,
        "graph_limits": graph_limits,
        "ellipse": ellipse,
        "h_x": h_x,
        "h_y_up": h_y_up,
        "h_y_down": h_y_down,
        "graph_box": graph_box,
        "v_upx": v_upx,
        "v_upy": v_upy,
        "v_midx": v_midx,
        "v_midy": v_midy,
        "v_downx": v_downx,
        "v_downy": v_downy,
        "v_downx2": v_downx2,
        "fig": fig,
    }


def _make_step2_figure(
    pool: pd.DataFrame,
    xcol: str,
    ycol: str,
    mu_x: float,
    mu_y: float,
    rx: float,
    ry: float,
    line_xs: list[float] | None,
    axis_ranges: dict | None = None,
    *,
    std_a: float | None = None,   # <- opcional: se vier do Step1, usa as fórmulas originais
    sd_area: float | None = None, # <- opcional: idem
):
    """
    Scatter de todos os datasets + elipse + 2 horizontais fixas (ditadas pela elipse) +
    4 verticais arrastáveis com spans Y em 'andares' (baixo/médio/cima).
    """
    fig = go.Figure()

    # =============================
    # 1) PONTOS (agrupados por ds)
    # =============================
    if pool is not None and not pool.empty:
        for name, g in pool.groupby("__ds__"):
            fig.add_trace(go.Scattergl(
                x=g[xcol], y=g[ycol],
                mode="markers",
                name=str(name),
                marker=dict(size=5, opacity=0.65),
                hovertemplate=f"{xcol}=%{{x}}<br>{ycol}=%{{y}}<extra>{name}</extra>",
            ))
        title = "Adjust NII thresholds by dragging the blue lines"
    else:
        title = "No data to display."

    # =============================
    # 2) HORIZONTAIS = ELIPSE (N/I)
    # =============================
    if ry is None or mu_y is None:
        mu_y = float(mu_y or 0.0)
        ry   = float(ry or 1.0)
    y_inf = float(mu_y) - float(ry)
    y_sup = float(mu_y) + float(ry)

    # Span de X para desenhar horizontais
    if pool is not None and not pool.empty:
        xmin = float(np.nanmin(pool[xcol]))
        xmax = float(np.nanmax(pool[xcol]))
    else:
        xmin = float(mu_x) - float(rx)
        xmax = float(mu_x) + float(rx)

    fig.add_shape(
        type="line", x0=xmin, x1=xmax, y0=y_inf, y1=y_inf,
        xref="x", yref="y", line=dict(color="black", width=3)
    )
    fig.add_shape(
        type="line", x0=xmin, x1=xmax, y0=y_sup, y1=y_sup,
        xref="x", yref="y", line=dict(color="black", width=3)
    )

    # Elipse do Step1
    fig.add_trace(ellipse_trace(float(mu_x or 0), float(mu_y or 0), float(rx or 1), float(ry or 1)))

    # =====================================================
    # 3) SPANS VERTICAIS (3 andares) — iguais ao matplotlib
    # =====================================================
    if std_a is not None and sd_area is not None:
        y_bot0 = float(mu_y) - (1.0 + float(sd_area)) * float(std_a)
        y_top0 = float(mu_y) + (2.0 + float(sd_area)) * float(std_a)
        y_inf  = float(mu_y) - float(sd_area) * float(std_a)
        y_sup  = float(mu_y) + float(sd_area) * float(std_a)
    else:
        y_bot0 = float(mu_y) - 2.0 * float(ry)
        y_top0 = float(mu_y) + 2.0 * float(ry)

    span_down = (y_bot0, y_inf)
    span_mid  = (y_inf,  y_sup)
    span_up   = (y_sup,  y_top0)

    # ===========================================
    # 4) POSIÇÕES INICIAIS EM X (4 verticais)
    # ===========================================
    if not line_xs:
        x_end_ellipse = float(mu_x) + float(rx)
        if axis_ranges and axis_ranges.get("x"):
            x_min_ax, x_max_ax = map(float, axis_ranges["x"])
            x_end_ellipse = max(min(x_end_ellipse, x_max_ax), x_min_ax)

        x_up = x_end_ellipse
        x_mid = x_end_ellipse

        if pool is not None and not pool.empty:
            xs = _to_num(pool[xcol]).to_numpy()
            q10, q90 = np.nanpercentile(xs, [10, 90])
            x_bottom, x_bottom2 = float(q10), float(q90)
        else:
            x_bottom = float(mu_x) - 0.75 * float(rx)
            x_bottom2 = float(mu_x) + 0.75 * float(rx)

        line_xs = [x_bottom, x_mid, x_up, x_bottom2]
    else:
        line_xs = (list(line_xs) + [line_xs[-1]])[:4]
        line_xs[1] = float(line_xs[2])

    x_bottom, x_mid, x_up, x_bottom2 = line_xs[:4]

    # --- Labels dentro das caixas ---
    def mid(a, b):
        return 0.5 * (float(a) + float(b))

    x_left = mid(xmin, float(mu_x))
    x_center = float(mu_x)
    x_right = mid(float(mu_x), xmax)

    y_down_c = mid(y_bot0, y_inf)
    y_mid_c  = mid(y_inf,  y_sup)
    y_up_c   = mid(y_sup,  y_top0)

    labels = [
        dict(x=x_center, y=mu_y,    text="N"),
        dict(x=x_right,  y=y_mid_c, text="I"),
        dict(x=x_left,   y=y_up_c,  text="LR"),
        dict(x=x_right,  y=y_up_c,  text="LI"),
        dict(x=x_center, y=y_down_c,text="S"),
        dict(x=x_left,   y=y_down_c,text="SR"),
        dict(x=x_right,  y=y_down_c,text="SI"),
    ]
    for ann in labels:
        fig.add_annotation(
            x=ann["x"], y=ann["y"], text=ann["text"],
            showarrow=False, font=dict(size=12, color="#374151"),
            xref="x", yref="y", xanchor="center", yanchor="middle",
            align="center", bgcolor="rgba(255,255,255,0.6)",
        )

    # 4 verticais azuis
    fig.add_shape(
        type="line",
        x0=float(x_bottom), x1=float(x_bottom),
        y0=span_down[0], y1=span_down[1],
        xref="x", yref="y",
        line=dict(color="deepskyblue", width=3),
        editable=True,
        name="v_down",
    )
    fig.add_shape(
        type="line",
        x0=float(x_center) + float(rx), x1=float(x_center) + float(rx),
        y0=span_mid[0], y1=span_mid[1],
        xref="x", yref="y",
        line=dict(color="deepskyblue", width=3),
        editable=True,
        name="v_mid",
    )
    fig.add_shape(
        type="line",
        x0=float(x_up), x1=float(x_up),
        y0=span_up[0], y1=span_up[1],
        xref="x", yref="y",
        line=dict(color="deepskyblue", width=3),
        editable=True,
        name="v_up",
    )
    fig.add_shape(
        type="line",
        x0=float(x_bottom2), x1=float(x_bottom2),
        y0=span_down[0], y1=span_down[1],
        xref="x", yref="y",
        line=dict(color="deepskyblue", width=3),
        editable=True,
        name="v_down2",
    )

    # ===========================================
    # 5) LAYOUT / AXES
    # ===========================================
    fig.update_layout(
        autosize=False, width=640, height=640,
        margin=dict(l=60, r=10, t=80, b=60),
        title=dict(text=title, x=0.5, xanchor="center"),
        xaxis_title="NII",
        yaxis_title="Area",
        showlegend=True,
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    if axis_ranges and axis_ranges.get("x") and axis_ranges.get("y"):
        fig.update_layout(xaxis_range=axis_ranges["x"], yaxis_range=axis_ranges["y"])

    return fig



# ---------- registro ----------
def register(app):
    # NEXT → constrói Step 2 usando elipse do Step 1 e eixos ±3sd
    @app.callback(
        Output("store-nma-wizard", "data", allow_duplicate=True),  # <- allow_duplicate aqui
        Output("nma-fig-lines", "figure"),
        Input("nma-step1-next", "n_clicks"),
        State("store-nma", "data"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _go_to_step2(_n, store_nma, step1):
        # 1) dados-base
        params = (store_nma or {}).get("params")
        pool, xcol, ycol, _ = load_all_datasets(params)

        # elipse do step1
        mu_x = (step1 or {}).get("mu_x")
        mu_y = (step1 or {}).get("mu_y")
        rx = (step1 or {}).get("rx")
        ry = (step1 or {}).get("ry")
        std_a = (step1 or {}).get("std_a")
        sd_area = (step1 or {}).get("sd_area")

        # 2) ranges globais
        axis = (step1 or {}).get("axis")
        if not (axis and axis.get("x") and axis.get("y")):
            axis = compute_axis_ranges_from_all(params, k=3.0, headroom=0.05)

        # 3) recuperar linhas salvas
        saved = ((store_nma or {}).get("step2", {}) or {}).get("lines", {})

        def _xs_from_saved(saved_dict):
            keys = ["v_down", "v_mid", "v_up", "v_down2"]
            xs = []
            for k in keys:
                x = (saved_dict.get(k) or {}).get("x")
                xs.append(float(x) if x is not None else None)
            if xs[2] is not None:
                xs[1] = xs[2]
            return xs if any(v is not None for v in xs) else None

        line_xs = _xs_from_saved(saved)

        # 4) figura
        fig = _make_step2_figure(
            pool=pool,
            xcol=xcol, ycol=ycol,
            mu_x=mu_x, mu_y=mu_y,
            rx=rx, ry=ry,
            line_xs=line_xs,
            axis_ranges=axis,
            std_a=std_a, sd_area=sd_area,
        )

        # 5) avança wizard para step 2
        return {"step": 2}, fig

    # trava o Y das verticais quando o usuário arrasta (snap por "andar")
    @app.callback(
        Output("nma-fig-lines", "figure", allow_duplicate=True),
        Output("store-nma", "data", allow_duplicate=True),
        Input("nma-fig-lines", "relayoutData"),
        State("nma-fig-lines", "figure"),
        State("store-nma-step1", "data"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _lock_line_y(relayout, fig, step1, store_nma):
        if not relayout or not fig:
            return no_update, no_update

        store_nma = store_nma or {}
        step1 = step1 or {}

        mean_a = step1.get("mean_a", step1.get("mu_y"))
        ry = step1.get("ry")
        if ry is None:
            std_a = step1.get("std_a")
            sd_area = step1.get("sd_area")
            if std_a is not None and sd_area is not None:
                try:
                    ry = float(sd_area) * float(std_a)
                except Exception:
                    ry = None

        if mean_a is None or ry is None:
            return no_update, no_update

        mean_a = float(mean_a)
        ry = float(ry)

        std_a = step1.get("std_a")
        sd_area = step1.get("sd_area")
        if std_a is not None and sd_area is not None:
            try:
                std_a = float(std_a)
                sd_area = float(sd_area)
                y_inf = mean_a - sd_area * std_a
                y_sup = mean_a + sd_area * std_a
                y_bot0 = mean_a - (1.0 + sd_area) * std_a
                y_top0 = mean_a + (2.0 + sd_area) * std_a
            except Exception:
                y_inf = mean_a - ry
                y_sup = mean_a + ry
                y_bot0 = mean_a - 2.0 * ry
                y_top0 = mean_a + 2.0 * ry
        else:
            y_inf = mean_a - ry
            y_sup = mean_a + ry
            y_bot0 = mean_a - 2.0 * ry
            y_top0 = mean_a + 2.0 * ry

        spans = {
            "v_up": (y_sup, y_top0),
            "v_mid": (y_inf, y_sup),
            "v_down": (y_bot0, y_inf),
            "v_down2": (y_bot0, y_inf),
        }

        layout = fig.get("layout", {}) or {}
        shapes = [dict(s) for s in (layout.get("shapes") or [])]
        if not shapes:
            return no_update, no_update

        xaxis = layout.get("xaxis", {}) or {}
        x_range = xaxis.get("range")
        x_min_ax = x_max_ax = None
        if isinstance(x_range, (list, tuple)) and len(x_range) == 2:
            try:
                x_min_ax, x_max_ax = map(float, x_range)
            except Exception:
                x_min_ax = x_max_ax = None

        changed = False
        for key, val in (relayout or {}).items():
            if not key.startswith("shapes["):
                continue
            try:
                idx = int(key.split("[", 1)[1].split("]", 1)[0])
            except Exception:
                continue
            if idx < 0 or idx >= len(shapes):
                continue

            s = shapes[idx]
            role = s.get("name")
            if role not in spans:
                continue

            if key.endswith(".x0") or key.endswith(".x1"):
                try:
                    new_x = float(val)
                except Exception:
                    continue

                if x_min_ax is not None and x_max_ax is not None:
                    new_x = min(max(new_x, x_min_ax), x_max_ax)

                s["x0"] = new_x
                s["x1"] = new_x

                y0, y1 = spans[role]
                s["y0"] = float(y0)
                s["y1"] = float(y1)
                s["yref"] = "y"

                shapes[idx] = s
                changed = True

        if not changed:
            return no_update, no_update

        new_fig = dict(fig)
        new_layout = dict(layout)
        new_layout["shapes"] = shapes
        new_fig["layout"] = new_layout

        lines_data = {}
        for s in shapes:
            name = s.get("name")
            if not name:
                continue
            line_meta = s.get("line", {}) or {}
            if line_meta.get("color") != "deepskyblue":
                continue
            try:
                lines_data[name] = {
                    "x": float(s["x0"]),
                    "y0": float(s["y0"]),
                    "y1": float(s["y1"]),
                }
            except Exception:
                pass

        new_store = dict(store_nma)
        step2_ns = dict(new_store.get("step2", {}) or {})
        step2_ns["lines"] = lines_data
        new_store["step2"] = step2_ns

        return new_fig, new_store

    # Alterna visibilidade dos panes
    @app.callback(
        Output("nma-step1-pane", "style", allow_duplicate=True),
        Output("nma-step2-pane", "style", allow_duplicate=True),
        Output("nma-result-pane", "style", allow_duplicate=True),
        Input("store-nma-wizard", "data"),
        prevent_initial_call=True,
    )
    def _toggle_panes(data):
        step = (data or {}).get("step", 1)
        show = {"display": "block"}
        hide = {"display": "none"}
        if step == 1:  return show, hide, hide
        if step == 2:  return hide, show, hide
        return hide, hide, show  # step == 3

    # Step2 → Previous
    @app.callback(
        Output("store-nma-wizard", "data", allow_duplicate=True),
        Input("nma-step2-prev", "n_clicks"),
        prevent_initial_call=True,
    )
    def _step2_prev(n):
        if not n:
            raise dash.exceptions.PreventUpdate
        return {"step": 1}

    # Step2 → Complete: salva thresholds e vai para Step 3
    @app.callback(
        Output("store-nma-settings", "data"),
        Output("store-nma-wizard", "data", allow_duplicate=True),
        Input("nma-step2-complete", "n_clicks"),
        State("nma-fig-lines", "figure"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _step2_complete_save(n, fig, step1):
        if not n:
            raise dash.exceptions.PreventUpdate

        # --- extrai thresholds das shapes do gráfico (por NOME) ---
        shapes = (fig or {}).get("layout", {}).get("shapes", []) or []

        # verticais (pelos nomes definidos no Step 2)
        vmap = {"v_down": None, "v_mid": None, "v_up": None, "v_down2": None}
        for s in shapes:
            if not isinstance(s, dict):
                continue
            if s.get("type") != "line":
                continue
            name = s.get("name")
            # é vertical se x0 == x1
            try:
                x0 = float(s.get("x0", "nan"))
                x1 = float(s.get("x1", "inf"))
            except Exception:
                continue
            if name in vmap and x0 == x1:
                vmap[name] = x0

        # horizontais pretas (duas) — usa igualdade de y0==y1
        hlines = [s for s in shapes
                  if isinstance(s, dict) and s.get("type") == "line"
                  and str(s.get("y0")) is not None and str(s.get("y1")) is not None
                  and float(s.get("y0", 0)) == float(s.get("y1", 1))]
        ys = sorted({float(s["y0"]) for s in hlines}) if hlines else []
        y_low, y_high = (ys[0], ys[-1]) if len(ys) >= 2 else (None, None)

        # também salva centro/DPs vindos do Step 1 (se existirem)
        step1 = step1 or {}
        settings = {
            "nii_mu": step1.get("mean_nii"),
            "nii_sd": step1.get("std_nii"),
            "area_mu": step1.get("mean_area"),
            "area_sd": step1.get("std_area"),
            "k_nii": step1.get("nii_sd_factor"),
            "k_area": step1.get("area_sd_factor"),
            "thresholds": {
                # nomes das verticais (para reuso 1:1 no preview)
                "v_down": vmap["v_down"],
                "v_mid": vmap["v_mid"],
                "v_up": vmap["v_up"],
                "v_down2": vmap["v_down2"],
                # agregados (retrocompatível com usos anteriores)
                "x_left": vmap["v_down"],
                "x_mid": vmap["v_mid"],
                "x_right": vmap["v_up"],
                # horizontais
                "y_low": y_low,
                "y_high": y_high,
            },
        }

        # avança para o Step 3 (resultado/preview)
        return settings, {"step": 3}

    @app.callback(
        Output("nma-fig-preview", "figure"),
        Input("store-nma-settings", "data"),
        State("store-nma-step1", "data"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _build_preview(settings, step1, store_nma):
        import plotly.express as px
        import plotly.graph_objects as go

        step1 = step1 or {}
        settings = settings or {}
        thr = settings.get("thresholds", {}) or {}

        # ==== DADOS (só controles) ====
        df_json = step1.get("df_json")
        if df_json is not None:
            df = pd.read_json(df_json, orient="split")
            xcol = "NII" if "NII" in df.columns else (step1.get("col_x") or "NII")
            ycol = "Area" if "Area" in df.columns else (step1.get("col_y") or "Area")
        else:
            params = (store_nma or {}).get("params")
            pool, xcol, ycol, _ = load_all_datasets(params)
            df = pool.copy() if pool is not None else pd.DataFrame(columns=[xcol or "NII", ycol or "Area"])

        # normaliza
        rename_map = {}
        if "NII" not in df.columns and xcol in df.columns:  rename_map[xcol] = "NII"
        if "Area" not in df.columns and ycol in df.columns: rename_map[ycol] = "Area"
        if step1.get("col_x_tmp") in df.columns:            rename_map[step1["col_x_tmp"]] = "NII"
        if step1.get("col_y_tmp") in df.columns:            rename_map[step1["col_y_tmp"]] = "Area"
        if rename_map: df = df.rename(columns=rename_map)

        # filtra controles
        control_label = str(step1.get("control_label", "control")).lower()
        cond_col = next((c for c in df.columns if c.lower() in ("condition", "cond", "group", "grupo")), None)
        if cond_col:
            m = (df[cond_col].astype(str).str.lower().isin(["control", "controle", control_label])
                 | df[cond_col].astype(str).str.contains("control", case=False, regex=False))
            df_plot = df[m].copy()
        else:
            df_plot = df.copy()

        # ==== PARÂMETROS GEOMÉTRICOS ====
        mu_x = float(step1.get("mu_x") or step1.get("mean_nii") or 0.0)
        mu_y = float(step1.get("mu_y") or step1.get("mean_area") or 0.0)
        rx = float(step1.get("rx") or (step1.get("std_nii") or 1.0) * float(step1.get("nii_sd_factor", 1.0)))
        # ry: usa regra com std_a/sd_area se houver
        if isinstance(step1.get("std_a"), (int, float)) and isinstance(step1.get("sd_area"), (int, float)):
            ry = float(step1["sd_area"]) * float(step1["std_a"])
            y_low = mu_y - ry
            y_high = mu_y + ry
            y_bot0 = mu_y - (1.0 + float(step1["sd_area"])) * float(step1["std_a"])
            y_top0 = mu_y + (2.0 + float(step1["sd_area"])) * float(step1["std_a"])
        else:
            ry = float(step1.get("ry") or 1.0)
            y_low = mu_y - ry
            y_high = mu_y + ry
            y_bot0 = mu_y - 2.0 * ry
            y_top0 = mu_y + 2.0 * ry

        # sobrepõe valores do usuário (se existem)
        y_low = float(thr.get("y_low", y_low)) if thr.get("y_low") is not None else y_low
        y_high = float(thr.get("y_high", y_high)) if thr.get("y_high") is not None else y_high

        x_v_down = thr.get("v_down", thr.get("x_left"))
        x_v_mid = thr.get("v_mid", thr.get("x_mid"))
        x_v_up = thr.get("v_up", thr.get("x_right"))
        # fallback do x_v_mid = fim da elipse
        if x_v_mid is None: x_v_mid = mu_x + rx

        # ==== FIG ====
        fig = px.scatter(df_plot if not df_plot.empty else pd.DataFrame({"NII": [], "Area": []}),
                         x="NII", y="Area", opacity=0.75)
        fig.update_layout(
            margin=dict(l=60, r=10, t=40, b=60),
            xaxis_title="NII",
            yaxis_title="Area",
            showlegend=False,
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        # ranges do step1 (se houver)
        axis = step1.get("axis")
        if axis and axis.get("x") and axis.get("y"):
            fig.update_layout(xaxis_range=axis["x"], yaxis_range=axis["y"])

        # elipse
        fig.add_trace(ellipse_trace(mu_x, mu_y, rx, ry))

        # horizontais pretas (largura 3)
        xr = fig.layout.xaxis.range or [
            float(df_plot["NII"].min()) if "NII" in df_plot and not df_plot.empty else mu_x - rx * 2,
            float(df_plot["NII"].max()) if "NII" in df_plot and not df_plot.empty else mu_x + rx * 2,
        ]
        x0, x1 = float(xr[0]), float(xr[1])
        for y in [y_low, y_high]:
            fig.add_shape(type="line", x0=x0, x1=x1, y0=float(y), y1=float(y),
                          xref="x", yref="y", line=dict(color="black", width=3))

        # verticais em PRETO (mesma espessura das horizontais) com spans por “andar”
        spans = [(y_bot0, y_low), (y_low, y_high), (y_high, y_top0)]
        x_v_down = thr.get("v_down", thr.get("x_left"))
        x_v_mid = thr.get("v_mid", thr.get("x_mid"))
        x_v_up = thr.get("v_up", thr.get("x_right"))
        x_v_down2 = thr.get("v_down2", None)  # <- nova (segunda do painel inferior)
        if x_v_mid is None:
            x_v_mid = mu_x + rx  # fallback: fim da elipse

        # v_down  (andar inferior)
        if x_v_down is not None:
            y0, y1 = spans[0]
            fig.add_shape(type="line",
                          x0=float(x_v_down), x1=float(x_v_down),
                          y0=float(y0), y1=float(y1),
                          xref="x", yref="y",
                          line=dict(color="black", width=3))

        # v_mid   (andar do meio)
        if x_v_mid is not None:
            y0, y1 = spans[1]
            fig.add_shape(type="line",
                          x0=float(x_v_mid), x1=float(x_v_mid),
                          y0=float(y0), y1=float(y1),
                          xref="x", yref="y",
                          line=dict(color="black", width=3))

        # v_up    (andar superior)
        if x_v_up is not None:
            y0, y1 = spans[2]
            fig.add_shape(type="line",
                          x0=float(x_v_up), x1=float(x_v_up),
                          y0=float(y0), y1=float(y1),
                          xref="x", yref="y",
                          line=dict(color="black", width=3))

        # v_down2 (segunda do andar inferior)
        if x_v_down2 is not None:
            y0, y1 = spans[0]
            fig.add_shape(type="line",
                          x0=float(x_v_down2), x1=float(x_v_down2),
                          y0=float(y0), y1=float(y1),
                          xref="x", yref="y",
                          line=dict(color="black", width=3))

        # ===== Rótulos (caixas) SI, S, SR, N, LR, LI, I =====
        # centros para posicionamento
        xr = fig.layout.xaxis.range or [
            float(df_plot["NII"].min()) if "NII" in df_plot and not df_plot.empty else mu_x - rx * 2,
            float(df_plot["NII"].max()) if "NII" in df_plot and not df_plot.empty else mu_x + rx * 2,
        ]
        xmin, xmax = float(xr[0]), float(xr[1])

        def mid(a, b):
            return 0.5 * (float(a) + float(b))

        x_left_c = mid(xmin, mu_x)
        x_center_c = mu_x
        x_right_c = mid(mu_x, xmax)
        y_down_c = mid(y_bot0, y_low)
        y_mid_c = mid(y_low, y_high)
        y_up_c = mid(y_high, y_top0)

        labels = [
            ("SR", x_left_c, y_down_c),
            ("S", x_center_c, y_down_c),
            ("SI", x_right_c, y_down_c),
            ("N", x_center_c, y_mid_c),
            ("LR", x_left_c, y_up_c),
            ("LI", x_right_c, y_up_c),
            ("I", x_right_c, y_mid_c),
        ]
        for text, x, y in labels:
            fig.add_annotation(
                x=x, y=y, text=text,
                xref="x", yref="y",
                showarrow=False,
                xanchor="center", yanchor="middle",
                font=dict(size=12, color="#111827"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#111827", borderwidth=1, borderpad=2,
            )

        return fig


    # abre o painel de SAVE quando clicar em "Save settings"
    @app.callback(
        Output("nma-save-panel", "style", allow_duplicate=True),
        Input("nma-save-open", "n_clicks"),
        prevent_initial_call=True,
    )
    def _open_save_panel(n):
        if not n:
            raise dash.exceptions.PreventUpdate
        return {"display": "block"}  # já centralizamos via estilos do container

    # botão "Browse…" → abre seletor de pastas do sistema e preenche o input
    @app.callback(
        Output("nma-save-path", "value", allow_duplicate=True),
        Input("nma-save-browse", "n_clicks"),
        prevent_initial_call=True,
    )
    def _browse_folder(n):
        if not n:
            raise dash.exceptions.PreventUpdate
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = tkfd.askdirectory(title="Escolha a pasta para salvar as configurações")
            root.destroy()
            if not path:
                raise dash.exceptions.PreventUpdate
            return path
        except Exception:
            # Se falhar (ex.: ambiente headless), não apaga o campo
            raise dash.exceptions.PreventUpdate

    # "Save now" → grava o pickle no disco
    @app.callback(
        Output("nma-save-status", "children", allow_duplicate=True),
        Input("nma-save-do", "n_clicks"),
        State("nma-save-path", "value"),
        State("store-nma-settings", "data"),
        State("store-nma-step1", "data"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _save_settings_to_disk(n, save_dir, settings, step1, store_nma):
        if not n:
            raise dash.exceptions.PreventUpdate

        if not save_dir or not str(save_dir).strip():
            return "⚠️ Informe (ou escolha com Browse) uma pasta válida."

        p = Path(str(save_dir)).expanduser().resolve()
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return f"❌ Não foi possível criar/acessar a pasta: {e}"

        try:
            payload = build_pkl_payload(settings or {}, step1 or {}, store_nma or {})
            out_path = p / "control_parameters.pickle"
            with open(out_path, "wb") as f:
                pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            return f"❌ Erro ao salvar: {e}"

        return f"✅ Salvo em: {out_path}"









