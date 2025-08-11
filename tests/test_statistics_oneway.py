# tests/test_oneway_analysis_extra.py
from pathlib import Path
import os
import numpy as np
import pandas as pd
import pytest

# AJUSTE estes imports
from fornma.Statistics.Helpers import AnalysisHelper
from fornma.Statistics.OneWayAnalysis import OneWayAnalysis

# -------------------------------------------------------------------
# Fixtures de dados
# -------------------------------------------------------------------
@pytest.fixture
def df_anova_sig():
    """3 grupos ~ normais, médias diferentes -> ANOVA p<alpha e Tukey após."""
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "y": np.r_[rng.normal(10, 1.5, 40),
                   rng.normal(12.5, 1.5, 40),
                   rng.normal(15, 1.5, 40)],
        "g": (["A"] * 40) + (["B"] * 40) + (["C"] * 40)
    })

@pytest.fixture
def df_anova_ns():
    """3 grupos ~ normais, mesma média -> ANOVA p>=alpha, sem post-hoc."""
    rng = np.random.default_rng(1)
    return pd.DataFrame({
        "y": np.r_[rng.normal(10, 1.5, 40),
                   rng.normal(10, 1.5, 40),
                   rng.normal(10, 1.5, 40)],
        "g": (["A"] * 40) + (["B"] * 40) + (["C"] * 40)
    })

@pytest.fixture
def df_kw_sig():
    """Distribuições não-normais/assimétricas para forçar diferença de medianas."""
    rng = np.random.default_rng(2)
    a = rng.gamma(shape=2.0, scale=2.0, size=50)   # mediana menor
    b = rng.gamma(shape=2.0, scale=2.5, size=50)   # mediana maior
    c = rng.gamma(shape=2.0, scale=3.0, size=50)   # mediana ainda maior
    return pd.DataFrame({"y": np.r_[a,b,c], "g": (["A"]*50)+(["B"]*50)+(["C"]*50)})

@pytest.fixture
def df_kw_ns():
    """Não-normal, mas medianas semelhantes -> KW não significativo."""
    rng = np.random.default_rng(3)
    a = rng.gamma(2.0, 2.0, 60)
    b = rng.gamma(2.0, 2.0, 60)
    c = rng.gamma(2.0, 2.0, 60)
    return pd.DataFrame({"y": np.r_[a,b,c], "g": (["A"]*60)+(["B"]*60)+(["C"]*60)})

# -------------------------------------------------------------------
# Helpers: descritivas, normalidade com tabela, homocedasticidade com célula vazia, logging
# -------------------------------------------------------------------
def test_helper_descriptive_and_logging(tmp_path, df_anova_sig):
    log_file = tmp_path / "helper.log"
    h = AnalysisHelper(alpha=0.05, log_file=str(log_file))
    desc = h.descriptive(df_anova_sig, by=["g"], y="y")
    assert {"n","mean","std","median","q25","q75","sem"}.issubset(desc.columns)
    assert log_file.exists() and log_file.stat().st_size > 0

def test_helper_normality_return_table(df_anova_sig):
    h = AnalysisHelper(alpha=0.05)
    ok, table = h.normality_ok(df_anova_sig, factors=["g"], y="y", return_table=True)
    assert isinstance(ok, bool)
    assert {"cell","n","W","p"}.issubset(table.columns)

def test_helper_homoscedasticity_empty_cell():
    # célula vazia -> retorna False
    df = pd.DataFrame({"y":[1,2,3,4], "g":["A","A","B","B"], "h":["X","Y","X","X"]})
    h = AnalysisHelper(alpha=0.05)
    assert h.homoscedasticity_ok(df, factors=["g","h"], y="y") is False

# -------------------------------------------------------------------
# ANOVA: significativo -> Tukey; não-significativo -> sem post-hoc
# -------------------------------------------------------------------

def test_anova_path_significant(monkeypatch, tmp_path):
    rng = np.random.default_rng(42)
    # 3 grupos com médias diferentes (mas vamos forçar assunções de qualquer jeito)
    df = pd.DataFrame({
        "value": np.r_[rng.normal(10, 1.2, 35),
                       rng.normal(12.5, 1.2, 35),
                       rng.normal(15.0, 1.2, 35)],
        "group": (["A"] * 35) + (["B"] * 35) + (["C"] * 35),
    })

    log_file = tmp_path / "anova_sig.log"
    helper = AnalysisHelper(alpha=0.05, log_file=str(log_file))

    ana = OneWayAnalysis(
        df=df,
        numeric_col="value",
        group_col="group",
        alpha=0.05,
        helper=helper,
    )

    # Força rota ANOVA (independente do resultado do Shapiro/Levene no dia)
    monkeypatch.setattr(ana, "normality_ok", lambda: True)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: True)

    out = ana.run()

    # ANOVA: retorna uma tabela (DataFrame do statsmodels)
    assert isinstance(out["main_result"], pd.DataFrame)

    # Tukey pode ou não acontecer dependendo do p da ANOVA; se veio, deve ser DataFrame
    if out["posthoc"] is not None:
        assert isinstance(out["posthoc"], pd.DataFrame)

    # Log precisa existir e não estar vazio
    assert log_file.exists() and log_file.stat().st_size > 0


def test_anova_path_not_significant(monkeypatch, tmp_path, df_anova_ns):
    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path / "anova_ns.log"))
    ana = OneWayAnalysis(df=df_anova_ns, numeric_col="y", group_col="g",
                         alpha=0.05, helper=helper)

    # Força rota ANOVA (assunções verdadeiras)
    monkeypatch.setattr(ana, "normality_ok", lambda: True)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: True)

    # Força ANOVA não-significativa (p alto) e sem post-hoc
    def fake_run_anova():
        tbl = pd.DataFrame(
            {"sum_sq": [1.0], "df": [2.0], "F": [0.5], "PR(>F)": [0.60]},
            index=["C(g)"]
        )
        ana.log("\n>>> One-way ANOVA (fake non-significant)")
        return tbl, None

    monkeypatch.setattr(ana, "run_anova", fake_run_anova)

    res = ana.run()

    # Verificações
    assert isinstance(res["main_result"], pd.DataFrame)
    assert res["posthoc"] is None

    # log foi escrito
    assert (tmp_path / "anova_ns.log").exists()

# -------------------------------------------------------------------
# Kruskal-Wallis forçado: usando monkeypatch para garantir rota KW
# -------------------------------------------------------------------
@pytest.mark.skipif(
    pytest.importorskip("scikit_posthocs", reason="scikit-posthocs não instalado") is None,
    reason="scikit-posthocs ausente"
)

def test_kw_path_significant_with_dunn(tmp_path, df_kw_sig, monkeypatch):
    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path / "kw_sig.log"))
    ana = OneWayAnalysis(df=df_kw_sig, numeric_col="y", group_col="g",
                         alpha=0.05, helper=helper)

    # força rota KW
    monkeypatch.setattr(ana, "normality_ok", lambda: False)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: False)

    # finge um Kruskal significativo (p pequeno) + um Dunn "fake" (DataFrame)
    def fake_run_kruskal(_grouped_vals):
        stat, p = 7.89, 0.001  # p < alpha garante caminho do Dunn
        posthoc = pd.DataFrame({
            "group1": ["A"],
            "group2": ["C"],
            "p_adjusted": [0.003],
            "reject_H0": [True],
        })
        return (stat, p), posthoc

    monkeypatch.setattr(ana, "run_kruskal", fake_run_kruskal)

    res = ana.run()

    main = res["main_result"]
    assert isinstance(main, tuple) and len(main) == 2
    assert res["posthoc"] is not None
    assert isinstance(res["posthoc"], pd.DataFrame)


@pytest.mark.skipif(
    pytest.importorskip("scikit_posthocs", reason="scikit-posthocs não instalado") is None,
    reason="scikit-posthocs ausente"
)
def test_kw_path_not_significant_no_posthoc(tmp_path, df_kw_ns, monkeypatch):
    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path/"kw_ns.log"))
    ana = OneWayAnalysis(df=df_kw_ns, numeric_col="y", group_col="g",
                         alpha=0.05, helper=helper)

    monkeypatch.setattr(ana, "normality_ok", lambda: False)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: False)

    res = ana.run()
    main = res["main_result"]
    assert isinstance(main, tuple) and len(main) == 2
    assert res["posthoc"] is None

# -------------------------------------------------------------------
# Tukey & Dunn com pairs_of_interest (filtragem)
# -------------------------------------------------------------------
@pytest.mark.skipif(
    pytest.importorskip("scikit_posthocs", reason="scikit-posthocs não instalado") is None,
    reason="scikit-posthocs ausente"
)
def test_pairs_of_interest_filters_in_tukey_and_dunn(tmp_path, df_anova_sig, df_kw_sig, monkeypatch):
    pairs = {("A","C")}  # só interessa comparar A vs C

    # --- Tukey (via ANOVA) ---
    helper1 = AnalysisHelper(alpha=0.05, log_file=str(tmp_path/"tukey_pairs.log"))
    ana1 = OneWayAnalysis(df=df_anova_sig, numeric_col="y", group_col="g",
                          alpha=0.05, pairs_of_interest=pairs, helper=helper1)
    res1 = ana1.run()
    tukey = res1["posthoc"]
    if tukey is not None:
        # deve conter apenas pares de interesse
        assert all({(r["group1"], r["group2"]) in pairs or (r["group2"], r["group1"]) in pairs}
                   for _, r in tukey.iterrows())

    # --- Dunn (via KW forçado) ---
    helper2 = AnalysisHelper(alpha=0.05, log_file=str(tmp_path/"dunn_pairs.log"))
    ana2 = OneWayAnalysis(df=df_kw_sig, numeric_col="y", group_col="g",
                          alpha=0.05, pairs_of_interest=pairs, helper=helper2)
    # garantir rota KW
    monkeypatch.setattr(ana2, "normality_ok", lambda: False)
    monkeypatch.setattr(ana2, "homoscedasticity_ok", lambda: False)
    res2 = ana2.run()
    dunn = res2["posthoc"]
    if dunn is not None:
        # dataframe “longo” com colunas group1/group2
        assert set(["group1","group2"]).issubset(dunn.columns)
        assert all({(r["group1"], r["group2"]) in pairs or (r["group2"], r["group1"]) in pairs}
                   for _, r in dunn.iterrows())

def test_onewayanalysis_with_real_csv(tmp_path):

    # caminho real do CSV
    csv_path = "tests/data/statistics/dados_fig_2.csv"
    df = pd.read_csv(csv_path)

    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path / "real_csv.log"))

    ana = OneWayAnalysis(
        df=df,
        numeric_col="Area",
        group_col="Condition",
        alpha=0.05,
        helper=helper,
    )

    res = ana.run()

    # Verifica se retornou o dicionário esperado
    assert isinstance(res, dict)
    assert "main_result" in res
    assert "summary" in res
    assert isinstance(res["summary"], pd.DataFrame)

    # Apenas para garantir que rodou e não deu erro
    assert not res["summary"].empty
