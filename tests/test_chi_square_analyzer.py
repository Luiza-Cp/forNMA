# tests/statistics/test_chi_square_analyzer.py
import numpy as np
import pandas as pd
import pytest

from fornma.Statistics.ChiSquareAnalyzer import (
    ChiSquareAnalyzer,
    MonteCarloChi2Simulator,
)

# -----------------------
# Fixtures auxiliares
# -----------------------
class HelperMock:
    def __init__(self):
        self.messages = []
    def log(self, msg: str):
        self.messages.append(msg)

@pytest.fixture
def helper():
    return HelperMock()

@pytest.fixture
def analyzer(helper):
    # default: usa exact quando esperado < 5
    return ChiSquareAnalyzer(
        expected_min=5.0,
        use_exact=True,
        simulator=MonteCarloChi2Simulator(num_simulations=1000, seed=123),
        helper=helper,
        log_file=None,  # se o seu helper já grava em arquivo, mantenha None aqui
    )

# Dataset com esperados adequados (assintótico)
@pytest.fixture
def df_ok():
    # 3 condições x 3 categorias, contagens razoáveis
    data = []
    rng = np.random.default_rng(0)
    conditions = ["A", "B", "C"]
    cats = ["round", "irregular", "lobed"]
    for cond in conditions:
        # cada condição com 90 observações, distribuídas
        counts = rng.multinomial(90, [0.4, 0.4, 0.2])
        for cat, c in zip(cats, counts):
            data += [{"Condition": cond, "NMA_category": cat}] * int(c)
    return pd.DataFrame(data)

# Dataset que causa Fisher em pares 2x2 (esperado baixo)
@pytest.fixture
def df_low():
    # 2 condições x 2 categorias, com célula pequena
    data = (
        [{"Condition": "A", "NMA_category": "round"}] * 30 +
        [{"Condition": "A", "NMA_category": "irregular"}] * 1 +
        [{"Condition": "B", "NMA_category": "round"}] * 2 +
        [{"Condition": "B", "NMA_category": "irregular"}] * 25
    )
    return pd.DataFrame(data)

# -----------------------
# Testes: global_test
# -----------------------

def test_global_assintotico(df_ok, tmp_path):

    log_path = tmp_path / "log.txt"
    analyzer = ChiSquareAnalyzer(
        expected_min=5.0,
        use_exact=True,
        simulator=MonteCarloChi2Simulator(num_simulations=1000, seed=123),
        log_file=str(log_path),   # <- no __init__
        helper=None,              # cria AnalysisHelper(log_file=...)
    )

    res = analyzer.global_test(df_ok, group_col="Condition", category_col="NMA_category")

    assert np.isscalar(res.chi2)
    assert 0.0 <= res.p_value <= 1.0
    assert res.percentages.shape == res.contingency_table.shape

    # log gerado?
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8").strip()
    assert len(content) > 0

def test_global_exato_via_monkeypatch(analyzer, df_ok, monkeypatch):
    # Força caminho Monte Carlo retornando p fixo
    called = {"flag": False}
    def fake_p_value(_table):
        called["flag"] = True
        return 0.1234

    monkeypatch.setattr(MonteCarloChi2Simulator, "p_value", lambda self, table: fake_p_value(table))
    # também força a condição esperados < expected_min elevando o limiar
    analyzer.expected_min = 1e9

    res = analyzer.global_test(df_ok, group_col="Condition", category_col="NMA_category")
    assert called["flag"] is True
    assert abs(res.p_value - 0.1234) < 1e-9

# -----------------------
# Testes: pairwise_posthoc
# -----------------------

def test_posthoc_assintotico(analyzer, df_ok):
    res = analyzer.global_test(df_ok, group_col="Condition", category_col="NMA_category")
    df_post = analyzer.pairwise_posthoc(res.contingency_table, correction_method="bonferroni")
    assert df_post is not None
    # 3 condições -> 3 pares
    assert len(df_post) == 3
    assert set(df_post.columns) >= {"Comparison", "test_type", "p_raw", "p_corrected", "reject_null"}

def test_posthoc_fisher_2x2(analyzer, df_low):
    # força tratar como "esperado baixo"
    analyzer.expected_min = 100

    res = analyzer.global_test(df_low, group_col="Condition", category_col="NMA_category")
    df_post = analyzer.pairwise_posthoc(res.contingency_table, correction_method="bonferroni")

    assert df_post is not None
    assert len(df_post) == 1
    assert df_post.loc[0, "test_type"].lower().startswith("fisher")

def test_posthoc_monte_carlo_forcado(analyzer, df_ok, monkeypatch):
    # Força Monte Carlo nos pares elevando expected_min e retornando p fixo
    analyzer.expected_min = 1e9
    monkeypatch.setattr(MonteCarloChi2Simulator, "p_value", lambda self, tbl: 0.042)

    res = analyzer.global_test(df_ok, group_col="Condition", category_col="NMA_category")
    df_post = analyzer.pairwise_posthoc(res.contingency_table, correction_method="auto")
    assert df_post is not None
    assert (df_post["test_type"].str.lower() == "monte carlo").any()
    # todos os p_raw devem ser 0.042 (porque monkeypatchou)
    assert np.allclose(df_post["p_raw"], 0.042)

# -----------------------
# Teste com dados reais
# -----------------------

@pytest.mark.parametrize("csv_path", ["tests/data/statistics/dados_fig_2.csv"])
def test_real_data_condition_vs_nma(analyzer, csv_path):
    df = pd.read_csv(csv_path)
    assert {"Condition", "NMA_category"} <= set(df.columns), "CSV deve ter colunas Condition e NMA_category"

    res = analyzer.global_test(df, group_col="Condition", category_col="NMA_category")

    # garante outputs básicos
    assert isinstance(res.chi2, (int, float))
    assert 0.0 <= res.p_value <= 1.0
    assert res.contingency_table.shape[0] >= 2  # pelo menos 2 condições
    assert res.contingency_table.shape[1] >= 2  # pelo menos 2 categorias

    # Se global for significativo, faz post-hoc
    if res.p_value < 0.05:
        df_post = analyzer.pairwise_posthoc(res.contingency_table, correction_method="auto")
        assert df_post is not None
        # As “diferenças na NMA_category na Condition” estarão marcadas em reject_null
        assert {"Comparison", "p_corrected", "reject_null"} <= set(df_post.columns)
    else:
        # Mesmo sem significância global, os resultados percentuais são úteis
        assert res.percentages.notna().any().any()
