from __future__ import annotations
from typing import Optional, Sequence, Literal, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging
from .Graphs import Graphs

# configure logger simples (ajuste conforme seu projeto)
logger = logging.getLogger("fornma.plot")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(h)

GraphType = Literal['violin', 'box', 'dot', 'bar', 'scatter', 'line', 'rolling-average', 'cpd']


def plot(path: Union[str, Sequence[str]],
         path_save: str,
         conditions: Optional[Sequence[str]],
         frames: Optional[Sequence[int]],
         graph_type: GraphType,
         gate: bool,
         **kwargs) -> str:

    if isinstance(path, (str, Path)):
        paths = [Path(path)]
    else:
        paths = [Path(p) for p in path]

    dfs = []

    for p in paths:
        p = Path(p)
        if not p.exists():
            raise FileNotFoundError(f"File {p} does not exists.")

        df_i = pd.read_csv(p)

        cond_cols = [c for c in df_i.columns if c.lower() == 'condition']
        if not cond_cols:
            raise ValueError(
                    f"The file '{p.name}' has no 'condition' column. "
                    f"To analyze more than one file, every file needs this column filled in."
                )

        cond_col = cond_cols[0]
        if not df_i[cond_col].astype(bool).any():
            raise ValueError(
                    f"The file '{p.name}' has a 'condition' column, but it is empty or has invalid values. "
                    f"To analyze more than one file, this column must be filled in."
            )

        dfs.append(df_i)

    df = pd.concat(dfs, ignore_index=True)

    out_dir = Path(path_save)
    out_dir.mkdir(parents=True, exist_ok=True)


    required_any = {'Overtime'}
    missing_any = [c for c in required_any if c not in df.columns]

    ot = False
    if 'Overtime' in df.columns:
        ot = bool(pd.api.types.is_bool_dtype(df['Overtime']) and df['Overtime'].any())

    graphs = Graphs(df, ot, conditions, frames, str(out_dir))
    graphs.is_in_df([kwargs.get('x'), kwargs.get('y'), kwargs.get('hue'), kwargs.get('size')])

    if gate:
        x, y = kwargs.get('x'), kwargs.get('y')
        if x is None or y is None:
            raise ValueError("To apply a gate, provide 'x' and 'y' in kwargs.")
        graphs.gate(x, y)

    # log no arquivo + logger
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = out_dir / "logs-fornma.txt"
    with log_path.open("a", encoding="utf-8") as logs:
        logs.write(f"\n\n{dt} - {graph_type} plot")

    logger.info("Generating plot '%s' (ot=%s) | params=%s", graph_type, ot, {k: kwargs.get(k) for k in ('x','y','hue','size','n','frames','control','dot')})

    # roteamento
    if graph_type == 'violin':
        if kwargs.get('dot'):
            fig = graphs.violin_dot(kwargs.get('y'), kwargs.get('hue'))
            graphs.save_figs(fig, 'violin-dot-plot')
        else:
            fig = graphs.violinplot(kwargs.get('y'), kwargs.get('hue'))
            graphs.save_figs(fig, 'violin-plot')

    elif graph_type == 'box':
        if kwargs.get('dot'):
            fig = graphs.box_dot(kwargs.get('y'), kwargs.get('hue'))
            graphs.save_figs(fig, 'box-dot-plot')
        else:
            fig = graphs.boxplot(kwargs.get('y'), kwargs.get('hue'))
            graphs.save_figs(fig, 'box-plot')

    elif graph_type == 'dot':
        fig = graphs.stripplot(kwargs.get('y'), kwargs.get('hue'))
        graphs.save_figs(fig, 'dot-plot')

    elif graph_type == 'bar':
        fig = graphs.barplot(kwargs.get('y'), kwargs.get('hue'))
        graphs.save_figs(fig, 'bar-plot')

    elif graph_type == 'scatter':
        figs, titles = graphs.scatterplot(kwargs.get('x'), kwargs.get('y'), kwargs.get('hue'), kwargs.get('size'))
        for f, t in zip(figs, titles):
            graphs.save_figs(f, t)

    elif graph_type == 'line':
        if not ot:
            raise ValueError("Line plots need time-lapse data (an 'Overtime' column with at least one True value).")
        graphs.save_figs(graphs.lineplot(**kwargs), 'line-plot')

    elif graph_type == 'rolling-average':
        if not ot:
            raise ValueError("Rolling average plots need time-lapse data (an 'Overtime' column with at least one True value).")
        ycol = kwargs.get('y'); n = kwargs.get('n')
        if ycol is None or n is None:
            raise ValueError("Rolling Average requer kwargs 'y' e 'n'.")
        graphs.save_figs(graphs.rolling_average(ycol, n), 'rolling-average-plot')

    elif graph_type == 'cpd':
        if not ot:
            raise ValueError("CPD plots need time-lapse data (an 'Overtime' column with at least one True value).")
        graphs.save_figs(graphs.cpd(kwargs.get('frames'), kwargs.get('control')), 'cumulative-population-doubling')

    else:
        raise ValueError(f"Invalid graph_type: {graph_type}")

    return f'Files were saved at {out_dir}'
