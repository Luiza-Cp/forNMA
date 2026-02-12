import numpy as np
import pandas as pd
from scipy.stats import shapiro, levene, kruskal
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
from datetime import datetime
from .Helpers import AnalysisHelper


class OneWayAnalysis:
    def __init__(self, df: pd.DataFrame, numeric_col: str, group_col: str,
                 alpha: float = 0.05, pairs_of_interest=None,  log_file: str | None = None,
                 helper: AnalysisHelper | None = None):
        self.df = df
        self.numeric_col = numeric_col
        self.group_col = group_col
        self.alpha = alpha
        self.pairs_of_interest = set(pairs_of_interest or [])
        self.log_file = log_file
        self.helper = helper or AnalysisHelper(alpha=alpha, log_file=log_file)
        self.log = self.helper.log

    # -------- helpers --------
    def descriptive(self) -> pd.DataFrame:
        return self.helper.descriptive(self.df, [self.group_col], self.numeric_col)


    def normality_ok(self) -> bool:
        return self.helper.normality_ok(self.df, [self.group_col], self.numeric_col)


    def homoscedasticity_ok(self):
        return self.helper.homoscedasticity_ok(self.df, [self.group_col], self.numeric_col)

    def dunn_posthoc(self, p_adjust_method: str = "bonferroni") -> pd.DataFrame:
        """Dunn via scikit-posthocs: com/sem pairs_of_interest como combinado."""
        import scikit_posthocs as sp  # lazy import

        if self.pairs_of_interest:
            self.log("\n=== Dunn (pairs of interest; fit only on these pairs) ===")
            # p crus
            dunn = sp.posthoc_dunn(self.df, val_col=self.numeric_col,
                                   group_col=self.group_col, p_adjust=None)
            # upper triangular -> long
            tri = dunn.where(np.triu(np.ones(dunn.shape), k=1).astype(bool))
            melted = tri.stack().reset_index()
            melted.columns = ["group1", "group2", "p_raw"]

            # filtra pelos pares definidos
            mask = melted.apply(
                lambda r: (r["group1"], r["group2"]) in self.pairs_of_interest or
                          (r["group2"], r["group1"]) in self.pairs_of_interest, axis=1
            )
            filtered = melted.loc[mask].reset_index(drop=True)

            if not filtered.empty:
                reject, p_adj, _, _ = multipletests(filtered["p_raw"],
                                                    method=p_adjust_method,
                                                    alpha=self.alpha)
                filtered["p_adjusted"] = p_adj
                filtered["reject_H0"] = reject
            else:
                filtered["p_adjusted"] = []
                filtered["reject_H0"] = []

            self.log(filtered.to_string(index=False))
            return filtered

        else:
            self.log(f"\n=== Dunn (full matrix; p_adjust='{p_adjust_method}') ===")
            dunn = sp.posthoc_dunn(self.df, val_col=self.numeric_col,
                                   group_col=self.group_col, p_adjust=p_adjust_method)  # já ajustado
            self.log(dunn.to_string())
            return dunn


    # -------- main tests --------
    def run_anova(self):
        self.log("\n>>> One-way ANOVA")
        model = ols(f'{self.numeric_col} ~ C({self.group_col})', data=self.df).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        self.log(anova_table.to_string())
        p = float(anova_table['PR(>F)'].iloc[0])
        if p < self.alpha:
            posthoc = self.helper.tukey(
                df=self.df, value_col=self.numeric_col, group_col=self.group_col,
                alpha=self.alpha, pairs_of_interest=self.pairs_of_interest
            )
        else:
            self.log("\nANOVA not significant; no post-hoc.")
            posthoc = None

        return anova_table, posthoc

    def run_kruskal(self, grouped_vals):
        self.log("\n>>> Kruskal-Wallis")
        stat, p = kruskal(*grouped_vals)
        self.log(f"Kruskal-Wallis H = {stat:.4f}, p = {p:.4f}")
        posthoc = self.dunn_posthoc() if p < self.alpha else None
        if p >= self.alpha:
            self.log("\nKruskal not significant; no post-hoc.")
        return (stat, p), posthoc

    # -------- orchestrator --------
    def run(self):
        self.log(f"\n=== On {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        self.log(f">>> Anova analysis of '{self.numeric_col}' between '{self.group_col}'")

        summary = self.descriptive()
        norm = self.normality_ok()
        homo = self.homoscedasticity_ok()

        if norm and homo:
            self.log("\n✅ Assumptions met. Performing one-way ANOVA...")
            main, post = self.run_anova()
        else:
            self.log("\n⚠️ Assumptions violated. Performing Kruskal-Wallis...")
            grouped = [self.df[self.df[self.group_col] == group][self.numeric_col] for group in self.df[self.group_col].unique()]
            main, post = self.run_kruskal(grouped)

        return {"main_result": main, "posthoc": post, "summary": summary}



if __name__ == '__main__':
    dados_geminina = pd.read_csv(
        '/media/luiza/DATA/Doutorado/forNMA/experimentos/Nicolas/Dado Tiago 2023/2 53BP1-NB/Results/Results C/Results complete.csv',
        index_col=0)
    helper = AnalysisHelper(alpha=0.05, log_file="logs.txt")

    ana = OneWayAnalysis(
        df=dados_geminina,
        numeric_col="integrated_density_dapi",
        group_col="Condition",
        alpha=0.05,
        helper=helper,  # injeta o helper
    )
    ana.run()
