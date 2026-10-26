import numpy as np
import pandas as pd

from statsmodels.formula.api import ols
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import scikit_posthocs as sp

from .Helpers import AnalysisHelper
from .ScheirerRayHare import ScheirerRayHare


class TwoWayAnalysis:
    def __init__(self, df: pd.DataFrame, numeric_col: str, group_col1: str, group_col2: str,
                 alpha: float = 0.05, pairs_of_interest=None, log_file: str | None = None,
                 helper: AnalysisHelper | None = None):
        self.df = df.copy()
        self.numeric_col = numeric_col
        self.group_col1 = group_col1
        self.group_col2 = group_col2
        self.alpha = alpha
        self.pairs_of_interest = set(pairs_of_interest or [])
        self.helper = helper or AnalysisHelper(alpha=alpha, log_file=log_file)
        self.log = self.helper.log
        self.results: dict = {}

        # coluna combinada para pós-testes em células
        self.df["group"] = self.df[self.group_col1].astype(str) + " | " + self.df[self.group_col2].astype(str)

    # -------- auxiliares (delegam ao helper) --------
    def descriptive(self) -> pd.DataFrame:
        return self.helper.descriptive(self.df, by=[self.group_col1, self.group_col2], y=self.numeric_col)

    def normality_ok(self) -> bool:
        return self.helper.normality_ok(self.df, factors=[self.group_col1, self.group_col2], y=self.numeric_col)

    def homoscedasticity_ok(self) -> bool:
        return self.helper.homoscedasticity_ok(self.df, factors=[self.group_col1, self.group_col2], y=self.numeric_col)

    # -------- ANOVA 2 vias + Tukey (sem dupla correção) --------
    def run_two_way_anova(self):
        self.helper.log_section("Main test: Two-way ANOVA (Type II)")
        formula = f"{self.numeric_col} ~ C({self.group_col1}) * C({self.group_col2})"
        model = ols(formula, data=self.df).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        self.helper.log_table("ANOVA table", anova_table)

        posthoc = None
        if (anova_table["PR(>F)"] < self.alpha).any():
            self.log("Post-hoc: Tukey HSD will run because at least one effect is significant.")
            posthoc = self.helper.tukey(
                df=self.df,
                value_col=self.numeric_col,
                group_col="group",
                alpha=self.alpha,
                pairs_of_interest=self.pairs_of_interest or None
            )
        else:
            self.log("Post-hoc: not run because no ANOVA effect was significant.")

        # (opcional) correção Bonferroni nos 3 efeitos (A, B, A:B)
        pvals = anova_table["PR(>F)"].astype(float).values
        pval_corr = multipletests(pvals, method="bonferroni")[1]
        self.results["pval_corr"] = pval_corr

        return anova_table, posthoc

    # -------- Dunn (com/sem pairs_of_interest) --------
    def dunn_post_hoc(self):
        self.helper.log_section("Post-hoc: Dunn test")

        def _ordenar_par(a, b):
            return tuple(sorted([str(a), str(b)]))

        if self.pairs_of_interest:
            self.log("Mode: pairs of interest only.")
            comps_ordenados = {_ordenar_par(x, y) for (x, y) in self.pairs_of_interest}
            grupos_desejados = sorted({g for par in comps_ordenados for g in par})

            df_pares = self.df[self.df["group"].isin(grupos_desejados)].copy()
            dunn_raw = sp.posthoc_dunn(df_pares, val_col=self.numeric_col, group_col="group", p_adjust=None)

            tri = dunn_raw.where(np.triu(np.ones(dunn_raw.shape), k=1).astype(bool))
            dunn_long = tri.stack().reset_index()
            dunn_long.columns = ['grupo1', 'grupo2', 'p_raw']
            dunn_long['par'] = dunn_long.apply(lambda r: _ordenar_par(r['grupo1'], r['grupo2']), axis=1)
            dunn_long = dunn_long[dunn_long['par'].isin(comps_ordenados)].reset_index(drop=True)

            if not dunn_long.empty:
                reject, p_adj, _, _ = multipletests(dunn_long['p_raw'].values, method='bonferroni', alpha=self.alpha)
                dunn_long['p_ajustado'] = p_adj
                dunn_long['significativo'] = reject
            else:
                dunn_long['p_ajustado'] = []
                dunn_long['significativo'] = []

            dunn_matrix = None
            letters_df = None
            self.helper.log_table("Dunn results", dunn_long.drop(columns=['par']), index=False)

        else:
            self.log("Mode: full matrix with Bonferroni adjustment.")
            dunn_matrix = sp.posthoc_dunn(self.df, val_col=self.numeric_col, group_col="group", p_adjust="bonferroni")

            dunn_long = (dunn_matrix.reset_index()
                         .melt(id_vars='index', var_name='grupo2', value_name='p_ajustado')
                         .rename(columns={'index': 'grupo1'}))
            dunn_long = dunn_long[dunn_long['grupo1'] != dunn_long['grupo2']].reset_index(drop=True)
            dunn_long['significativo'] = dunn_long['p_ajustado'] < self.alpha

            letters_bin = sp.sign_table(dunn_matrix)
            letters_df = letters_bin.copy()
            letters_df['CLD'] = letters_df.apply(lambda row: ''.join(letters_df.columns[row == 1]), axis=1)
            letters_df = letters_df[['CLD']].reset_index().rename(columns={'index': 'grupo'})

            dunn_long = (dunn_long
                         .merge(letters_df, left_on='grupo1', right_on='grupo', how='left')
                         .rename(columns={'CLD': 'CLD1'}).drop(columns=['grupo'])
                         .merge(letters_df, left_on='grupo2', right_on='grupo', how='left')
                         .rename(columns={'CLD': 'CLD2'}).drop(columns=['grupo']))

            self.helper.log_table("Dunn results", dunn_long, index=False)
            self.helper.log_table("Compact letter display", letters_df, index=False)

        # salvar
        self.results['dunn'] = dunn_long
        self.results['dunn_matrix'] = dunn_matrix
        self.results['dunn_letters'] = letters_df
        return dunn_long

    # -------- Orquestrador --------
    def run(self):
        self.helper.log_header(
            "Two-way comparison",
            numeric_column=self.numeric_col,
            factor_a=self.group_col1,
            factor_b=self.group_col2,
            alpha=self.alpha,
        )

        summary = self.descriptive()
        self.results['summary_stats'] = summary.reset_index()
        self.helper.log_section("Assumption checks")
        norm = self.normality_ok()
        homo = self.homoscedasticity_ok()

        self.helper.log_section("Decision")
        self.helper.log_kv("Normality", "OK" if norm else "NOT OK")
        self.helper.log_kv("Homoscedasticity", "OK" if homo else "NOT OK")

        if norm and homo:
            self.helper.log_kv("Selected test", "Two-way ANOVA")
            anova_table, tukey_df = self.run_two_way_anova()
            main = anova_table
            post = tukey_df
        else:
            self.helper.log_kv("Selected test", "Scheirer-Ray-Hare")
            self.helper.log_section("Main test: Scheirer-Ray-Hare")
            srh = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False)
            srh.fit(data=self.df, y=self.numeric_col, x1=self.group_col1, x2=self.group_col2)
            self.results["srh"] = srh.to_dataframe()
            self.log(srh.summary())

            if hasattr(srh, "any_significant") and srh.any_significant(self.alpha):
                self.log("Post-hoc: Dunn test will run because at least one SRH effect is significant.")
                post = self.dunn_post_hoc()
            else:
                self.log("Post-hoc: not run because no SRH effect was significant.")
                post = None
            main = self.results["srh"]

        # retorno padronizado (igual à one-way)
        return {"main_result": main, "posthoc": post, "summary": self.results['summary_stats']}

    # -------- QoL --------
    def descriptors(self):
        """(mantido p/ compatibilidade) gera summary_stats e retorna."""
        descritores = (
            self.df.groupby("group")[self.numeric_col]
            .agg(
                n="count",
                mean="mean",
                std="std",
                sem=lambda x: x.std() / np.sqrt(x.count()) if x.count() > 0 else np.nan,
                median="median",
                min="min",
                max="max",
                q25=lambda x: x.quantile(0.25),
                q75=lambda x: x.quantile(0.75),
            )
            .reset_index()
        )
        self.results['summary_stats'] = pd.DataFrame(descritores)
        self.log(self.results['summary_stats'].to_string(index=False))
        return self.results['summary_stats']

    def get_results(self) -> dict:
        """Retorna todo o dicionário de resultados acumulados."""
        return self.results

    def reset(self):
        """Limpa resultados, mantendo dados/params."""
        self.results = {}


if __name__=='__main__':
    dados_geminina = pd.read_csv(
        'data/example.csv',
        index_col=0)

    helper = AnalysisHelper(alpha=0.05)
    ana2 = TwoWayAnalysis(
        df=dados_geminina,
        numeric_col="integrated_density_dapi",
        group_col1="Condition",
        group_col2="NMA_category",
        alpha=0.05,
        helper=helper,
    )

    # roda análise
    resultados = ana2.run()

    print("\n=== Resultado principal ===")
    print(resultados["main_result"])

    print("\n=== Pós-teste ===")
    print(resultados["posthoc"])

    print("\n=== Descritivos ===")
    print(resultados["summary"])
