# src/fornma/gui/callbacks/nma_step2.py
from __future__ import annotations
from dash import Input, Output, State, no_update
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from fornma.gui.utils.nma_helpers import (
    load_all_datasets,
    ellipse_trace,
    compute_axis_ranges_from_all,
)


# ---------- utilidades ----------
def _to_num(s: pd.Series) -> pd.Series:
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


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

    Regras de altura:
      - Com std_a/sd_area (originais do matplotlib):
          y_inf  = μy − sd_area·std_a
          y_sup  = μy + sd_area·std_a
          y_bot0 = μy − (1 + sd_area)·std_a
          y_top0 = μy + (2 + sd_area)·std_a
      - Sem std_a/sd_area (fallback usando só ry = sd_area·std_a):
          y_inf  = μy − ry
          y_sup  = μy + ry
          y_bot0 = μy − 2·ry
          y_top0 = μy + 2·ry
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
        title = "Step 2 — Ajuste dos limiares de NII"
    else:
        title = "No data to display."

    # =============================
    # 2) HORIZONTAIS = ELIPSE (N/I)
    # =============================
    # Limites “N/I” são ditados pela elipse do Step1
    if ry is None or mu_y is None:
        # fallback defensivo
        mu_y = float(mu_y or 0.0)
        ry   = float(ry or 1.0)
    y_inf = float(mu_y) - float(ry)
    y_sup = float(mu_y) + float(ry)

    # Span de X para desenhar horizontais (usa range dos dados quando possível)
    if pool is not None and not pool.empty:
        xmin = float(np.nanmin(pool[xcol]))
        xmax = float(np.nanmax(pool[xcol]))
    else:
        xmin = float(mu_x) - float(rx)
        xmax = float(mu_x) + float(rx)

    # Duas horizontais pretas (ditam altura dos quadrantes N e I)
    fig.add_shape(
        type="line", x0=xmin, x1=xmax, y0=y_inf, y1=y_inf,
        xref="x", yref="y", line=dict(color="black", width=3)
    )
    fig.add_shape(
        type="line", x0=xmin, x1=xmax, y0=y_sup, y1=y_sup,
        xref="x", yref="y", line=dict(color="black", width=3)
    )

    # Elipse igual à do Step1
    fig.add_trace(ellipse_trace(float(mu_x or 0), float(mu_y or 0), float(rx or 1), float(ry or 1)))

    # =====================================================
    # 3) SPANS VERTICAIS (3 andares) — iguais ao matplotlib
    # =====================================================
    if std_a is not None and sd_area is not None:
        # Fórmulas originais
        y_bot0 = float(mu_y) - (1.0 + float(sd_area)) * float(std_a)
        y_top0 = float(mu_y) + (2.0 + float(sd_area)) * float(std_a)
        y_inf  = float(mu_y) - float(sd_area) * float(std_a)  # redefine com std_a/sd_area exatos
        y_sup  = float(mu_y) + float(sd_area) * float(std_a)
    else:
        # Fallback com ry (mantém a lógica de “três andares” sem std_a explícito)
        y_bot0 = float(mu_y) - 2.0 * float(ry)
        y_top0 = float(mu_y) + 2.0 * float(ry)
        # y_inf/y_sup já definidos acima pelo ry

    span_down = (y_bot0, y_inf)   # “andar” inferior
    span_mid  = (y_inf,  y_sup)   # “andar” do meio
    span_up   = (y_sup,  y_top0)  # “andar” superior

    # ===========================================
    # 4) POSIÇÕES INICIAIS EM X (4 verticais)
    # ===========================================
    if not line_xs:
        # Fim da elipse (direita)
        x_end_ellipse = float(mu_x) + float(rx)

        # Clip opcional ao range do eixo, se já vier definido
        if axis_ranges and axis_ranges.get("x"):
            x_min_ax, x_max_ax = map(float, axis_ranges["x"])
            x_end_ellipse = max(min(x_end_ellipse, x_max_ax), x_min_ax)

        # up e mid começam iguais, no fim da elipse
        x_up = x_end_ellipse
        x_mid = x_end_ellipse

        if pool is not None and not pool.empty:
            xs = _to_num(pool[xcol]).to_numpy()
            q10, q90 = np.nanpercentile(xs, [10, 90])
            x_bottom, x_bottom2 = float(q10), float(q90)
        else:
            # fallback em torno de μx ± rx
            x_bottom = float(mu_x) - 0.75 * float(rx)
            x_bottom2 = float(mu_x) + 0.75 * float(rx)

        line_xs = [x_bottom, x_mid, x_up, x_bottom2]
    else:
        # Garante 4 posições e re-alinha v_mid ao v_up no init
        line_xs = (list(line_xs) + [line_xs[-1]])[:4]
        # força alinhamento mid = up no primeiro draw
        line_xs[1] = float(line_xs[2])

    x_bottom, x_mid, x_up, x_bottom2 = line_xs[:4]


    # Cria as 4 verticais azuis já com spans Y por “andar”
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
        x0=float(x_mid), x1=float(x_mid),
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
        xaxis_title=xcol or "NII",
        yaxis_title=ycol or "Area",
        showlegend=True,
    )

    # aplica ranges globais se existirem
    if axis_ranges and axis_ranges.get("x") and axis_ranges.get("y"):
        fig.update_layout(xaxis_range=axis_ranges["x"], yaxis_range=axis_ranges["y"])

    return fig



# ---------- registro ----------
def register(app):
    # NEXT → constrói Step 2 usando elipse do Step 1 e eixos ±3sd (iguais ao Step 1)
    @app.callback(
        Output("store-nma-wizard", "data"),
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

        # 2) ranges globais (preferir salvos; senão recalcula)
        axis = (step1 or {}).get("axis")
        if not (axis and axis.get("x") and axis.get("y")):
            axis = compute_axis_ranges_from_all(params, k=3.0, headroom=0.05)

        # 3) recuperar linhas salvas do store-nma
        saved = ((store_nma or {}).get("step2", {}) or {}).get("lines", {})

        def _xs_from_saved(saved_dict):
            # ordem: v_down, v_mid, v_up, v_down2
            keys = ["v_down", "v_mid", "v_up", "v_down2"]
            xs = []
            for k in keys:
                x = (saved_dict.get(k) or {}).get("x")
                xs.append(float(x) if x is not None else None)
            # se v_up existir, alinhar v_mid a v_up no primeiro draw (tua regra)
            if xs[2] is not None:
                xs[1] = xs[2]
            return xs if any(v is not None for v in xs) else None

        line_xs = _xs_from_saved(saved)

        # 4) montar figura (usa a tua função já ajustada com os 3 “andares”)
        fig = _make_step2_figure(
            pool=pool,
            xcol=xcol, ycol=ycol,
            mu_x=mu_x, mu_y=mu_y,
            rx=rx, ry=ry,
            line_xs=line_xs,  # <- carrega posições salvas (ou defaults)
            axis_ranges=axis,
            std_a=std_a, sd_area=sd_area,
        )

        # 5) avança wizard para step 2 (destrava o _toggle_panes)
        return {"step": 2}, fig

    # trava o Y das verticais quando o usuário arrasta (snap y para [μy−ry, μy+ry])
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
        """
        Mantém as linhas verticais (v_up, v_mid, v_down, v_down2) estritamente verticais,
        repondo y0/y1 conforme o 'andar' e salvando as posições no store-nma.
        """
        if not relayout or not fig:
            return no_update, no_update

        store_nma = store_nma or {}
        step1 = step1 or {}

        # --- Parâmetros do Step1: média e "altura" dos quadrantes (ry) ---
        # mean_a pode ter sido salvo como 'mean_a' ou 'mu_y'
        mean_a = step1.get("mean_a", step1.get("mu_y"))
        # ry pode estar direto, ou podemos obter por sd_area * std_a
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
            # sem parâmetros mínimos, não alteramos a figura nem o store
            return no_update, no_update

        mean_a = float(mean_a)
        ry = float(ry)

        # Se tivermos std_a e sd_area, usamos as fórmulas originais do matplotlib.
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
                # fallback seguro com ry
                y_inf = mean_a - ry
                y_sup = mean_a + ry
                y_bot0 = mean_a - 2.0 * ry
                y_top0 = mean_a + 2.0 * ry
        else:
            # fallback usando apenas ry (mantém a lógica de 3 andares)
            y_inf = mean_a - ry
            y_sup = mean_a + ry
            y_bot0 = mean_a - 2.0 * ry
            y_top0 = mean_a + 2.0 * ry

        spans = {
            "v_up": (y_sup, y_top0),  # andar superior
            "v_mid": (y_inf, y_sup),  # andar do meio
            "v_down": (y_bot0, y_inf),  # andar inferior
            "v_down2": (y_bot0, y_inf),  # idem inferior
        }

        # --- Preparos da figura/axis ---
        layout = fig.get("layout", {}) or {}
        shapes = [dict(s) for s in (layout.get("shapes") or [])]
        if not shapes:
            return no_update, no_update

        # range do eixo X para clip opcional
        xaxis = layout.get("xaxis", {}) or {}
        x_range = xaxis.get("range")
        x_min_ax = x_max_ax = None
        if isinstance(x_range, (list, tuple)) and len(x_range) == 2:
            try:
                x_min_ax, x_max_ax = map(float, x_range)
            except Exception:
                x_min_ax = x_max_ax = None

        # --- Aplica mudanças vindas do relayoutData ---
        changed = False
        for key, val in (relayout or {}).items():
            # Esperamos formatos tipo: 'shapes[3].x0', 'shapes[3].x1'
            if not key.startswith("shapes["):
                continue
            try:
                idx_str = key.split("[", 1)[1].split("]", 1)[0]
                idx = int(idx_str)
            except Exception:
                continue
            if idx < 0 or idx >= len(shapes):
                continue

            s = shapes[idx]
            role = s.get("name")  # "v_up" | "v_mid" | "v_down" | "v_down2" (somente verticais azuis têm name)
            if role not in spans:
                # Ignora horizontais pretas, elipse, etc.
                continue

            # Só processa mudanças em X; mantém as linhas estritamente verticais
            if key.endswith(".x0") or key.endswith(".x1"):
                try:
                    new_x = float(val)
                except Exception:
                    continue

                # clip opcional ao range do eixo
                if x_min_ax is not None and x_max_ax is not None:
                    if new_x < x_min_ax:
                        new_x = x_min_ax
                    elif new_x > x_max_ax:
                        new_x = x_max_ax

                # atualiza x0/x1 iguais
                s["x0"] = new_x
                s["x1"] = new_x

                # repõe y0/y1 conforme o 'andar'
                y0, y1 = spans[role]
                s["y0"] = float(y0)
                s["y1"] = float(y1)
                s["yref"] = "y"

                shapes[idx] = s
                changed = True

        if not changed:
            return no_update, no_update

        # --- Reescreve shapes na figure ---
        new_fig = dict(fig)
        new_layout = dict(layout)
        new_layout["shapes"] = shapes
        new_fig["layout"] = new_layout

        # --- Salva posições finais no store-nma ---
        lines_data = {}
        for s in shapes:
            # só coleta as verticais azuis com 'name'
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
                # ignora se algum dado não estiver coerente
                pass

        new_store = dict(store_nma)
        step2_ns = dict(new_store.get("step2", {}) or {})
        step2_ns["lines"] = lines_data
        new_store["step2"] = step2_ns

        return new_fig, new_store

    # alterna visibilidade dos panes preservando estilos originais
    @app.callback(
        Output("nma-stage1", "style"),
        Output("nma-nii-slider-row", "style"),
        Output("nma-step2-pane", "style"),
        Input("store-nma-wizard", "data"),
        State("nma-stage1", "style"),
        State("nma-nii-slider-row", "style"),
        State("nma-step2-pane", "style"),
        prevent_initial_call=False,
    )
    def _toggle_panes(wiz, s1, sNII, s2):
        s1 = dict(s1 or {})
        sNII = dict(sNII or {})
        s2 = dict(s2 or {})
        step = (wiz or {}).get("step", 1)
        if step == 2:
            s1["display"]  = "none"
            sNII["display"] = "none"
            s2["display"]  = "block"
        else:
            s1["display"]  = "flex"     # como no layout original
            sNII["display"] = "block"
            s2["display"]  = "none"
        return s1, sNII, s2
