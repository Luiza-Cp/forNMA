import numpy as np
import pandas as pd
from scipy.stats import shapiro, levene, kruskal, mannwhitneyu, ttest_ind
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
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
            self.helper.log_section("Post-hoc: Dunn test (pairs of interest)")
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

            self.log(filtered.to_string(index=False) if not filtered.empty else "No requested pairs were found.")
            return filtered

        else:
            self.helper.log_section(f"Post-hoc: Dunn test (full matrix, p_adjust={p_adjust_method})")
            dunn = sp.posthoc_dunn(self.df, val_col=self.numeric_col,
                                   group_col=self.group_col, p_adjust=p_adjust_method)  # já ajustado
            self.log(dunn.to_string())
            return dunn


    # -------- main tests --------
    def run_anova(self):
        self.helper.log_section("Main test: One-way ANOVA")
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
            self.log("Post-hoc: not run because ANOVA was not significant.")
            posthoc = None

        return anova_table, posthoc

    def run_kruskal(self, grouped_vals):
        self.helper.log_section("Main test: Kruskal-Wallis")
        stat, p = kruskal(*grouped_vals)
        self.log(f"Statistic H={stat:.4f} | p={p:.4f}")
        posthoc = self.dunn_posthoc() if p < self.alpha else None
        if p >= self.alpha:
            self.log("Post-hoc: not run because Kruskal-Wallis was not significant.")
        return (stat, p), posthoc

    def run_ttest(self, group_names, grouped_vals, equal_var: bool):
        test_name = "Student t-test" if equal_var else "Welch t-test"
        self.helper.log_section(f"Main test: {test_name}")
        stat, p = ttest_ind(grouped_vals[0], grouped_vals[1], equal_var=equal_var, nan_policy="omit")
        self.log(f"Statistic t={stat:.4f} | p={p:.4f} | equal_variance_assumed={bool(equal_var)}")
        return pd.DataFrame([{
            "test_used": test_name,
            "group1": group_names[0],
            "group2": group_names[1],
            "statistic": float(stat),
            "p_value": float(p),
            "equal_variance_assumed": bool(equal_var),
        }]), None

    def run_mannwhitney(self, group_names, grouped_vals):
        self.helper.log_section("Main test: Mann-Whitney U")
        stat, p = mannwhitneyu(grouped_vals[0], grouped_vals[1], alternative="two-sided")
        self.log(f"Statistic U={stat:.4f} | p={p:.4f}")
        return pd.DataFrame([{
            "test_used": "Mann-Whitney U",
            "group1": group_names[0],
            "group2": group_names[1],
            "statistic": float(stat),
            "p_value": float(p),
        }]), None

    # -------- orchestrator --------
    def run(self):
        self.helper.log_header(
            "One-way comparison",
            numeric_column=self.numeric_col,
            group_column=self.group_col,
            alpha=self.alpha,
        )

        summary = self.descriptive()
        self.helper.log_section("Assumption checks")
        norm = self.normality_ok()
        homo = self.homoscedasticity_ok()
        group_names = [g for g in self.df[self.group_col].dropna().unique()]
        grouped = [self.df[self.df[self.group_col] == group][self.numeric_col].dropna() for group in group_names]
        non_empty = [(name, values) for name, values in zip(group_names, grouped) if len(values) > 0]
        group_names = [name for name, _values in non_empty]
        grouped = [values for _name, values in non_empty]

        if len(grouped) < 2:
            raise ValueError(f"At least two non-empty groups are required in '{self.group_col}'.")

        self.helper.log_section("Decision")
        self.helper.log_kv("Groups detected", len(grouped))
        self.helper.log_kv("Normality", "OK" if norm else "NOT OK")
        self.helper.log_kv("Homoscedasticity", "OK" if homo else "NOT OK")

        if len(grouped) == 2:
            if norm:
                self.helper.log_kv("Selected test", "Student t-test" if homo else "Welch t-test")
                main, post = self.run_ttest(group_names, grouped, equal_var=bool(homo))
            else:
                self.helper.log_kv("Selected test", "Mann-Whitney U")
                main, post = self.run_mannwhitney(group_names, grouped)
        else:
            if norm and homo:
                self.helper.log_kv("Selected test", "One-way ANOVA")
                main, post = self.run_anova()
            else:
                self.helper.log_kv("Selected test", "Kruskal-Wallis")
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
