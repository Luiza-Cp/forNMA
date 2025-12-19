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
# Adicione esta linha no início do arquivo nma_step2.py (após os imports)
__all__ = ['register', '_build_preview', 'build_pkl_payload']

def _extract_y_thresholds(fig_lines: dict):
    if not fig_lines or "layout" not in fig_lines:
        return None, None
    ys = []
    for shp in (fig_lines["layout"].get("shapes") or []):
        if shp.get("type") == "line" and shp.get("y0") == shp.get("y1"):
            try:
                ys.append(float(shp["y0"]))
            except Exception:
                pass
    if not ys:
        return None, None
    ys = sorted(ys)
    return ys[0], ys[-1]  # low, high

def _extract_verticals(fig_lines: dict):
    # Lê linhas azuis por "name" (v_down, v_mid, v_up, v_down2); se não houver, deixa None
    vmap = {"v_down": None, "v_mid": None, "v_up": None, "v_down2": None}
    if not fig_lines or "layout" not in fig_lines:
        return vmap
    for s in (fig_lines["layout"].get("shapes") or []):
        if s.get("type") == "line" and s.get("line", {}).get("color") == "deepskyblue":
            name = s.get("name")
            if name in vmap:
                try:
                    vmap[name] = float(s["x0"])
                except Exception:
                    pass
    return vmap

# ---------- utilidades ----------
def _to_num(s: pd.Series) -> pd.Series:
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def build_pkl_payload(settings: dict, step1: dict, store_nma: dict) -> dict:
    """
    Constrói um dicionário com o MESMO schema usado pelo script original (control_parameters.pickle).
    """
    print("\n=== [DEBUG BUILD_PKL] INICIANDO ===")

    settings = settings or {}
    step1 = step1 or {}
    store_nma = store_nma or {}
    params = store_nma.get("params")

    # --- 1) DEBUG: Verificar valores recebidos ---
    print("Valores recebidos do step1:")
    print(f"  mu_x: {step1.get('mu_x')}")
    print(f"  mu_y: {step1.get('mu_y')}")
    print(f"  sd_x (std_NII real): {step1.get('sd_x')}")
    print(f"  sd_y (std_a real): {step1.get('sd_y')}")
    print(f"  kx: {step1.get('kx')}")
    print(f"  ky: {step1.get('ky')}")
    print(f"  rx: {step1.get('rx')}")
    print(f"  ry: {step1.get('ry')}")

    # --- 2) parâmetros básicos do Step 1 ---
    # Usar as chaves CORRETAS que sabemos existir no step1
    mean_NII = float(step1.get("mu_x", 0.0))
    mean_a = float(step1.get("mu_y", 0.0))

    # OBTER DESVIO PADRÃO DO CONTROLE - usar sd_x e sd_y!
    std_NII = float(step1.get("sd_x", 1.0))  # Este é o std_NII correto do controle
    std_a = float(step1.get("sd_y", 1.0))  # Este é o std_a correto do controle

    # Fatores dos sliders
    kx = float(step1.get("kx", 1.0))  # fator do slider NII
    ky = float(step1.get("ky", 1.0))  # fator do slider Area

    print(f"\nValores extraídos (corretos):")
    print(f"  std_NII (de sd_x): {std_NII}")
    print(f"  std_a (de sd_y): {std_a}")
    print(f"  kx: {kx}, ky: {ky}")

    # --- 3) thresholds vindos do Step 2 ---
    thr = (settings.get("thresholds") or {})

    # --- 4) Calcular rx (horizontal) e ry (vertical) ---
    # rx = fator_NII * std_NII (do controle)
    rx = kx * std_NII

    # ry inicial = fator_Area * std_a (do controle)
    ry_initial = ky * std_a

    print(f"\nValores calculados inicialmente:")
    print(f"  rx (kx * std_NII): {kx} * {std_NII} = {rx}")
    print(f"  ry_initial (ky * std_a): {ky} * {std_a} = {ry_initial}")

    # --- 5) Ajustar se Step 2 tem thresholds horizontais ---
    y_low = thr.get("y_low")
    y_high = thr.get("y_high")

    if y_low is not None and y_high is not None:
        try:
            y_low_f = float(y_low)
            y_high_f = float(y_high)

            # Recalcular mean_a e ry baseado nas linhas horizontais do Step 2
            mean_a = (y_high_f + y_low_f) / 2.0
            ry = abs(y_high_f - y_low_f) / 2.0

            # Ajustar ky para que ky * std_a = ry (para manter consistência)
            if std_a != 0:
                ky = ry / std_a
            else:
                ky = 1.0

            print(f"\nAjustado por thresholds do Step 2:")
            print(f"  y_low: {y_low_f}, y_high: {y_high_f}")
            print(f"  Novo mean_a: {mean_a}")
            print(f"  Novo ry: {ry}")
            print(f"  ky ajustado: {ky} (era: {step1.get('ky')})")

        except Exception as e:
            print(f"Erro ao ajustar por thresholds: {e}")
            ry = ry_initial
    else:
        ry = ry_initial

    # --- 6) sd_NII e sd_area são os fatores (kx e ky) ---
    sd_NII = kx
    sd_area = ky

    print(f"\nValores finais para pickle:")
    print(f"  sd_NII: {sd_NII}")
    print(f"  sd_area: {sd_area}")
    print(f"  std_NII: {std_NII}")
    print(f"  std_a: {std_a}")
    print(f"  mean_NII: {mean_NII}")
    print(f"  mean_a: {mean_a}")
    print(f"  rx final (sd_NII * std_NII): {sd_NII * std_NII}")
    print(f"  ry final (sd_area * std_a): {sd_area * std_a}")

    # --- 7) horizontais ---
    # Obter limites do gráfico para h_x cobrir toda largura
    try:
        axis = step1.get("axis")
        if not (axis and axis.get("x") and axis.get("y")):
            axis = compute_axis_ranges_from_all(params, k=3.0, headroom=0.0)

        min_a, max_a = float(axis["y"][0]), float(axis["y"][1])
        min_NII, max_NII = float(axis["x"][0]), float(axis["x"][1])

        if min_a > 0:
            min_a -= min_a / 3.0
        if min_NII > 0:
            min_NII -= min_NII / 3.0

        graph_limits = (min_a, max_a, min_NII, max_NII)
    except Exception:
        graph_limits = (
            mean_a - 3 * std_a,
            mean_a + 3 * std_a,
            mean_NII - 3 * std_NII,
            mean_NII + 3 * std_NII,
        )

    # h_x deve cobrir toda a largura do gráfico
    min_NII = graph_limits[2]
    max_NII = graph_limits[3]
    h_x = [min_NII, max_NII]

    h_y_up = [mean_a + ry, mean_a + ry]
    h_y_down = [mean_a - ry, mean_a - ry]

    print(f"\nLinhas horizontais:")
    print(f"  h_x (largura total): [{min_NII:.2f}, {max_NII:.2f}]")
    print(f"  h_y_down: {h_y_down}")
    print(f"  h_y_up: {h_y_up}")

    # --- 8) elipse + circle ---
    circle = np.linspace(0, 2 * np.pi, 100)
    ellipse = {
        "center": (mean_NII, mean_a),
        "width": 2 * rx,
        "height": 2 * ry,
        "angle": 0
    }

    print(f"\nElipse:")
    print(f"  centro: ({mean_NII}, {mean_a})")
    print(f"  largura (2*rx): {2 * rx}")
    print(f"  altura (2*ry): {2 * ry}")

    # --- 9) verticais ---
    v_downx_x = thr.get("v_down", thr.get("x_left", mean_NII))
    v_midx_x = thr.get("v_mid", thr.get("x_mid", mean_NII + 0.75 * rx))
    v_upx_x = thr.get("v_up", thr.get("x_right", mean_NII + 1.5 * rx))
    v_downx2_x = thr.get("v_down2", None)

    v_downx_x = float(v_downx_x) if v_downx_x is not None else float(mean_NII)
    v_midx_x = float(v_midx_x) if v_midx_x is not None else float(mean_NII + 0.75 * rx)
    v_upx_x = float(v_upx_x) if v_upx_x is not None else float(mean_NII + 1.5 * rx)

    if v_downx2_x is not None:
        v_downx2_x = float(v_downx2_x)
    else:
        v_downx2_x = v_upx_x

    # spans em Y (3 andares)
    # Usando o ry ajustado para consistência
    y_bot0 = mean_a - 2.0 * ry
    y_inf = mean_a - ry
    y_sup = mean_a + ry
    y_top0 = mean_a + 2.0 * ry

    v_upy = [y_sup, y_top0]
    v_midy = [y_inf, y_sup]
    v_downy = [y_bot0, y_inf]

    v_downx = [v_downx_x, v_downx_x]
    v_midx = [v_midx_x, v_midx_x]
    v_upx = [v_upx_x, v_upx_x]
    v_downx2 = [v_downx2_x, v_downx2_x]

    print(f"\nLinhas verticais:")
    print(f"  v_downx: {v_downx} (x={v_downx_x})")
    print(f"  v_midx: {v_midx} (x={v_midx_x})")
    print(f"  v_upx: {v_upx} (x={v_upx_x})")
    print(f"  v_downx2: {v_downx2} (x={v_downx2_x})")
    print(f"  Spans Y: v_upy={v_upy}, v_midy={v_midy}, v_downy={v_downy}")

    # --- 10) box style ---
    graph_box = dict(
        boxstyle="round,pad=0.3",
        fc="#dedcdc",
        alpha=0.7,
        ec="#bdbbbb",
        lw=1,
    )

    # --- 11) nome / fig ---
    name = (params or {}).get("name") or (step1.get("dataset_name") or "Dataset 1")
    fig = None

    # --- 12) payload final ---
    payload = {
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

        # escalares auxiliares
        "x_left": v_downx_x,
        "x_mid": v_midx_x,
        "x_right": v_upx_x,

        "fig": fig,
    }

    print("\n=== [DEBUG BUILD_PKL] FINALIZADO ===")
    print(f"Número de chaves no payload: {len(payload)}")
    print("====================================\n")

    return payload

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
        print("\n=== [DEBUG BUILD_PREVIEW] INICIANDO ===")
        print(f"Step1 tem 'from_pickle': {step1.get('from_pickle') if step1 else 'No step1'}")

        step1 = step1 or {}
        settings = settings or {}
        thr = settings.get("thresholds", {}) or {}

        # VERIFICAÇÃO CHAVE: Se veio do pickle
        if step1.get("from_pickle"):
            print("[DEBUG BUILD_PREVIEW] Usando parâmetros de pickle carregados")

            # 1) Usar parâmetros diretamente do step1 (que vieram do pickle)
            mu_x = float(step1.get("mu_x", 0.0))
            mu_y = float(step1.get("mu_y", 0.0))
            rx = float(step1.get("rx", 1.0))
            ry = float(step1.get("ry", 1.0))
            kx = float(step1.get("kx", 1.0))
            ky = float(step1.get("ky", 1.0))

            # 2) Pegar thresholds do pickle (armazenados em step1 ou settings)
            pickle_thresholds = step1.get("pickle_thresholds", {})
            if pickle_thresholds:
                thr = pickle_thresholds

            print(f"[DEBUG BUILD_PREVIEW] Parâmetros do pickle: mu_x={mu_x}, mu_y={mu_y}, rx={rx}, ry={ry}")
            print(f"[DEBUG BUILD_PREVIEW] Thresholds: {thr}")

            # 3) Axis do step1 ou criar um padrão
            axis = step1.get("axis")
            if not axis or not axis.get("x") or not axis.get("y"):
                axis = {
                    "x": [mu_x - 3 * rx, mu_x + 3 * rx],
                    "y": [mu_y - 3 * ry, mu_y + 3 * ry]
                }

            # 4) Tentar carregar dados atuais para o scatter
            df_plot = pd.DataFrame(columns=["NII", "Area", "__ds__"])
            try:
                params = (store_nma or {}).get("params")
                if params:
                    pool, xcol, ycol, _ = load_all_datasets(params)
                    if pool is not None and not pool.empty:
                        rename_map = {}
                        if "NII" not in pool.columns and xcol in pool.columns:
                            rename_map[xcol] = "NII"
                        if "Area" not in pool.columns and ycol in pool.columns:
                            rename_map[ycol] = "Area"
                        if rename_map:
                            pool = pool.rename(columns=rename_map)

                        # Converter para float para garantir
                        for col in ["NII", "Area"]:
                            if col in pool.columns:
                                pool[col] = pd.to_numeric(pool[col], errors='coerce')

                        # Manter apenas as colunas necessárias
                        cols_to_keep = ["NII", "Area"]
                        if "__ds__" in pool.columns:
                            cols_to_keep.append("__ds__")

                        df_plot = pool[cols_to_keep].dropna().copy()
                        print(f"[DEBUG BUILD_PREVIEW] Carregados {len(df_plot)} pontos dos datasets atuais")
            except Exception as e:
                print(f"[DEBUG BUILD_PREVIEW] Erro ao carregar dados: {e}")
                # Continua com DataFrame vazio

            # 5) Criar figura básica com cores por dataset
            import plotly.express as px
            import plotly.graph_objects as go

            if not df_plot.empty:
                # Verificar se temos a coluna de dataset (__ds__)
                if "__ds__" in df_plot.columns:
                    # Contar quantos datasets únicos temos
                    unique_datasets = df_plot["__ds__"].nunique()
                    print(f"[DEBUG BUILD_PREVIEW] Plotando {len(df_plot)} pontos de {unique_datasets} datasets")

                    # Usar cores diferentes por dataset
                    fig = px.scatter(
                        df_plot,
                        x="NII",
                        y="Area",
                        color="__ds__",  # Colorir por dataset
                        opacity=0.75,
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        title=f"NMA Preview ({unique_datasets} datasets)",
                        labels={"__ds__": "Dataset"}  # Renomear legenda
                    )
                else:
                    # Se não tiver, usar a mesma cor para todos
                    fig = px.scatter(
                        df_plot,
                        x="NII",
                        y="Area",
                        opacity=0.75,
                        title="NMA Preview (datasets não identificados)"
                    )
            else:
                # Figura vazia com eixos apropriados
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[], y=[], mode='markers'))
                fig.update_layout(
                    title="NMA Preview (nenhum dado disponível)",
                    xaxis_title="NII",
                    yaxis_title="Area"
                )

            # 6) Adicionar elipse do pickle
            fig.add_trace(ellipse_trace(mu_x, mu_y, rx, ry))

            # 7) Adicionar thresholds horizontais (do pickle)
            y_low = thr.get("y_low")
            y_high = thr.get("y_high")

            # Se não tiver thresholds no pickle, usar baseado na elipse
            if y_low is None or y_high is None:
                y_low = mu_y - ry
                y_high = mu_y + ry

            # Desenhar horizontais
            xr = axis["x"]
            x0, x1 = float(xr[0]), float(xr[1])

            for y in [y_low, y_high]:
                fig.add_shape(
                    type="line",
                    x0=x0, x1=x1, y0=float(y), y1=float(y),
                    xref="x", yref="y",
                    line=dict(color="black", width=3)
                )

            # 8) Adicionar thresholds verticais (do pickle)
            # Spans Y baseados na elipse
            y_bot0 = mu_y - 2.0 * ry
            y_top0 = mu_y + 2.0 * ry
            spans = [(y_bot0, y_low), (y_low, y_high), (y_high, y_top0)]

            # Verticais do pickle
            x_v_down = thr.get("v_down", thr.get("x_left"))
            x_v_mid = thr.get("v_mid", thr.get("x_mid"))
            x_v_up = thr.get("v_up", thr.get("x_right"))
            x_v_down2 = thr.get("v_down2", None)

            # Fallbacks razoáveis se não existirem no pickle
            if x_v_mid is None:
                x_v_mid = mu_x + rx
            if x_v_up is None:
                x_v_up = mu_x + 1.5 * rx
            if x_v_down is None:
                x_v_down = mu_x - 0.75 * rx
            if x_v_down2 is None:
                x_v_down2 = mu_x + 0.75 * rx

            # Desenhar verticais
            verticals = [
                ("v_down", x_v_down, spans[0]),
                ("v_mid", x_v_mid, spans[1]),
                ("v_up", x_v_up, spans[2]),
                ("v_down2", x_v_down2, spans[0])
            ]

            for name, x_val, (y0, y1) in verticals:
                if x_val is not None:
                    fig.add_shape(
                        type="line",
                        x0=float(x_val), x1=float(x_val),
                        y0=float(y0), y1=float(y1),
                        xref="x", yref="y",
                        line=dict(color="black", width=3)
                    )

            # 9) Adicionar rótulos das regiões
            def mid(a, b):
                return 0.5 * (float(a) + float(b))

            x_left_c = mid(x0, mu_x)
            x_center_c = mu_x
            x_right_c = mid(mu_x, x1)
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

            # 10) Configurar layout final
            fig.update_layout(
                margin=dict(l=60, r=10, t=40, b=60),
                xaxis_title="NII",
                yaxis_title="Area",
                showlegend=True,  # Mostrar legenda
                legend=dict(
                    title="Datasets",
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.02,
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="LightGrey",
                    borderwidth=1
                ),
                title="NMA Preview (settings carregadas do arquivo)"
            )

            if axis and axis.get("x") and axis.get("y"):
                fig.update_layout(xaxis_range=axis["x"], yaxis_range=axis["y"])

            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True)

            print("[DEBUG BUILD_PREVIEW] Preview gerado a partir do pickle")
            return fig

        # ============================================================
        # CASO NORMAL (quando NÃO veio do pickle)
        # ============================================================
        else:
            print("[DEBUG BUILD_PREVIEW] Modo normal (não veio do pickle)")

            import plotly.express as px
            import plotly.graph_objects as go

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

            # --- GARANTE COERÊNCIA ELIPSE x THRESHOLDS HORIZONTAIS ---
            # Se temos y_low e y_high vindos do Step 2, recalculamos ry (e opcionalmente mu_y)
            try:
                if y_low is not None and y_high is not None:
                    y_low_f = float(y_low)
                    y_high_f = float(y_high)

                    # raio vertical = metade da distância entre as horizontais
                    ry = abs(y_high_f - y_low_f) / 2.0

                    # centro vertical = meio entre as horizontais
                    mu_y = (y_high_f + y_low_f) / 2.0

                    # atualiza também os limites dos "andares" para ficar tudo consistente
                    y_low = mu_y - ry
                    y_high = mu_y + ry
                    y_bot0 = mu_y - 2.0 * ry
                    y_top0 = mu_y + 2.0 * ry
            except Exception:
                # se der algum problema numérico, cai fora silenciosamente
                pass

            x_v_down = thr.get("v_down", thr.get("x_left"))
            x_v_mid = thr.get("v_mid", thr.get("x_mid"))
            x_v_up = thr.get("v_up", thr.get("x_right"))
            # fallback do x_v_mid = fim da elipse
            if x_v_mid is None: x_v_mid = mu_x + rx

            # ==== FIG - com cores por dataset ====
            if not df_plot.empty and "__ds__" in df_plot.columns:
                # Contar quantos datasets únicos temos
                unique_datasets = df_plot["__ds__"].nunique()
                print(f"[DEBUG BUILD_PREVIEW] Plotando {len(df_plot)} pontos de {unique_datasets} datasets")

                # Usar cores diferentes por dataset
                fig = px.scatter(
                    df_plot,
                    x="NII",
                    y="Area",
                    color="__ds__",  # Colorir por dataset
                    opacity=0.75,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    title=f"NMA Preview ({unique_datasets} datasets)",
                    labels={"__ds__": "Dataset"}
                )
            elif not df_plot.empty:
                # Dataset sem identificação por dataset, usar cor única
                fig = px.scatter(df_plot, x="NII", y="Area", opacity=0.75)
            else:
                # DataFrame vazio
                fig = px.scatter(pd.DataFrame({"NII": [], "Area": []}), x="NII", y="Area")

            fig.update_layout(
                margin=dict(l=60, r=10, t=40, b=60),
                xaxis_title="NII",
                yaxis_title="Area",
                showlegend=True,  # Mostrar legenda
                legend=dict(
                    title="Datasets" if "__ds__" in df_plot.columns else None,
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.02,
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="LightGrey",
                    borderwidth=1
                ),
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

            # verticais em PRETO (mesma espessura das horizontais) com spans por "andar"
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
    # === SAVE: clicar em "Save settings" -> abre seletor de pasta e salva imediatamente ===
    @app.callback(
        Output("nma-save-status", "children"),
        Input("nma-save-open", "n_clicks"),
        State("store-nma-settings", "data"),
        State("store-nma-step1", "data"),
        State("store-nma", "data"),
        prevent_initial_call=True,
    )
    def _save_settings_click(n, settings, step1, store_nma):
        if not n:
            raise dash.exceptions.PreventUpdate

        # 1) Monta o payload no MESMO schema esperado pelo NMA_settings.py
        try:
            payload = build_pkl_payload(settings=settings or {}, step1=step1 or {}, store_nma=store_nma or {})
        except Exception as e:
            return f"Erro ao montar payload: {e}"

        # 2) Pergunta a pasta para salvar (diálogo nativo do SO)
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            save_dir = tkfd.askdirectory(title="Escolha a pasta para salvar as configurações NMA")
            root.destroy()
        except Exception as e:
            return f"Não foi possível abrir o seletor de pastas (ambiente headless?): {e} "

        if not save_dir:
            raise dash.exceptions.PreventUpdate  # usuário cancelou

        # 3) Escreve o arquivo .pickle no diretório escolhido
        try:
            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            # nome padrão compatível com o seu script antigo:
            out_path = save_dir / "control_parameters.pickle"
            with open(out_path, "wb") as f:
                pickle.dump(payload, f)

            # (opcional) um JSON visível para inspeção rápida
            # from json import dump;  dump(payload, open(save_dir / "control_parameters.json", "w"), default=str, indent=2)

            return f"✅ Settings salvas em: {out_path}"
        except Exception as e:
            return f"Erro ao salvar o arquivo: {e}"

    @app.callback(
        Output("nma-fig-preview", "figure", allow_duplicate=True),
        Output("nma-result-pane", "style", allow_duplicate=True),
        Output("nma-step2-pane", "style", allow_duplicate=True),
        Input("nma-step2-complete", "n_clicks"),
        State("store-nma-settings", "data"),  # <- lê o CONSOLIDADO
        prevent_initial_call=True,
    )
    def _step2_complete(n, settings):
        if not n:
            return no_update, no_update, no_update

        if not settings or not settings.get("sample"):
            f = go.Figure()
            f.update_layout(title="Missing final settings", width=640, height=640)
            return f, {"display": "block"}, {"display": "none"}

        xcol = settings.get("xcol", "NII")
        ycol = settings.get("ycol", "Area")
        mu_x = float(settings.get("mu_x", 0.0))
        mu_y = float(settings.get("mu_y", 0.0))
        rx = float(settings.get("rx", 1.0))
        ry = float(settings.get("ry", 1.0))
        axis = settings.get("axis") or {}

        x = np.asarray(settings["sample"]["x"], dtype=float)
        y = np.asarray(settings["sample"]["y"], dtype=float)
        df = pd.DataFrame({xcol: x, ycol: y})

        fig = go.Figure()
        if not df.empty:
            fig.add_trace(go.Scattergl(
                x=df[xcol], y=df[ycol],
                mode="markers",
                marker=dict(size=6, opacity=0.65, color="#2563eb"),
                name="Controls (sample)",
            ))

        # Elipse FINAL (vem do Step 1/Auto/Sliders já consolidado)
        ell = ellipse_trace(mu_x, mu_y, rx, ry)
        ell.update(line=dict(color="#111827", width=2), name="Ellipse (final)")
        fig.add_trace(ell)

        # Se o Step 2 definiu faixas horizontais, plote-as
        y_lo = settings.get("y_lo");
        y_hi = settings.get("y_hi")
        if y_lo is not None:
            fig.add_shape(type="line", x0=df[xcol].min(), x1=df[xcol].max(),
                          y0=y_lo, y1=y_lo, line=dict(color="#ef4444", width=2, dash="dot"))
        if y_hi is not None:
            fig.add_shape(type="line", x0=df[xcol].min(), x1=df[xcol].max(),
                          y0=y_hi, y1=y_hi, line=dict(color="#ef4444", width=2, dash="dot"))

        fig.update_layout(
            autosize=False, width=640, height=640,
            margin=dict(l=60, r=10, t=70, b=60),
            title=dict(text="NMA — Preview (final)", x=0.5, xanchor="center"),
            xaxis_title=xcol, yaxis_title=ycol, showlegend=True,
        )
        if axis and axis.get("x") and axis.get("y"):
            fig.update_layout(xaxis_range=axis["x"], yaxis_range=axis["y"])
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        return fig, {"display": "block"}, {"display": "none"}

    def register_step2_collect(app):
        @app.callback(
            Output("store-nma-settings", "data", allow_duplicate=True),
            Input("nma-fig-lines", "figure"),
            State("store-nma-step1", "data"),
            prevent_initial_call=True,
        )
        def _collect(fig_lines, step1):
            if not step1:
                return no_update

            vmap = _extract_verticals(fig_lines)
            y_low, y_high = _extract_y_thresholds(fig_lines)

            settings = {
                "xcol": step1.get("xcol"),
                "ycol": step1.get("ycol"),
                "mu_x": step1.get("mu_x"),
                "mu_y": step1.get("mu_y"),
                "rx": step1.get("rx"),
                "ry": step1.get("ry"),
                "kx": step1.get("kx"),
                "ky": step1.get("ky"),
                "axis": step1.get("axis"),
                "sample": step1.get("sample"),
                "thresholds": {
                    "v_down": vmap["v_down"],
                    "v_mid": vmap["v_mid"],
                    "v_up": vmap["v_up"],
                    "v_down2": vmap["v_down2"],
                    # aliases retrocompatíveis que o build_pkl_payload também aceita
                    "x_left": vmap["v_down"],
                    "x_mid": vmap["v_mid"],
                    "x_right": vmap["v_up"],
                    # horizontais
                    "y_low": y_low,
                    "y_high": y_high,
                },
            }
            return settings

