# fornma/Statistics/ChiSquare.py

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from itertools import combinations
from datetime import datetime
from typing import Optional, Tuple, List, Dict

from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.multitest import multipletests

from fornma.Statistics.Helpers import AnalysisHelper

# =========================
# Simulador Monte Carlo
# =========================
@dataclass
class MonteCarloChi2Simulator:
    """
    Simula p-valor exato (Monte Carlo) para qui-quadrado de independência,
    mantendo os totais marginais fixos via embaralhamento de rótulos de coluna.
    """
    num_simulations: int = 10_000
    seed: int = 42

    def p_value(self, observed: np.ndarray) -> float:
        rng = np.random.default_rng(self.seed)
        observed = np.asarray(observed, dtype=int)

        if observed.ndim != 2 or observed.size == 0:
            raise ValueError("`observed` deve ser uma matriz 2D não vazia.")

        # margens não podem ter totais zero
        if np.any(observed.sum(axis=0) == 0) or np.any(observed.sum(axis=1) == 0):
            raise ValueError("Tabela com linha ou coluna de total zero — não é possível simular.")

        try:
            chi2_obs, *_ = chi2_contingency(observed, correction=False)
        except ValueError as e:
            raise ValueError(f"Não foi possível calcular chi2 nos dados observados: {e}")

        # constrói rótulos conforme margens
        row_labels = np.repeat(np.arange(observed.shape[0]), observed.sum(axis=1))
        col_labels = np.repeat(np.arange(observed.shape[1]), observed.sum(axis=0))

        more_extreme = 0
        simulated = np.zeros_like(observed, dtype=int)

        for _ in range(self.num_simulations):
            simulated.fill(0)
            rng.shuffle(col_labels)
            # reconstrói a tabela simulada
            for r, c in zip(row_labels, col_labels):
                simulated[r, c] += 1

            try:
                chi2_sim, *_ = chi2_contingency(simulated, correction=False)
                if chi2_sim >= chi2_obs:
                    more_extreme += 1
            except ValueError:
                # ignora desenhos degenerados
                continue

        # ajuste +1 para evitar zero
        return (more_extreme + 1) / (self.num_simulations + 1)


# =========================
# Resultado estruturado
# =========================
@dataclass
class GlobalChi2Result:
    chi2: float
    p_value: float
    contingency_table: pd.DataFrame
    expected: Optional[np.ndarray]
    percentages: pd.DataFrame  # col-wise (% por coluna, estilo SPSS)


# =========================
# Analisador principal
# =========================
class ChiSquareAnalyzer:
    """
    Faz:
      - teste global de associação (qui-quadrado ou exato via Monte Carlo)
      - post-hoc pareado entre níveis de `group_col`
    """

    def __init__(
        self,
        expected_min: float = 5.0,
        use_exact: bool = True,
        simulator: Optional[MonteCarloChi2Simulator] = None,
        log_file: str | None = None,
        helper: AnalysisHelper | None = None,

    ):
        self.expected_min = float(expected_min)
        self.use_exact = bool(use_exact)
        self.simulator = simulator or MonteCarloChi2Simulator()
        self.helper =  helper or AnalysisHelper( log_file=log_file)
        self.log = self.helper.log

    # ---------- util ----------
    @staticmethod
    def _percent_table_by_column(ct: pd.DataFrame) -> pd.DataFrame:
        return ct.div(ct.sum(axis=0), axis=1).replace([np.inf, -np.inf], np.nan) * 100

    @staticmethod
    def _auto_method(n_tests: int) -> str:
        return "fdr_bh" if n_tests > 3 else "bonferroni"

    # ---------- público ----------
    def global_test(
        self,
        df: pd.DataFrame,
        group_col: str,
        category_col: str,
    ) -> GlobalChi2Result:
        self.log(f"\n=== Início: {datetime.now():%Y-%m-%d %H:%M:%S} ===")
        self.log(f">>> Qui-quadrado de '{category_col}' por '{group_col}'")

        # Tabela de contingência
        ct = pd.crosstab(df[group_col], df[category_col])
        pct = self._percent_table_by_column(ct)

        self.log("\n▶ Contagens:")
        self.log(ct.to_string())
        self.log("\n▶ % por coluna:")
        self.log(pct.round(2).to_string())

        # Teste global (assintótico ou exato)
        chi2_asym, p_asym, _, expected = chi2_contingency(ct)
        expected_min_val = expected.min() if expected is not None else np.nan

        if self.use_exact and expected_min_val < self.expected_min:
            self.log(f"\n⚠️ Esperado < {self.expected_min:.1f}. Usando Monte Carlo para p-valor global.")
            chi2 = chi2_contingency(ct, correction=False)[0]  # estatística observada sem correção
            p_value = self.simulator.p_value(ct.values)
        else:
            self.log("\n✅ Premissas atendidas. Usando qui-quadrado assintótico.")
            chi2, p_value = chi2_asym, p_asym

        self.log("\n=== Resultado Global ===")
        self.log(f"Chi² = {chi2:.4f} | p = {p_value:.4e}")

        return GlobalChi2Result(
            chi2=chi2,
            p_value=p_value,
            contingency_table=ct,
            expected=expected,
            percentages=pct,
        )

    def pairwise_posthoc(
        self,
        contingency_table: pd.DataFrame,
        correction_method: str = "auto",
    ) -> Optional[pd.DataFrame]:
        """
        Executa comparações pareadas entre linhas (níveis de group_col).
        Usa Fisher para 2x2 com esperados baixos; senão Monte Carlo se habilitado.
        Retorna DataFrame com p_raw, p_corrected, tipo de teste, etc.
        """
        ct = contingency_table
        pairs = list(combinations(ct.index, 2))
        self.log(f"\n=== Post-hoc pareado: {len(pairs)} combinações ===")

        results: List[Dict] = []

        for g1, g2 in pairs:
            sub = ct.loc[[g1, g2]]
            test_type = "Chi-square"
            chi2_stat = None

            try:
                chi2_stat, p_sub, _, expected_sub = chi2_contingency(sub)
                low = (expected_sub < self.expected_min).any()
            except ValueError as e:
                self.log(f"\n▶ {g1} vs {g2}: erro no chi2_contingency: {e}")
                low = True  # força fallback

            if low:
                if sub.shape == (2, 2):
                    self.log(f"▶ {g1} vs {g2}: esperado baixo → Fisher.")
                    _, p_val = fisher_exact(sub)
                    test_type = "Fisher"
                    chi2_stat = None
                elif self.use_exact:
                    self.log(f"▶ {g1} vs {g2}: esperado baixo → Monte Carlo.")
                    p_val = MonteCarloChi2Simulator(
                        num_simulations=self.simulator.num_simulations,
                        seed=self.simulator.seed,
                    ).p_value(sub.values)
                    test_type = "Monte Carlo"
                    chi2_stat = None
                else:
                    # se não usar exato, mantém p assintótico (se disponível)
                    if chi2_stat is None:
                        self.log(f"⚠️ {g1} vs {g2}: sem teste válido. Pulando.")
                        continue
                    p_val = p_sub
                    test_type = "Chi-square (assint.)"
            else:
                p_val = p_sub
                test_type = "Chi-square"

            self.log(f"▶ {g1} vs {g2} | Teste: {test_type} | p bruto = {p_val:.4e}")

            results.append({
                "Comparison": f"{g1} vs {g2}",
                "test_type": test_type,
                "chi2_stat": chi2_stat,
                "p_raw": p_val
            })

        if not results:
            self.log("\n⚠️ Nenhuma comparação válida.")
            return None

        df_res = pd.DataFrame(results)

        if correction_method == "auto":
            correction_method = self._auto_method(len(df_res))

        self.log(f"\n=== Correção de múltiplas comparações: {correction_method.upper()} ===")
        rej, p_corr, _, _ = multipletests(df_res["p_raw"], method=correction_method)
        df_res["p_corrected"] = p_corr
        df_res["reject_null"] = rej

        self.log("\n▶ Resumo post-hoc:")
        self.log(df_res.to_string(index=False))

        return df_res

