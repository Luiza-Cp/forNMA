# src/fornma/gui/callbacks/nma_step1.py
from __future__ import annotations
from dash import Input, Output, State, ctx, no_update
import plotly.graph_objects as go
import numpy as np
import pandas as pd


# ---------- helpers ----------
def _ellipse_trace(xc, yc, rx, ry, n=256, name="threshold"):
    t = np.linspace(0, 2*np.pi, n)
    x = xc + rx * np.cos(t)
    y = yc + ry * np.sin(t)
    return go.Scatter(x=x, y=y, mode="lines", line=dict(width=2, color="black"),
                      name=name, hoverinfo="skip")

def _make_step1_figure(df: pd.DataFrame, xcol: str, ycol: str,
                       xc: float, yc: float, rx: float, ry: float) -> go.Figure:
    fig = go.Figure()
    if df is not None and not df.empty:
        fig.add_trace(go.Scattergl(
            x=df[xcol], y=df[ycol],
            mode="markers",
            marker=dict(size=6, opacity=0.65, color="#2563eb"),
            name="Controls (sample)",
        ))
        fig.add_trace(_ellipse_trace(xc, yc, rx, ry))
        title_txt = "Adjust here the threshold ellipse.<br><sup>Use the Area/NII SD sliders</sup>"
    else:
        title_txt = "No control data to preview.<br><sup>Mark at least one dataset as Control and click Create</sup>"

    fig.update_layout(
        autosize=False, width=640, height=640,
        margin=dict(l=60, r=10, t=70, b=60),
        title=dict(text=title_txt, x=0.5, xanchor="center"),
        xaxis_title=(xcol or "NII"),
        yaxis_title=(ycol or "Area"),
    )
    return fig

def _load_controls_pool_from_params(params: dict, sample_per_ds: int = 2000):
    """
    Concatena todos os datasets com is_control=True.
    Retorna (pool, xcol, ycol, log)
    """
    log = []
    if not params:
        log.append("params: vazio/nulo")
        return None, None, None, "\n".join(log)

    dfs = []
    xcol = ycol = None

    def _to_num(series: pd.Series) -> pd.Series:
        if series.dtype == object:
            series = series.astype(str).str.replace(",", ".", regex=False)
        return pd.to_numeric(series, errors="coerce")

    for j, ds in enumerate(params.get("datasets", []), start=1):
        name = ds.get("name") or f"ds{j}"
        if not ds.get("is_control", False):
            log.append(f"- {name}: ignorado (is_control=False)")
            continue

        path = (ds.get("path") or "").strip()
        a_in = (ds.get("area_col") or "").strip()
        n_in = (ds.get("nii_col") or "").strip()
        if not (path and a_in and n_in):
            log.append(f"- {name}: faltando path/area_col/nii_col")
            continue

        try:
            raw = pd.read_csv(path, engine="python", sep=None)  # infere sep
        except Exception as e:
            log.append(f"- {name}: erro lendo CSV '{path}': {e}")
            continue

        cols_norm = [str(c).lstrip("\ufeff").strip() for c in raw.columns]
        raw.columns = cols_norm
        log.append(f"- {name}: lidas {len(raw)} linhas; colunas: {cols_norm[:6]}{' ...' if len(cols_norm)>6 else ''}")

        cmap = {c.casefold(): c for c in cols_norm}
        a_name = cmap.get(a_in.casefold())
        n_name = cmap.get(n_in.casefold())

        if not (a_name and n_name):
            # fallback: contains
            def _contains(needle):
                for c in cols_norm:
                    if needle.casefold() in c.casefold():
                        return c
                return None
            a_name = a_name or _contains(a_in)
            n_name = n_name or _contains(n_in)

        if not (a_name and n_name):
            log.append(f"  · colunas não encontradas (area='{a_in}', nii='{n_in}')")
            continue

        df = raw[[a_name, n_name]].copy()
        before = len(df)
        df[a_name] = _to_num(df[a_name])
        df[n_name] = _to_num(df[n_name])
        df = df.dropna()
        after = len(df)

        log.append(f"  · usando '{a_name}' (Area) e '{n_name}' (NII) | válidas: {after}/{before} linhas")

        if after == 0:
            log.append("  · nenhuma linha válida após coerção numérica")
            continue

        if after > sample_per_ds:
            df = df.sample(n=sample_per_ds, random_state=0)
            log.append(f"  · amostradas {sample_per_ds} linhas")

        df = df.rename(columns={a_name: "AREA_TMP", n_name: "NII_TMP"})
        dfs.append(df)
        xcol = "NII_TMP"; ycol = "AREA_TMP"

    if not dfs:
        log.append("Nenhum controle válido encontrado.")
        return None, None, None, "\n".join(log)

    pool = pd.concat(dfs, axis=0, ignore_index=True)
    log.append(f"POOL final: {len(pool)} linhas.")
    return pool, xcol, ycol, "\n".join(log)



# ---------- registro ----------
def register(app):
    # A) Clique em "Create NMA Settings" → gera amostra, SDs e desenha figura inicial

    @app.callback(
        Output("nma-fig-ellipse", "figure"),
        Output("store-nma-step1", "data"),
        Output("nma-nii-sd", "value"),
        Output("nma-area-sd", "value"),
        Output("nma-step1-debug", "children"),
        Input("btn-nma-build", "n_clicks"),  # ainda escuta o clique
        Input("store-nma", "data"),  # << também escuta mudanças no store
        prevent_initial_call=True,
    )
    def _step1_init(_n_clicks, store_nma):
        """
        Dispara quando o usuário clica no botão OU quando o store-nma muda.
        Só prossegue se store_nma tiver 'params'.
        """
        params = (store_nma or {}).get("params")
        if not params:
            # se o gatilho foi só o clique, ainda não temos params -> espera a próxima mudança do store
            if ctx.triggered_id == "btn-nma-build":
                return no_update, no_update, no_update, no_update, "aguardando params do botão…"
            # se veio de uma mudança do store mas continua sem params, registra e sai
            return _make_step1_figure(None, "NII", "Area", 0, 0, 1, 1), {}, 1.0, 1.0, "params: vazio/nulo"

        # carrega controles
        pool, xcol, ycol, log = _load_controls_pool_from_params(params)
        if pool is None or pool.empty:
            fig = _make_step1_figure(None, "NII", "Area", 0, 0, 1, 1)
            return fig, {}, 1.0, 1.0, log

        mu_x = float(pool[xcol].mean());
        sd_x = float(pool[xcol].std(ddof=1) or 1.0)
        mu_y = float(pool[ycol].mean());
        sd_y = float(pool[ycol].std(ddof=1) or 1.0)

        kx = 1.0;
        ky = 1.0
        rx = kx * sd_x;
        ry = ky * sd_y
        fig = _make_step1_figure(pool, xcol, ycol, mu_x, mu_y, rx, ry)

        store = {
            "xcol": xcol, "ycol": ycol,
            "mu_x": mu_x, "mu_y": mu_y,
            "sd_x": sd_x, "sd_y": sd_y,
            "kx": kx, "ky": ky,  # 👈 novo
            "rx": rx, "ry": ry,  # 👈 novo (raios atuais)
            "sample": {
                "x": pool[xcol].astype(float).tolist(),
                "y": pool[ycol].astype(float).tolist(),
            }
        }

        return fig, store, kx, ky, log

    # B) Sliders → redesenha apenas a elipse (usa a amostra guardada no store)

    @app.callback(
        Output("nma-fig-ellipse", "figure", allow_duplicate=True),
        Output("store-nma-step1", "data", allow_duplicate=True),  # 2º output
        Input("nma-nii-sd", "value"),
        Input("nma-area-sd", "value"),
        State("store-nma-step1", "data"),
        prevent_initial_call=True,
    )
    def _step1_update(kx, ky, store):
        # quando ainda não existe store (ex.: usuário mexeu nos sliders muito cedo),
        # precisamos retornar DOIS valores
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

        # reconstrói df a partir do sample guardado
        import pandas as pd
        import numpy as np
        x = np.asarray(store["sample"]["x"], dtype=float)
        y = np.asarray(store["sample"]["y"], dtype=float)
        df = pd.DataFrame({xcol: x, ycol: y})

        fig = _make_step1_figure(df, xcol, ycol, mu_x, mu_y, rx, ry)

        # atualiza o store com multiplicadores e raios atuais
        new_store = dict(store)
        new_store.update({"kx": float(kx), "ky": float(ky), "rx": float(rx), "ry": float(ry)})

        # SEMPRE retornar 2 itens
        return fig, new_store
