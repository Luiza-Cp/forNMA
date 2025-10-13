# src/fornma/gui/utils/nma_helpers.py
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go


# -------------------- parsing / limpeza --------------------
def _to_num(s: pd.Series) -> pd.Series:
    """Converte strings numéricas com vírgula decimal para float (coerce)."""
    if s.dtype == object:
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _normalize_header(cols) -> list[str]:
    """Remove BOM, trim e retorna lista de nomes de colunas normalizados."""
    return [str(c).lstrip("\ufeff").strip() for c in cols]


def _resolve_two_columns(raw: pd.DataFrame, a_in: str, n_in: str) -> tuple[str|None, str|None]:
    """Resolve nomes reais das colunas de Área/NII com casefold e 'contains'."""
    cols_norm = _normalize_header(raw.columns)
    raw.columns = cols_norm
    cmap = {c.casefold(): c for c in cols_norm}
    a_name = cmap.get(a_in.casefold())
    n_name = cmap.get(n_in.casefold())
    if not a_name:
        a_name = next((c for c in cols_norm if a_in.casefold() in c.casefold()), None)
    if not n_name:
        n_name = next((c for c in cols_norm if n_in.casefold() in c.casefold()), None)
    return a_name, n_name


# -------------------- loaders --------------------
def load_controls_pool(params: dict, sample_per_ds: int = 2000) -> tuple[pd.DataFrame|None, str|None, str|None, str]:
    """
    Concatena datasets marcados como is_control=True.
    Retorna (pool_df, xcol, ycol, log) onde:
      pool_df tem colunas: 'NII_TMP', 'AREA_TMP'
      xcol='NII_TMP', ycol='AREA_TMP'
    """
    log = []
    if not params:
        log.append("params: vazio/nulo")
        return None, None, None, "\n".join(log)

    dfs = []
    for j, ds in enumerate(params.get("datasets", []), start=1):
        name = ds.get("name") or f"ds{j}"
        if not ds.get("is_control", False):
            log.append(f"- {name}: ignorado (is_control=False)")
            continue

        path = (ds.get("path") or "").strip()
        a_in = (ds.get("area_col") or "").strip()
        n_in = (ds.get("nii_col") or "").strip()
        if not (path and a_in and n_in):
            log.append(f"- {name}: faltando path/area/nii")
            continue

        try:
            raw = pd.read_csv(path, engine="python", sep=None)  # infere separador
        except Exception as e:
            log.append(f"- {name}: erro lendo CSV '{path}': {e}")
            continue

        a_name, n_name = _resolve_two_columns(raw, a_in, n_in)
        if not (a_name and n_name):
            log.append(f"- {name}: colunas não encontradas (area='{a_in}', nii='{n_in}')")
            continue

        df = raw[[a_name, n_name]].copy()
        before = len(df)
        df[a_name] = _to_num(df[a_name]); df[n_name] = _to_num(df[n_name])
        df = df.dropna()
        after = len(df)
        log.append(f"  · válidas {after}/{before} linhas")

        if after == 0:
            continue
        if after > sample_per_ds:
            df = df.sample(n=sample_per_ds, random_state=0)
            log.append(f"  · amostradas {sample_per_ds}")

        df = df.rename(columns={a_name: "AREA_TMP", n_name: "NII_TMP"})
        dfs.append(df)

    if not dfs:
        log.append("Nenhum controle válido encontrado.")
        return None, None, None, "\n".join(log)

    pool = pd.concat(dfs, axis=0, ignore_index=True)
    return pool, "NII_TMP", "AREA_TMP", "\n".join(log)


def load_all_datasets(params: dict, sample_per_ds: int = 4000) -> tuple[pd.DataFrame|None, str|None, str|None, str]:
    """
    Carrega TODOS os datasets (controle e não-controle).
    Retorna (pool_df, xcol, ycol, log) com colunas: 'NII_TMP','AREA_TMP','__ds__'
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
            raw = pd.read_csv(path, engine="python", sep=None)
        except Exception as e:
            log.append(f"- {name}: erro lendo CSV: {e}")
            continue

        a_name, n_name = _resolve_two_columns(raw, a_in, n_in)
        if not (a_name and n_name):
            log.append(f"- {name}: não achou colunas (area='{a_in}', nii='{n_in}')")
            continue

        df = raw[[a_name, n_name]].copy()
        before = len(df)
        df[a_name] = _to_num(df[a_name]); df[n_name] = _to_num(df[n_name])
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


# -------------------- gráficos --------------------
def ellipse_trace(xc, yc, rx, ry, n=256, name="threshold"):
    t = np.linspace(0, 2*np.pi, n)
    x = xc + rx * np.cos(t)
    y = yc + ry * np.sin(t)
    return go.Scatter(x=x, y=y, mode="lines", line=dict(width=2, color="black"),
                      name=name, hoverinfo="skip")


# -------------------- ranges globais --------------------
def compute_axis_ranges_from_all(
    params: dict,
    k: float = 3.0,
    headroom: float = 0.05,
    use_quantile: float | None = None,
    k_neg: float = 2.0,   # <- NOVO: desvio no lado "menor"
):
    """
    Ranges globais (todos os datasets), com piso 0 e assimetria:
      X: [max(0, μx − k_neg·σx), (max(μx + k·σx, Qx) * (1 + headroom))]
      Y: [max(0, μy − k_neg·σy), (max(μy + k·σy,  Qy) * (1 + headroom))]
    Qx/Qy opcionais via 'use_quantile' (p.ex. 99.5) para não deixar 1 outlier explodir o topo.
    Retorna {"x":[xmin,xmax], "y":[ymin,ymax], "xcol":..., "ycol":...}
    """
    # carrega pool global como você já fazia (mantém seu comportamento atual)
    pool, xcol, ycol, _ = load_all_datasets(params, sample_per_ds=8000)
    if pool is None or pool.empty:
        return None

    # estatísticas globais
    mu_x = float(pool[xcol].mean()); sd_x = float(pool[xcol].std(ddof=1) or 1.0)
    mu_y = float(pool[ycol].mean()); sd_y = float(pool[ycol].std(ddof=1) or 1.0)

    # topo (lado positivo) usa 'k' — como antes
    x_top = mu_x + float(k) * sd_x
    y_top = mu_y + float(k) * sd_y

    # opcional: percentil alto para segurar cauda
    if use_quantile is not None:
        qx = float(np.nanpercentile(pool[xcol], use_quantile))
        qy = float(np.nanpercentile(pool[ycol], use_quantile))
        x_top = max(x_top, qx)
        y_top = max(y_top, qy)

    # piso assimétrico (lado negativo) com max(0, μ − k_neg·σ)
    x_min = max(0.0, mu_x - float(k_neg) * sd_x)
    y_min = max(0.0, mu_y - float(k_neg) * sd_y)

    # headroom só no topo
    x_max = x_top * (1.0 + float(headroom))
    y_max = y_top * (1.0 + float(headroom))

    return {"x": [x_min, x_max], "y": [y_min, y_max], "xcol": xcol, "ycol": ycol}

