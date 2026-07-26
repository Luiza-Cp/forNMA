import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests
from .Helpers import AnalysisHelper
from typing import Tuple
from itertools import combinations

# =========================
# Comparações por subgrupo
# =========================
class ChiSquareSubgroupComparator:
    """
    Para cada categoria em `group_col`, compara proporções entre pares de níveis de `condition_col`
    (2x2 por categoria), usando qui-quadrado ou Fisher conforme esperados.
    """

    def __init__(
        self,
        expected_min: float = 5.0,
        correction_method: str = "bonferroni",
        log_file: str | None = None,
        helper: AnalysisHelper | None = None,
    ):
        self.expected_min = float(expected_min)
        self.correction_method = correction_method
        self.helper = helper or AnalysisHelper(log_file=log_file)
        self.log = self.helper.log

    def compare(
        self,
        df: pd.DataFrame,
        group_col: str,
        condition_col: str,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        self.helper.log_header(
            "Chi-square subgroup comparison",
            subgroup_column=group_col,
            condition_column=condition_col,
            expected_minimum=self.expected_min,
        )

        groups = df[group_col].dropna().unique().tolist()
        conditions = df[condition_col].dropna().unique().tolist()

        totals = {
            cond: int((df[condition_col] == cond).sum())
            for cond in conditions
        }

        results = []
        self.helper.log_section("Pairwise subgroup tests")
        for grp in groups:
            self.log(f"Subgroup: {grp}")
            counts = {
                cond: int(((df[condition_col] == cond) & (df[group_col] == grp)).sum())
                for cond in conditions
            }
            for c1, c2 in combinations(conditions, 2):
                table = np.array([
                    [counts[c1], totals[c1] - counts[c1]],
                    [counts[c2], totals[c2] - counts[c2]],
                ], dtype=int)

                # logo após construir `table`
                row_sums = table.sum(axis=1)
                col_sums = table.sum(axis=0)

                # pula qualquer 2x2 degenerado: alguma linha OU alguma coluna com soma zero
                if (row_sums == 0).any() or (col_sums == 0).any():
                    self.log(f"{grp} | {c1} vs {c2} | skipped because the 2x2 table has a zero row or column.")
                    continue

                chi2_stat, p_chi2, _, expected = chi2_contingency(table, correction=False)
                if (expected < self.expected_min).any():
                    self.log(f"{grp} | {c1} vs {c2} | selected test=Fisher exact | reason=low expected count")
                    try:
                        _, p_val = fisher_exact(table)
                        test = "Fisher"
                        chi2_stat = None
                    except ValueError as e:
                        self.log(f"{grp} | {c1} vs {c2} | skipped because Fisher exact failed: {e}")
                        continue
                else:
                    self.log(f"{grp} | {c1} vs {c2} | selected test=Chi-square")
                    p_val = p_chi2
                    test = "Chi-square"

                results.append({
                    "Group": grp,
                    "Comparison": f"{c1} vs {c2}",
                    "Test": test,
                    "Chi-square Statistic": chi2_stat,
                    "Raw p-value": p_val,
                    "Table": table,
                })

        df_results = pd.DataFrame(results)
        if df_results.empty:
            self.log("No valid subgroup comparison.")
            # também retorna a tabela de proporções vazia
            prop_table = (
                df.groupby([condition_col, group_col])
                  .size()
                  .unstack(fill_value=0)
                  .pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
                  .round(2)
            )
            return df_results, prop_table

        method = (self.correction_method if self.correction_method != "auto"
                  else ("fdr_bh" if len(df_results) > 3 else "bonferroni"))
        self.helper.log_section("Multiple-comparison correction")
        self.helper.log_kv("Correction method", method)
        rej, p_corr, _, _ = multipletests(df_results["Raw p-value"], method=method)
        df_results["Corrected p-value"] = p_corr
        df_results["Significant"] = np.where(rej, "Yes", "No")

        self.helper.log_table("Subgroup comparison results", df_results, index=False)

        # Tabela de proporções estilo SPSS (% por condição)
        prop_table = (
            df.groupby([condition_col, group_col])
              .size()
              .unstack(fill_value=0)
              .pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
              .round(2)
              .sort_index(axis=1, key=lambda idx: [str(x) for x in idx])
        )

        self.helper.log_table("Proportions (% per condition)", prop_table)

        return df_results, prop_table
