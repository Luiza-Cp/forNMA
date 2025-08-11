# Helpers.py
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import shapiro, levene
from itertools import product
from statsmodels.stats.multicomp import pairwise_tukeyhsd


class AnalysisHelper:
    def __init__(self, alpha: float = 0.05, log_file: str | None = None):
        self.alpha = alpha
        self.log_file = log_file

    # logging centralizado
    def log(self, msg: str):
        print(msg)
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")

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
        self.log("\n=== Descriptive statistics ===")
        self.log(summary.round(3).to_string())
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
                self.log(f"{label}: p = {p:.4f}")
                rows.append({"cell": label, "n": len(vals), "W": stat, "p": p})
                if p < alpha:
                    ok = False
            else:
                self.log(f"{label}: n<{min_n}, Shapiro ignorado")
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
            self.log("Some cells empty; treating as heteroscedastic.")
            return False

        _, p = levene(*groups)
        self.log(f"Levene p = {p:.4f}")
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

        self.log("\n=== Tukey HSD (FWER by Tukey) ===")
        self.log(out.to_string(index=False))
        return out

    def _resolve_alpha(self, alpha: float | None) -> float:
        return self.alpha if alpha is None else alpha
