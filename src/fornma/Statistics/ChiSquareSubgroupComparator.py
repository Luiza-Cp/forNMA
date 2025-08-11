import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests
from fornma.Statistics.Helpers import AnalysisHelper
from typing import Tuple
from datetime import datetime
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
        self.log(f"\n=== Subgroup compare @ {datetime.now():%Y-%m-%d %H:%M:%S} ===")
        self.log(f">>> Comparando '{condition_col}' entre grupos de '{group_col}'")

        groups = df[group_col].dropna().unique().tolist()
        conditions = df[condition_col].dropna().unique().tolist()

        totals = {
            cond: int((df[condition_col] == cond).sum())
            for cond in conditions
        }

        results = []
        for grp in groups:
            self.log(f"\n▶ Grupo: {grp}")
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
                    self.log(f"⚠️ {c1} vs {c2}: tabela 2x2 degenerada (linha/coluna zero). Pulando.")
                    continue

                chi2_stat, p_chi2, _, expected = chi2_contingency(table, correction=False)
                if (expected < self.expected_min).any():
                    self.log(f"→ {c1} vs {c2}: esperado < {self.expected_min:.1f} → Fisher.")
                    try:
                        _, p_val = fisher_exact(table)
                        test = "Fisher"
                        chi2_stat = None
                    except ValueError as e:
                        self.log(f"❌ Fisher falhou ({e}). Pulando {c1} vs {c2}.")
                        continue
                else:
                    self.log(f"→ {c1} vs {c2}: usando Qui-quadrado.")
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
            self.log("\n⚠️ Nenhuma comparação válida.")
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
        rej, p_corr, _, _ = multipletests(df_results["Raw p-value"], method=method)
        df_results["Corrected p-value"] = p_corr
        df_results["Significant"] = np.where(rej, "Yes", "No")

        self.log(f"\n=== Correção múltipla: {method.upper()} ===")
        self.log(df_results.to_string(index=False))

        # Tabela de proporções estilo SPSS (% por condição)
        prop_table = (
            df.groupby([condition_col, group_col])
              .size()
              .unstack(fill_value=0)
              .pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)
              .round(2)
              .sort_index(axis=1, key=lambda idx: [str(x) for x in idx])
        )

        self.log("\n▶ Proporções (% por condição):")
        self.log(prop_table.to_string())

        return df_results, prop_table
