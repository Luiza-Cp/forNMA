# ScheirerRayHare.py

import re
import warnings
import pandas as pd
import numpy as np
from scipy.stats import rankdata, chi2
import statsmodels.api as sm
import statsmodels.formula.api as smf


class ScheirerRayHare:
    """
    Object-oriented interface for performing the Scheirer–Ray–Hare (SRH) test,
    a non-parametric extension of the Kruskal–Wallis test for two-way factorial
    designs, with or without interaction terms.

    Features
    --------
    - Maintains default parameters (`type`, `tie_correct`, `ss`, `verbose`).
    - Stores the state of the last fitted model (cleaned data, ranked response,
      cell-size table, ANOVA results, correction factors).
    - Provides extension points for future features (permutation p-values,
      effect sizes, plots, export).

    Statistical background
    ----------------------
    SRH ranks the dependent variable across all observations and fits a two-way
    OLS model to the ranks. Sum of squares per term are scaled by n(n+1)/12 to
    yield H-Statistics; an optional tie correction (based on duplicate values in y)
    is applied to adjust H.

    Types of sums of squares
    ------------------------
    - Type I (sequential): each effect is tested after those entered before it.
    - Type II (hierarchical): each main effect is tested after the other main effect,
      ignoring the interaction; commonly recommended for unbalanced designs.
    - Type III: each effect is tested after all other effects (including interaction).
      To match R’s behaviour, we fit with sum contrasts.

    Reference
    ---------
    Inspired by the R function `scheirerRayHare` from the `rcompanion` package:
    https://search.r-project.org/CRAN/refmans/rcompanion/html/scheirerRayHare.html
    """

    def __init__(self, type=2, tie_correct=True, ss=True, verbose=True):
        self.type = type
        self.tie_correct = tie_correct
        self.ss = ss
        self.verbose = verbose

        # filled after fit()
        self.result_ = None
        self.yname_ = None
        self.x1name_ = None
        self.x2name_ = None
        self.n_ = None
        self.D_ = None
        self.denom_ = None
        self.cell_sizes_ = None
        self._type_label = None

    def _parse_formula_or_names(self, data, formula, y, x1, x2):
        if formula is not None:
            if "~" not in formula:
                raise ValueError("Formula must be like 'y ~ x1 * x2' (or '+').")
            lhs, rhs = [s.strip() for s in formula.split("~", 1)]
            yname = lhs
            # extract bare variable names, preserve order
            base_terms = [t.strip() for t in re.split(r'[\+\*\:]', rhs) if t.strip()]
            seen = set()
            base_terms = [t for t in base_terms if not (t in seen or seen.add(t))]
            if len(base_terms) < 2:
                raise ValueError("Formula must include two factors on the RHS (x1 and x2).")
            x1name, x2name = base_terms[:2]
        else:
            if not (isinstance(y, str) and isinstance(x1, str) and isinstance(x2, str)):
                raise ValueError("Provide `formula` or the names `y`, `x1`, `x2`.")
            yname, x1name, x2name = y, x1, x2

        for col in (yname, x1name, x2name):
            if col not in data:
                raise ValueError(f"Column '{col}' not found in `data`.")
        return yname, x1name, x2name

    def fit(self, data, formula=None, y=None, x1=None, x2=None):
        # 1) names
        if not isinstance(data, pd.DataFrame):
            raise ValueError("`data` must be a pandas.DataFrame.")
        yname, x1name, x2name = self._parse_formula_or_names(data, formula, y, x1, x2)

        # 2) clean & types
        df_clean = data[[yname, x1name, x2name]].dropna().copy()
        if df_clean.empty:
            raise ValueError("No data left after dropping NAs.")
        df_clean[x1name] = df_clean[x1name].astype("category")
        df_clean[x2name] = df_clean[x2name].astype("category")

        x1_vals = df_clean[x1name]
        x2_vals = df_clean[x2name]
        lev1 = x1_vals.cat.categories
        lev2 = x2_vals.cat.categories

        # abortar desenho degenerado (antes de montar modelo)
        if len(lev1) < 2 or len(lev2) < 2:
            bad = x1name if len(lev1) < 2 else x2name
            raise ValueError(
                f"Factor '{bad}' is degenerate (only one observed level). "
                "SRH requires two factors with >= 2 levels each."
            )

        # grade completa dos níveis observados (para detectar vazios)
        cell_sizes_full = (
            pd.crosstab(x1_vals, x2_vals)
            .reindex(index=lev1, columns=lev2, fill_value=0)
        )
        if (cell_sizes_full == 0).any().any():
            warnings.warn("Empty cells found (factor-level combinations with zero observations).")
        if (cell_sizes_full < 5).any().any():
            warnings.warn("Some cells have < 5 observations (rule-of-thumb warning).")

        # 3) ranks
        y_vals = df_clean[yname]
        ranks = pd.Series(rankdata(y_vals.to_numpy(), method="average"), index=df_clean.index)

        # 4) model on ranks
        df_model = pd.DataFrame({"ranks": ranks, x1name: x1_vals, x2name: x2_vals})

        t = str(self.type).upper()
        use_type = 3 if t in {"3", "III"} else 2 if t in {"2", "II"} else 1 if t in {"1", "I"} else None
        if use_type is None:
            raise ValueError("`type` must be 1/'I', 2/'II', or 3/'III'.")

        # Type III com contrasts de soma (compatível com R)
        if use_type == 3:
            f_model = f"ranks ~ C({x1name}, Sum) * C({x2name}, Sum)"
        else:
            f_model = f"ranks ~ C({x1name}) * C({x2name})"

        model = smf.ols(f_model, data=df_model).fit()

        # 5) ANOVA
        if use_type == 2:
            anova_table = sm.stats.anova_lm(model, typ=2);
            type_label = "II"
        elif use_type == 1:
            anova_table = sm.stats.anova_lm(model, typ=1);
            type_label = "I"
        else:
            anova_table = sm.stats.anova_lm(model, typ=3);
            type_label = "III"

        # manter apenas efeitos (sem residual/intercept)
        main_idx = [ix for ix in anova_table.index
                    if not ix.lower().startswith("resid")
                    and "intercept" not in ix.lower()]
        anova_main = anova_table.loc[main_idx].copy()

        # --- dfs efetivos ao estilo rcompanion (ignora combinações inexistentes) ---
        lev1_present = x1_vals.cat.remove_unused_categories().cat.categories
        lev2_present = x2_vals.cat.remove_unused_categories().cat.categories
        df_x1_eff = max(len(lev1_present) - 1, 0)
        df_x2_eff = max(len(lev2_present) - 1, 0)
        present_combos = df_clean[[x1name, x2name]].drop_duplicates().shape[0]
        df_int_eff = max(present_combos - df_x1_eff - df_x2_eff - 1, 0)

        def _clean_label(ix):
            lab = ix
            lab = lab.replace(f"C({x1name})", x1name).replace(f"C({x2name})", x2name)
            lab = lab.replace(f"C({x1name}, Sum)", x1name).replace(f"C({x2name}, Sum)", x2name)
            return re.sub(r"\s+", "", lab)

        df_terms_eff = anova_main["df"].copy()
        for ix in anova_main.index:
            lbl = _clean_label(ix)
            if ":" in lbl:
                df_terms_eff.loc[ix] = float(df_int_eff)
            elif lbl == x1name or lbl.startswith(x1name):
                df_terms_eff.loc[ix] = float(df_x1_eff)
            elif lbl == x2name or lbl.startswith(x2name):
                df_terms_eff.loc[ix] = float(df_x2_eff)

        # 6) tie correction
        n = len(ranks)
        denom = n * (n + 1) / 12.0
        if self.tie_correct:
            ties = y_vals.value_counts()
            if n < 2:
                raise ValueError("Sample too small for tie correction.")
            D = 1.0 - ((ties ** 3 - ties).sum()) / (n ** 3 - n)
            if D <= 0 or not np.isfinite(D):
                warnings.warn("Tie correction D <= 0 or not finite. Using D=1.")
                D = 1.0
        else:
            D = 1.0

        # 7) stats (com dfs efetivos)
        if "sum_sq" not in anova_main.columns:
            raise RuntimeError("ANOVA table has no 'sum_sq' column (check statsmodels version).")

        ss_terms = anova_main["sum_sq"]
        H = ss_terms / denom
        H_adj = H / D
        p_values = pd.Series(chi2.sf(H_adj.values, df_terms_eff.values),
                             index=anova_main.index)

        # 8) ordenar e empacotar (x1, x2, x1:x2)
        idx_map = [(ix, _clean_label(ix)) for ix in anova_main.index]

        def _term_key(lbl):
            if ":" in lbl: return 2
            if lbl == x1name or lbl.startswith(x1name): return 0
            if lbl == x2name or lbl.startswith(x2name): return 1
            return 99

        order = sorted(idx_map, key=lambda t: _term_key(t[1]))
        ordered_raw = [t[0] for t in order]
        ordered_clean = [t[1] for t in order]

        out = pd.DataFrame({
            "df": df_terms_eff.loc[ordered_raw].values,
            "H": H.loc[ordered_raw].values,
            "H_adj": H_adj.loc[ordered_raw].values,
            "p-value": p_values.loc[ordered_raw].values,
        }, index=ordered_clean)

        if "p" not in out.columns and "p-value" in out.columns:
            out["p"] = out["p-value"]  # facilita integrações

        # store attrs
        self.result_ = out
        self.yname_, self.x1name_, self.x2name_ = yname, x1name, x2name

        if self.ss:
            out.insert(1, "sum_sq", ss_terms.loc[ordered_raw].values)

        # linha Residuals
        resid_idx = "Residual" if "Residual" in anova_table.index else \
            "Residuals" if "Residuals" in anova_table.index else None
        if resid_idx is not None:
            resid_df = float(anova_table.loc[resid_idx, "df"])
            resid_ss = float(anova_table.loc[resid_idx, "sum_sq"]) if self.ss else None
        else:
            resid_df = float(model.df_resid)
            resid_ss = float("nan") if self.ss else None

        residuals_row = pd.DataFrame({
            "df": [resid_df],
            **({"sum_sq": [resid_ss]} if self.ss else {}),
            "H": [np.nan],
            "H_adj": [np.nan],
            "p-value": [np.nan]
        }, index=["Residuals"])
        out = pd.concat([out, residuals_row], axis=0)

        # store attrs
        self.result_ = out
        self.yname_, self.x1name_, self.x2name_ = yname, x1name, x2name
        self.n_, self.D_, self.denom_ = n, D, denom
        self.cell_sizes_ = cell_sizes_full
        self._type_label = type_label

        if self.verbose:
            print("\nScheirer–Ray–Hare (SRH) test")
            print(f"Dependent variable  : {yname}")
            print(f"Factors             : {x1name}, {x2name}")
            print(f"N observations      : {n}")
            print(f"SS Type (ANOVA)     : {type_label}")
            print(f"Tie correction      : {'Yes' if self.tie_correct else 'No'} (D = {D:.7f})")
            print("Cell sizes (x1 by x2):")
            print(cell_sizes_full)
            print(f"\nSRH denominator (MS total) : {denom:.0f}\n")

        return self

    def to_dataframe(self):
        if self.result_ is None:
            raise RuntimeError("Call .fit() before .to_dataframe().")
        return self.result_.copy()


    # --- utilitários de saída/decisão ---
    def summary(self) -> str:
        """Retorna string com a tabela (não imprime)."""
        if self.result_ is None:
            raise RuntimeError("Call .fit() before .summary().")
        return self.result_.to_string()


    def effects_significant(self, alpha: float = 0.05) -> dict[str, bool]:
        """Dict com significância dos efeitos principais e da interação."""
        if self.result_ is None:
            raise RuntimeError("Call .fit() before .effects_significant().")
        # normaliza nomes
        idx = self.result_.index.astype(str)
        pcol = "p" if "p" in self.result_.columns else ("p-value" if "p-value" in self.result_.columns else None)
        if pcol is None:
            raise RuntimeError("SRH table must contain a 'p' or 'p-value' column.")
        # labels esperados
        a = self.x1name_
        b = self.x2name_
        inter = f"{a}:{b}"
        # pega p por label
        def get_p(lbl):
            m = self.result_.loc[idx == lbl, pcol]
            return float(m.iloc[0]) if not m.empty else None
        pa = get_p(a); pb = get_p(b); pint = get_p(inter)
        return {
            a: (pa is not None and pa < alpha),
            b: (pb is not None and pb < alpha),
            inter: (pint is not None and pint < alpha),
        }


    def any_significant(self, alpha: float = 0.05) -> bool:
        """True se qualquer efeito principal ou interação for significativo."""
        return any(self.effects_significant(alpha).values())



if __name__ == "__main__":
    # data from Sokal & Rohlf (1995)
    Value = [709, 679, 699, 657, 594, 677, 592, 538, 476, 508, 505, 539]
    Sex   = ["Male"]*3 + ["Female"]*3 + ["Male"]*3 + ["Female"]*3
    Fat   = ["Fresh"]*6 + ["Rancid"]*6
    df = pd.DataFrame({"Value": Value, "Sex": Sex, "Fat": Fat})


    srh = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=True)
    srh.fit(data=df, formula="Value ~ Sex * Fat")
    srh.summary()



