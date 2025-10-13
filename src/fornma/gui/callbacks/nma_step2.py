# src/fornma/gui/callbacks/nma_step2.py
from __future__ import annotations
from dash import Input, Output, State, no_update
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def _to_num(s: pd.Series) -> pd.Series:
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _load_all_datasets(params: dict, sample_per_ds: int = 4000):
    """
    Carrega TODOS os datasets (controle e não-controle) de params["datasets"].
    Retorna (pool_df, xcol, ycol, log)
    pool_df tem colunas: NII_TMP, AREA_TMP, __ds__
    """
    log = []
    if not params:
        log.append("step2: params vazio/nulo")
        return None, None, None, "\n".join(log)

    dfs = []
    for j, ds in enumerate(params.get("datasets", []), start=1):
        name = ds.get("name") or f"Dataset {j}"
        path = (ds.get("path") or "").strip()
        a_in = (ds.get("area_col") or "").strip()
        n_in = (ds.get("nii_col") or "").strip()
        if not (path and a_in and n_in):
            log.append(f"- {name}: faltando path/area/nii")
            continue

        try:
            raw = pd.read_csv(path, engine="python", sep=None)  # infere separador
        except Exception as e:
            log.append(f"- {name}: erro lendo CSV: {e}")
            continue

        cols_norm = [str(c).lstrip("\ufeff").strip() for c in raw.columns]
        raw.columns = cols_norm
        cmap = {c.casefold(): c for c in cols_norm}
        a_name = cmap.get(a_in.casefold()) or next((c for c in cols_norm if a_in.casefold() in c.casefold()), None)
        n_name = cmap.get(n_in.casefold()) or next((c for c in cols_norm if n_in.casefold() in c.casefold()), None)
        if not (a_name and n_name):
            log.append(f"- {name}: não achou colunas (area='{a_in}', nii='{n_in}')")
            continue

        df = raw[[a_name, n_name]].copy()
        before = len(df)
        df[a_name] = _to_num(df[a_name])
        df[n_name] = _to_num(df[n_name])
        df = df.dropna()
        after = len(df)
        log.append(f"- {name}: válidas {after}/{before} linhas")

        if after == 0:
            continue

        if after > sample_per_ds:
            df = df.sample(n=sample_per_ds, random_state=0)
            log.append(f"  · amostradas {sample_per_ds}")

        df = df.rename(columns={a_name: "AREA_TMP", n_name: "NII_TMP"})
        df["__ds__"] = name
        dfs.append(df)

    if not dfs:
        log.append("step2: nenhum dataset válido encontrado.")
        return None, None, None, "\n".join(log)

    pool = pd.concat(dfs, axis=0, ignore_index=True)
    log.append(f"step2: POOL final {len(pool)} linhas.")
    return pool, "NII_TMP", "AREA_TMP", "\n".join(log)


def _make_step2_figure(pool: pd.DataFrame, xcol: str, ycol: str,
                       ymin: float, ymax: float, line_xs: list[float] | None):
    fig = go.Figure()
    if pool is not None and not pool.empty:
        for name, g in pool.groupby("__ds__"):
            fig.add_trace(go.Scattergl(
                x=g[xcol], y=g[ycol],
                mode="markers",
                name=name,
                marker=dict(size=5, opacity=0.6),
            ))

        # se não vieram posições, usa quantis 10/30/70/90 do NII como sugestão
        if not line_xs:
            xs = pool[xcol].to_numpy()
            q10, q30, q70, q90 = np.nanpercentile(xs, [10, 30, 70, 90])
            line_xs = [float(q10), float(q30), float(q70), float(q90)]

        for v in line_xs:
            fig.add_shape(
                type="line",
                x0=float(v), x1=float(v),
                y0=float(ymin), y1=float(ymax),
                yref="y",  # coordenadas em dados
                line=dict(color="deepskyblue", width=3),
                editable=True,
            )

        title = "Click-and-drag the blue vertical lines to set NII limits.<br><sup>All datasets are shown</sup>"
    else:
        title = "No data to display."

    fig.update_layout(
        autosize=False, width=640, height=640,
        margin=dict(l=60, r=10, t=80, b=60),
        title=dict(text=title, x=0.5, xanchor="center"),
        xaxis_title=xcol or "NII",
        yaxis_title=ycol or "Area",
    )
    return fig


def register(app):
    # NEXT → constrói Step 2 com limites verticais da elipse (Step 1)
    @app.callback(
        Output("store-nma-wizard", "data"),
        Output("nma-fig-lines", "figure"),
        Input("nma-step1-next", "n_clicks"),
        State("store-nma", "data"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _go_to_step2(_n, store_nma, step1):
        params = (store_nma or {}).get("params")
        pool, xcol, ycol, log = _load_all_datasets(params)

        # pega limites verticais da elipse (Step 1)
        mu_y = (step1 or {}).get("mu_y")
        ry   = (step1 or {}).get("ry")
        if mu_y is None or ry is None:
            if pool is not None and not pool.empty:
                ymin, ymax = float(pool[ycol].min()), float(pool[ycol].max())
            else:
                ymin, ymax = 0.0, 1.0
        else:
            ymin, ymax = float(mu_y - ry), float(mu_y + ry)

        fig = _make_step2_figure(pool, xcol, ycol, ymin, ymax, line_xs=None)
        return {"step": 2}, fig

    # trava o Y das linhas quando o usuário arrasta (snap y para [ymin,ymax])
    @app.callback(
        Output("nma-fig-lines", "figure", allow_duplicate=True),
        Input("nma-fig-lines", "relayoutData"),
        State("nma-fig-lines", "figure"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _lock_line_y(relayout, fig, step1):
        if not relayout or not fig:
            return no_update

        mu_y = (step1 or {}).get("mu_y")
        ry   = (step1 or {}).get("ry")
        if mu_y is None or ry is None:
            return no_update
        ymin = float(mu_y - ry)
        ymax = float(mu_y + ry)

        shapes = [dict(s) for s in (fig.get("layout", {}).get("shapes") or [])]
        changed = False
        for k, v in relayout.items():
            if not k.startswith("shapes["):
                continue
            try:
                idx = int(k.split("[", 1)[1].split("]", 1)[0])
            except Exception:
                continue
            if 0 <= idx < len(shapes):
                s = shapes[idx]
                if k.endswith(".x0"): s["x0"] = float(v)
                if k.endswith(".x1"): s["x1"] = float(v)
                # força Y
                s["y0"] = ymin
                s["y1"] = ymax
                s["yref"] = "y"
                shapes[idx] = s
                changed = True

        if not changed:
            return no_update

        new_fig = dict(fig)
        new_fig.setdefault("layout", {})["shapes"] = shapes
        return new_fig

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
            s1["display"] = "none"
            sNII["display"] = "none"
            s2["display"] = "block"
        else:
            s1["display"] = "flex"  # Step 1 precisa ser 'flex' como no layout
            sNII["display"] = "block"
            s2["display"] = "none"
        return s1, sNII, s2

