# Helpers.py
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import shapiro, levene
from itertools import product
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from pathlib import Path
from typing import Union, List
import json
from datetime import datetime

class AnalysisHelper:
    def __init__(self, alpha: float = 0.05, log_file: str | None = None):
        self.alpha = alpha
        self.log_file = log_file

    def load_and_concat(self, paths: Union[str, Path, List[Union[str, Path]]]) -> pd.DataFrame:
        if isinstance(paths, (str, Path)):
            paths = [paths]
        dfs = []
        for p in paths:
            p = Path(p)
            if not p.exists():
                raise FileNotFoundError(f"File not found: {p}")
            df_i = pd.read_csv(p)
            if "Condition" not in df_i.columns:
                raise ValueError(f"'Condition' column missing in {p.name}.")
            if df_i["Condition"].isna().any() or (df_i["Condition"] == False).any():
                raise ValueError(f"Invalid/empty values in 'Condition' for {p.name}.")
            dfs.append(df_i)
        if not dfs:
            raise ValueError("No valid input files.")
        return pd.concat(dfs, ignore_index=True)


    # logging centralizado
    def log(self, msg: str):
        print(msg)
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")

    def log_header(self, analysis: str, **details):
        self.log("")
        self.log("=" * 72)
        self.log(f"Analysis: {analysis}")
        self.log(f"Started at: {datetime.now():%Y-%m-%d %H:%M:%S}")
        for key, value in details.items():
            label = str(key).replace("_", " ").capitalize()
            self.log(f"{label}: {value}")
        self.log("=" * 72)

    def log_section(self, title: str):
        self.log("")
        self.log(f"-- {title} --")

    def log_kv(self, key: str, value):
        self.log(f"{key}: {value}")

    def log_table(self, title: str, table: pd.DataFrame | None, *, index: bool = True, round_digits: int | None = None):
        self.log_section(title)
        if table is None or table.empty:
            self.log("No rows.")
            return
        out = table.round(round_digits) if round_digits is not None else table
        self.log(out.to_string(index=index))

    # descritivas
    def descriptive(self, df: pd.DataFrame, by: list[str], y: str) -> pd.DataFrame:
        """Funciona p/ 1 ou 2 fatores: by=['grupo'] (one-way) ou by=['A','B'] (two-way)."""
        key = by if isinstance(by, list) else [by]
        g = df.groupby(key)[y]
        summary = g.agg([
            ('n', 'count'), ('mean', 'mean'), ('std', 'std'),
            ('median', 'median'), ('min', 'min'), ('max', 'max'),
            ('q25', lambda x: x.quantile(0.25)), ('q75', lambda x: x.quantile(0.75)),
        ])
        summary['sem'] = summary['std'] / np.sqrt(summary['n'])
        self.log_table("Descriptive statistics", summary, round_digits=3)
        return summary


    # normalidade (Shapiro) por grupo
    def normality_ok(self, df: pd.DataFrame, factors: list[str], y: str,
                     min_n: int = 3, return_table: bool = False):
        """Shapiro por célula: factors=['grupo'] (one-way) ou ['A','B'] (two-way)."""
        alpha = self.alpha
        ok = True
        rows = []
        levels = [df[c].dropna().unique() for c in factors]
        for combo in product(*levels):
            mask = pd.Series(True, index=df.index)
            label_parts = []
            for col, val in zip(factors, combo):
                mask &= (df[col] == val)
                label_parts.append(f"{col}={val}")
            label = " x ".join(label_parts)

            vals = df.loc[mask, y].dropna()
            if len(vals) >= min_n:
                stat, p = shapiro(vals)
                self.log(f"Shapiro | {label} | n={len(vals)} | W={stat:.4f} | p={p:.4f}")
                rows.append({"cell": label, "n": len(vals), "W": stat, "p": p})
                if p < alpha:
                    ok = False
            else:
                self.log(f"Shapiro | {label} | n={len(vals)} | skipped because n<{min_n}")
                rows.append({"cell": label, "n": len(vals), "W": None, "p": None})

        if return_table:
            return ok, pd.DataFrame(rows)
        return ok

    def homoscedasticity_ok(self, df: pd.DataFrame, factors: list[str], y: str):
        """Levene entre células definidas por 1 ou 2 fatores."""
        alpha = self.alpha
        groups = []
        levels = [df[c].dropna().unique() for c in factors]
        for combo in product(*levels):
            mask = pd.Series(True, index=df.index)
            for col, val in zip(factors, combo):
                mask &= (df[col] == val)
            groups.append(df.loc[mask, y].dropna())

        if any(len(g) == 0 for g in groups):
            self.log("Levene | skipped because at least one group/cell is empty | result=NOT OK")
            return False

        stat, p = levene(*groups)
        self.log(f"Levene | statistic={stat:.4f} | p={p:.4f} | result={'OK' if p >= alpha else 'NOT OK'}")
        return p >= alpha


    def tukey(self, df: pd.DataFrame, value_col: str, group_col: str,
              alpha: float | None = None,
              pairs_of_interest: set[tuple[str, str]] | None = None) -> pd.DataFrame:
        """
        Tukey HSD: p-values já ajustados (FWER). Se pairs_of_interest for dado, apenas filtra.
        Retorna DataFrame com ['group1','group2','p_tukey','reject_H0'].
        """
        alpha = self.alpha if alpha is None else alpha
        tukey = pairwise_tukeyhsd(endog=df[value_col], groups=df[group_col], alpha=alpha)

        groups = list(tukey.groupsunique)
        out = pd.DataFrame({
            "group1": [groups[i] for i in tukey._multicomp.pairindices[0]],
            "group2": [groups[i] for i in tukey._multicomp.pairindices[1]],
            "p_tukey": tukey.pvalues,   # já ajustado pelo método Tukey
            "reject_H0": tukey.reject
        })

        if pairs_of_interest:
            mask = out.apply(
                lambda r: (r["group1"], r["group2"]) in pairs_of_interest or
                          (r["group2"], r["group1"]) in pairs_of_interest, axis=1
            )
            out = out.loc[mask].reset_index(drop=True)

        self.log_table("Post-hoc: Tukey HSD (FWER controlled by Tukey)", out, index=False)
        return out

    def _resolve_alpha(self, alpha: float | None) -> float:
        return self.alpha if alpha is None else alpha

    def _ensure_dir(self, out_dir: str | Path) -> Path:
        out = Path(out_dir);
        out.mkdir(parents=True, exist_ok=True);
        return out

    def _save_df(self, df: pd.DataFrame, out: Path, name: str) -> Path:
        p = out / f"{name}.csv";
        df.to_csv(p, index=False);
        return p

    def save_stats_bundle(self, out_dir, prefix,
                          main_result=None, posthoc=None, summary=None, extras: dict | None = None) -> dict:
        out = self._ensure_dir(out_dir);
        paths = {}
        # main_result: DataFrame ou (stat,p)
        if isinstance(main_result, pd.DataFrame):
            paths["main"] = self._save_df(main_result, out, f"{prefix}_main")
        elif isinstance(main_result, tuple) and len(main_result) == 2:
            paths["main"] = self._save_df(pd.DataFrame([{"stat": main_result[0], "p": main_result[1]}]),
                                          out, f"{prefix}_main")
        if isinstance(posthoc, pd.DataFrame):
            paths["posthoc"] = self._save_df(posthoc, out, f"{prefix}_posthoc")
        if isinstance(summary, pd.DataFrame):
            paths["summary"] = self._save_df(summary, out, f"{prefix}_summary")
        if extras:
            for k, v in extras.items():
                if isinstance(v, pd.DataFrame):
                    paths[k] = self._save_df(v, out, f"{prefix}_{k}")
                elif isinstance(v, np.ndarray):
                    paths[k] = self._save_df(pd.DataFrame(v), out, f"{prefix}_{k}")
        (out / f"{prefix}_meta.json").write_text(json.dumps(
            {"saved_at": datetime.now().isoformat()}, indent=2), encoding="utf-8")
        return paths

    def save_chi2(self, out_dir, prefix, global_result, posthoc: pd.DataFrame | None):
        out = self._ensure_dir(out_dir);
        ct = global_result.contingency_table
        paths = {
            "contingency": self._save_df(ct.reset_index(), out, f"{prefix}_contingency"),
            "percentages": self._save_df(global_result.percentages.reset_index(), out, f"{prefix}_percentages"),
        }
        if global_result.expected is not None:
            exp = pd.DataFrame(global_result.expected, index=ct.index, columns=ct.columns).reset_index()
            paths["expected"] = self._save_df(exp, out, f"{prefix}_expected")
        if posthoc is not None:
            paths["posthoc"] = self._save_df(posthoc, out, f"{prefix}_posthoc")
        (out / f"{prefix}_meta.json").write_text(json.dumps(
            {"chi2": global_result.chi2, "p_value": global_result.p_value,
             "saved_at": datetime.now().isoformat()}, indent=2), encoding="utf-8")
        return paths

    def save_chi2_subgroups(self, out_dir, prefix, df_results: pd.DataFrame, prop_table: pd.DataFrame) -> dict:
        out = Path(out_dir);
        out.mkdir(parents=True, exist_ok=True)
        paths = {}

        # flattens the 2x2 contingency "Table" into columns (a11..a22) before saving
        df_to_save = df_results.copy()
        if "Table" in df_to_save.columns:
            def _safe_mat(x):
                try:
                    a = np.asarray(x, dtype=int).reshape(2, 2)
                    return int(a[0, 0]), int(a[0, 1]), int(a[1, 0]), int(a[1, 1])
                except Exception:
                    return (np.nan, np.nan, np.nan, np.nan)

            a = df_to_save["Table"].apply(_safe_mat)
            df_to_save["a11"] = a.apply(lambda t: t[0])
            df_to_save["a12"] = a.apply(lambda t: t[1])
            df_to_save["a21"] = a.apply(lambda t: t[2])
            df_to_save["a22"] = a.apply(lambda t: t[3])
            df_to_save = df_to_save.drop(columns=["Table"])

        p_res = out / f"{prefix}_subgroup_results.csv"
        df_to_save.to_csv(p_res, index=False)
        paths["results"] = p_res

        p_prop = out / f"{prefix}_proportions.csv"
        prop_table.reset_index().to_csv(p_prop, index=False)
        paths["proportions"] = p_prop

        meta = {
            "saved_at": datetime.now().isoformat(),
            "n_comparisons": int(len(df_results)),
            "columns": list(df_to_save.columns),
        }
        (out / f"{prefix}_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return paths

