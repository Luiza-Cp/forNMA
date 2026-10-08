from __future__ import annotations
from typing import Optional, List, Union
from pathlib import Path
from datetime import datetime
from sklearn.cluster import KMeans

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import umap


def perform_clustering(
        path: Union[str, List[str]],
        saving_path: str,
        columns: Optional[List[str]] = None,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        metric: str= 'Euclidean',
        scale: bool = True,
                       ) -> pd.DataFrame:


    if isinstance(path, (str, Path)):
        paths = [Path(path)]
    else:
        paths = [Path(p) for p in path]

    out_dir = Path(saving_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    dfs = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            raise FileNotFoundError(f"File {p} does not exists.")
        df_i = pd.read_csv(p, index_col=0)
        if not "Condition" in df_i.columns:
            raise ValueError(
                f" The columns 'Condition' is required. Please, check the file '{p.name}' and try again. "
                f"This column can not be empty or set to False."
            )
        elif df_i['Condition'].isna().any() or df_i['Condition'].any() == False:
            raise ValueError(
                f"The file '{p.name}' has the column named 'Condition', but its values are empty or invalid."
            )
        else:
            dfs.append(df_i)

    df = pd.concat(dfs, ignore_index=True)

    if columns is None:
        feat_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not feat_cols:
            raise ValueError("None of columns are numeric UMAP.")
    else:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise KeyError(f"Missing columns: {missing}")
        feat_cols = list(columns)

    valid = ~df[feat_cols].isna().any(axis=1)
    if not valid.any():
        raise ValueError("All rows have NaN values at selected features.")


    X = df.loc[valid, feat_cols].to_numpy()
    if scale:
        X = StandardScaler().fit_transform(X)


    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=2,
        metric=metric.lower(),
        random_state=42,
    )
    embedding = reducer.fit_transform(X)

    emb_cols = [f"UMAP{i + 1}" for i in range(2)]

    df_out = df.copy()
    for c in emb_cols:
        df_out[c] = np.nan
    df_out.loc[valid, emb_cols] = embedding

    csv_path = out_dir / "Results with umap coordinates.csv"
    df_out.to_csv(csv_path, index=False)

    plt.figure(figsize=(7, 6))
    plt.scatter(df_out.loc[valid, "UMAP1"], df_out.loc[valid, "UMAP2"], s=4, alpha=0.8)
    plt.gca().set_aspect("equal", "datalim")
    plt.xlabel("UMAP1")
    plt.ylabel("UMAP2")
    plt.title(f"UMAP (n_neighbors={n_neighbors}, min_dist={min_dist})", fontsize=11)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fig_path = out_dir / f"umap_{ts}.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()

    # --- log ---
    log_path = out_dir / "logs-fornma.txt"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            "\n\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - UMAP\n"
            f"  files: {', '.join(str(p) for p in paths)}\n"
            f"  saving_path: {out_dir}\n"
            f"  features: {feat_cols}\n"
            f"  n_neighbors: {n_neighbors}\n"
            f"  min_dist: {min_dist}\n"
            f"  metric: {metric}\n"
            f"  scale: {scale}\n"
            f"  rows_total: {len(df)} | rows_used: {int(valid.sum())}\n"
            f"  outputs: figure={fig_path.name}, table={csv_path.name}\n"
        )

    return df_out


def plot_elbow(
    path: str,                  # Path to CSV returned by UMAP step
    saving_path: str,           # Folder to save the elbow plot
    k_min: int = 1,
    k_max: int = 10,
):
    """
      Generates and saves an Elbow Plot from a CSV containing UMAP coordinates.

      Parameters
      ----------
      path : str
          Path to the CSV file returned by the UMAP step (must contain UMAP columns).
      saving_path : str
          Folder where the elbow plot will be saved.
      k_min : int, optional
          Minimum number of clusters to test, by default 1.
      k_max : int, optional
          Maximum number of clusters to test, by default 10.

      Raises
      ------
      FileNotFoundError
          If the CSV file does not exist.
      ValueError
          If the CSV does not contain at least two numeric UMAP columns.
      """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File {path} does not exist.")

    df = pd.read_csv(path)

    # Select UMAP columns
    umap_cols = [c for c in df.columns if c.lower().startswith("umap")]
    if len(umap_cols) < 2:
        raise ValueError(
            f"The file must contain at least two UMAP columns (found {len(umap_cols)})."
        )

    X = df[umap_cols].dropna()
    if X.empty:
        raise ValueError("No valid rows found in the UMAP columns after dropping NaNs.")

    inertias = []
    k_values = range(k_min, k_max + 1)
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)

    save_dir = Path(saving_path)
    save_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 6))
    plt.plot(k_values, inertias, 'bo-')
    plt.xlabel('Number of Clusters (k)')
    plt.ylabel('Inertia')
    plt.title('Elbow Plot for Optimal Number of Clusters')
    elbow_path = save_dir / "elbow_plot.png"
    plt.savefig(elbow_path, dpi=300, bbox_inches="tight")
    plt.close()

    return


def color_umap(
    df_umap_path: Union[str, Path],
    saving_path: Optional[Union[str, Path]] = None,
    color_col: Optional[str] = None,            # color by an existing column
    use_clusters: bool = False,
    n_clusters: Optional[int] = None,           # if provided (and color_col=None), color by KMeans

) -> None:
    """
    Color a UMAP scatter either by an existing DataFrame column (color_col)
    or by KMeans clusters (when n_clusters is provided and color_col is None).

    Returns
    -------
    (fig_path, csv_path_if_cluster_else_None)

    Raises
    ------
    FileNotFoundError
        If df_umap_path does not exist.
    ValueError
        If UMAP columns are missing/invalid, or if neither coloring mode is specified.
    """
    df_umap_path = Path(df_umap_path)
    if not df_umap_path.exists():
        raise FileNotFoundError(f"File {df_umap_path} does not exist.")

    out_dir = Path(saving_path) if saving_path is not None else df_umap_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(df_umap_path)

    umap_cols = [c for c in df.columns if c.lower().startswith("umap")]
    if len(umap_cols) < 2:
        raise ValueError(f"Expected at least two UMAP columns, found: {umap_cols}")

    # Valid rows (no NaNs in UMAP)
    valid_mask = ~df[umap_cols].isna().any(axis=1)
    if not valid_mask.any():
        raise ValueError("No valid rows to plot: all UMAP rows contain NaN.")

    mode = 'kmeans' if use_clusters ==True else 'column'

    plt.figure()

    if mode == 'column' and color_col not in df.columns:
        raise ValueError(f"Column '{color_col}' not found in the DataFrame.")

    if mode=='kmeans':
        if n_clusters is None or n_clusters < 1:
            raise ValueError("'n_clusters' must be >= 1 when coloring by KMeans.")

        X = df.loc[valid_mask, umap_cols].to_numpy(dtype=float)
        kmeans = KMeans(n_clusters=n_clusters)
        labels = kmeans.fit_predict(X).astype(int)
        df = df.copy()
        df["cluster"] = np.nan
        df.loc[valid_mask, "cluster"] = labels
        color_col = 'cluster'


    series = df.loc[valid_mask, color_col]
    if pd.api.types.is_numeric_dtype(series):
        sc = plt.scatter(df.loc[valid_mask, umap_cols[0]],
                             df.loc[valid_mask, umap_cols[1]],
                             c=series.values, alpha=0.6, s=1)
        plt.colorbar(sc, label=str(color_col))
    else:
        # Categorical: one scatter per class for a clean legend
        cats = series.astype(str).unique().tolist()
        for lab in cats:
            idx = valid_mask & (df[color_col].astype(str) == lab)
            plt.scatter(df.loc[idx, umap_cols[0]],
                            df.loc[idx, umap_cols[1]],
                            alpha=0.6, label=lab, s=1)
            plt.legend(title=str(color_col), markerscale=1.6, fontsize=9, frameon=False)

    ts_csv = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"umap_with_clusters_k{n_clusters}_{ts_csv}.csv"

    if mode=='kmeans':
        df.to_csv(csv_path, index=False)

    title = f"UMAP colored by '{color_col}'"
    plt.gca().set_aspect("equal", "datalim")
    plt.xlabel(umap_cols[0]); plt.ylabel(umap_cols[1])
    plt.title(title, fontsize=11)

    ts_fig = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"k{n_clusters}" if mode == "kmeans" else f"col-{color_col}"
    fig_path = out_dir / f"umap_colored_{suffix}_{ts_fig}.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()


    log_path = out_dir / "logs-fornma.txt"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            "\n\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - UMAP coloring\n"
            f"  file: {df_umap_path}\n"
            f"  saving_path: {out_dir}\n"
            f"  umap_cols: {list(umap_cols)}\n"
            f"  mode: {mode}\n"
            f"  color_col: {color_col}\n"
            f"  n_clusters: {n_clusters}\n"
            f"  outputs: figure={fig_path.name}" + (f", table={csv_path.name}" if csv_path else "") + "\n"
        )

    return None


