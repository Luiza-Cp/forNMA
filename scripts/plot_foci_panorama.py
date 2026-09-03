from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


METHODS = [
    "raw_triangle",
    "raw_yen",
    "tophat_p90",
    "tophat_p95",
    "tophat_p97",
    "tophat_p98",
    "tophat_p99",
    "tophat_p995",
    "tophat_p999",
]
CHANNELS = ["DAPI", "gh2AX"]
CELL_LINES = ["RD", "SK"]
CONDITIONS = ["Control", "DMSO", "DOXO", "PTC", "PTC+DOXO"]
METRICS = {
    "count": "Foci_count",
    "area": "Foci_area_total",
    "mean": "Foci_mean_intensity",
}


def load_results(results_root: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(results_root.glob("*/*/Results_with_foci_thresholds_ALL.csv")):
        cell_line = path.relative_to(results_root).parts[0]
        df = pd.read_csv(path)
        df["Cell_line"] = cell_line
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No Results_with_foci_thresholds_ALL.csv found under {results_root}")
    return pd.concat(frames, ignore_index=True)


def to_long(df: pd.DataFrame, metric_key: str) -> pd.DataFrame:
    prefix = METRICS[metric_key]
    pattern = re.compile(rf"^{re.escape(prefix)}_(DAPI|gh2AX)_(.+)$")
    rows = []
    id_cols = ["Cell_line", "Condition", "Frame", "Cell"]
    for col in df.columns:
        match = pattern.match(col)
        if not match:
            continue
        channel, method = match.groups()
        if method not in METHODS:
            continue
        part = df[id_cols + [col]].copy()
        part = part.rename(columns={col: "value"})
        part["channel"] = channel
        part["method"] = method
        rows.append(part)
    if not rows:
        raise ValueError(f"No columns found for metric {metric_key}")
    long = pd.concat(rows, ignore_index=True)
    long["Condition"] = pd.Categorical(long["Condition"], categories=CONDITIONS, ordered=True)
    long["method"] = pd.Categorical(long["method"], categories=METHODS, ordered=True)
    long["panel"] = long["Cell_line"].astype(str) + " " + long["channel"].astype(str)
    return long.dropna(subset=["value"]).sort_values(["method", "Cell_line", "channel", "Condition"])


def add_metric_figure(long: pd.DataFrame, metric_key: str, out_path: Path, plot_kind: str, wide: bool = False) -> None:
    panels = [(line, channel) for line in CELL_LINES for channel in CHANNELS]
    subplot_titles = [f"{line} | {channel}" for line, channel in panels]
    fig = make_subplots(
        rows=len(METHODS),
        cols=len(panels),
        shared_xaxes=False,
        shared_yaxes=False,
        vertical_spacing=0.016 if wide else 0.012,
        horizontal_spacing=0.025 if wide else 0.035,
        subplot_titles=subplot_titles,
    )

    colors = {
        "Control": "#315C8C",
        "DMSO": "#8A8F36",
        "DOXO": "#C44536",
        "PTC": "#5F4B8B",
        "PTC+DOXO": "#1B8A5A",
    }

    showlegend_seen = set()
    for row_idx, method in enumerate(METHODS, start=1):
        method_df = long[long["method"] == method]
        for col_idx, (cell_line, channel) in enumerate(panels, start=1):
            panel_df = method_df[(method_df["Cell_line"] == cell_line) & (method_df["channel"] == channel)]
            for condition in CONDITIONS:
                values = panel_df.loc[panel_df["Condition"] == condition, "value"]
                if values.empty:
                    continue
                legend_key = condition
                common = dict(
                        x=[condition] * len(values),
                        y=values,
                        name=condition,
                        legendgroup=condition,
                        marker_color=colors[condition],
                        showlegend=legend_key not in showlegend_seen,
                )
                if plot_kind == "violin":
                    trace = go.Violin(
                        **common,
                        points="all",
                        jitter=0.08 if wide else 0.18,
                        pointpos=0,
                        marker_size=3.8 if wide else 2.6,
                        line_width=1,
                        opacity=0.64,
                        box_visible=True,
                        meanline_visible=True,
                        spanmode="hard",
                        width=0.92 if wide else None,
                        scalemode="width",
                    )
                else:
                    trace = go.Box(
                        **common,
                        boxpoints="all",
                        jitter=0.36,
                        pointpos=0,
                        marker_size=3,
                        line_width=1,
                        opacity=0.72,
                    )
                fig.add_trace(trace, row=row_idx, col=col_idx)
                showlegend_seen.add(legend_key)
            if col_idx == 1:
                fig.update_yaxes(title_text=method, row=row_idx, col=col_idx)

    metric_titles = {
        "count": "Foci Count",
        "area": "Foci Total Area",
        "mean": "Foci Mean Intensity",
    }
    fig.update_layout(
        title=f"{metric_titles[metric_key]} por Condicao, Canal, Linhagem e Metodo",
        template="plotly_white",
        height=max(3150, 350 * len(METHODS)) if wide else max(2200, 230 * len(METHODS)),
        width=2800 if wide else 1800,
        violinmode="group",
        boxmode="group",
        margin=dict(l=95, r=45, t=95, b=95),
        legend_title_text="Condition",
        font=dict(size=13 if wide else 11),
    )
    fig.update_xaxes(categoryorder="array", categoryarray=CONDITIONS, tickangle=-18 if wide else -25)
    fig.update_yaxes(zeroline=True, gridcolor="#E8EEF7")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_path, include_plotlyjs="cdn")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--plot-kind", choices=["box", "violin"], default="box")
    parser.add_argument("--wide", action="store_true")
    args = parser.parse_args()

    out_dir = args.out_dir or args.results_root / "foci_threshold_panorama_plots"
    df = load_results(args.results_root)
    for metric_key in METRICS:
        long = to_long(df, metric_key)
        suffix = "violin_wide_panorama" if args.plot_kind == "violin" and args.wide else "violin_panorama" if args.plot_kind == "violin" else "panorama"
        out_path = out_dir / f"foci_{metric_key}_{suffix}.html"
        add_metric_figure(long, metric_key, out_path, args.plot_kind, args.wide)
        long.to_csv(out_dir / f"foci_{metric_key}_long_data.csv", index=False)
        print(out_path)


if __name__ == "__main__":
    main()
