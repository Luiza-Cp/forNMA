# tests/test_two_way_analysis.py
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

from fornma.Statistics.Helpers import AnalysisHelper
from fornma.Statistics.TwoWayAnalysis import TwoWayAnalysis


# =========================
# Fixtures de dados sintéticos
# =========================
@pytest.fixture
def df_balanced_sig():
    """2x2 com médias bem diferentes por célula (fácil dar significância)."""
    rng = np.random.default_rng(0)
    A = np.repeat(["A1", "A2"], 60)
    B = np.tile(np.repeat(["B1", "B2"], 30), 2)
    # diferenças por célula
    mu = {("A1","B1"): 10, ("A1","B2"): 12, ("A2","B1"): 14, ("A2","B2"): 17}
    y = np.array([rng.normal(mu[(a,b)], 1.2) for a,b in zip(A,B)])
    return pd.DataFrame({"y": y, "A": A, "B": B})


@pytest.fixture
def df_balanced_ns():
    """2x2 com mesmas médias em todas as células (deve tender a não significar)."""
    rng = np.random.default_rng(1)
    A = np.repeat(["A1", "A2"], 60)
    B = np.tile(np.repeat(["B1", "B2"], 30), 2)
    y = rng.normal(10, 1.2, len(A))
    return pd.DataFrame({"y": y, "A": A, "B": B})


# =========================
# ANOVA 2 vias - fluxo
# =========================

def test_tw_anova_significant_triggers_tukey(monkeypatch, tmp_path, df_balanced_sig):
    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path / "tw_anova_sig.log"))
    ana = TwoWayAnalysis(df_balanced_sig, numeric_col="y", group_col1="A", group_col2="B",
                         alpha=0.05, helper=helper)

    # força premissas ok
    monkeypatch.setattr(ana, "normality_ok", lambda: True)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: True)

    # simula ANOVA "significativa" + um Tukey qualquer
    def fake_run_two_way_anova():
        tbl = pd.DataFrame({"sum_sq":[10, 5, 3],
                             "df":[1,1,1],
                             "F":[20.0, 10.0, 6.0],
                             "PR(>F)":[0.001, 0.020, 0.040]},
                            index=["C(A)","C(B)","C(A):C(B)"])
        tuk = pd.DataFrame({"group1":["A1 | B1"], "group2":["A2 | B2"],
                             "p_tukey":[0.004], "reject_H0":[True]})
        # TwoWayAnalysis.run espera (anova_table, posthoc)
        return tbl, tuk

    monkeypatch.setattr(ana, "run_two_way_anova", fake_run_two_way_anova)

    res = ana.run()
    assert isinstance(res["main_result"], pd.DataFrame)
    assert isinstance(res["posthoc"], pd.DataFrame) and not res["posthoc"].empty
    assert (tmp_path / "tw_anova_sig.log").exists()


def test_tw_anova_not_significant_no_posthoc(monkeypatch, tmp_path, df_balanced_ns):
    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path / "tw_anova_ns.log"))
    ana = TwoWayAnalysis(df_balanced_ns, numeric_col="y", group_col1="A", group_col2="B",
                         alpha=0.05, helper=helper)

    monkeypatch.setattr(ana, "normality_ok", lambda: True)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: True)

    # ANOVA não-significativa (todos p>alpha), sem Tukey
    def fake_run_two_way_anova():
        tbl = pd.DataFrame({"sum_sq":[1, 1, 1],
                             "df":[1,1,1],
                             "F":[0.5, 0.5, 0.5],
                             "PR(>F)":[0.60, 0.70, 0.80]},
                            index=["C(A)","C(B)","C(A):C(B)"])
        return tbl, None

    monkeypatch.setattr(ana, "run_two_way_anova", fake_run_two_way_anova)

    res = ana.run()
    assert isinstance(res["main_result"], pd.DataFrame)
    assert res["posthoc"] is None
    assert (tmp_path / "tw_anova_ns.log").exists()


def test_tw_anova_pairs_of_interest_reaches_tukey(monkeypatch, df_balanced_sig):
    # garante que pairs_of_interest é propagado para tukey()
    pairs = {("A1 | B1", "A2 | B2")}
    ana = TwoWayAnalysis(df_balanced_sig, "y", "A", "B", alpha=0.05,
                         pairs_of_interest=pairs, helper=AnalysisHelper(0.05))

    monkeypatch.setattr(ana, "normality_ok", lambda: True)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: True)

    captured = {}
    def fake_tukey(df, value_col, group_col, alpha, pairs_of_interest):
        captured["pairs"] = pairs_of_interest
        return pd.DataFrame({"group1":["A1 | B1"], "group2":["A2 | B2"],
                             "p_tukey":[0.01], "reject_H0":[True]})

    def fake_run_two_way_anova():
        tbl = pd.DataFrame({"sum_sq":[10,10,10], "df":[1,1,1],
                             "F":[5.0,5.0,5.0], "PR(>F)":[0.01,0.02,0.03]},
                            index=["C(A)","C(B)","C(A):C(B)"])
        # posthoc será calculado pelo helper.tukey (que vamos monkeypatchar)
        return tbl, ana.helper.tukey(df=ana.df, value_col="y", group_col="group",
                                     alpha=ana.alpha, pairs_of_interest=pairs)

    monkeypatch.setattr(ana.helper, "tukey", fake_tukey)
    monkeypatch.setattr(ana, "run_two_way_anova", fake_run_two_way_anova)

    res = ana.run()
    assert captured.get("pairs") == pairs
    assert isinstance(res["posthoc"], pd.DataFrame)


# =========================
# SRH - fluxo (sem testar internals do SRH)
# =========================

def test_tw_srh_significant_triggers_dunn(monkeypatch, tmp_path, df_balanced_ns):
    # força premissas violadas → SRH; e finge SRH significativo
    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path / "tw_srh_sig.log"))
    ana = TwoWayAnalysis(df_balanced_ns, "y", "A", "B", 0.05, helper=helper)

    monkeypatch.setattr(ana, "normality_ok", lambda: False)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: False)

    # Fake SRH: fit() no-op, to_dataframe() devolve DF mínimo, any_significant()->True
    class _FakeSRH:
        def __init__(self, *a, **k): pass
        def fit(self, *a, **k): return self
        def to_dataframe(self):
            return pd.DataFrame({"df":[1,1,1], "H":[1,2,3], "H_adj":[1,2,3], "p-value":[0.04,0.2,0.8]},
                                index=["A","B","A:B"])
        def any_significant(self, alpha): return True
        def summary(self): return "fake srh"

    # injeta FakeSRH no módulo TwoWayAnalysis em uso
    import fornma.Statistics.TwoWayAnalysis as twmod
    monkeypatch.setattr(twmod, "ScheirerRayHare", _FakeSRH)

    # e faça dunn_post_hoc retornar algo
    def fake_dunn():
        return pd.DataFrame({"grupo1":["A1 | B1"], "grupo2":["A2 | B2"],
                             "p_ajustado":[0.01], "significativo":[True]})
    monkeypatch.setattr(ana, "dunn_post_hoc", fake_dunn)

    res = ana.run()
    assert isinstance(res["main_result"], pd.DataFrame)   # SRH table
    assert isinstance(res["posthoc"], pd.DataFrame)       # dunn retornado
    assert (tmp_path / "tw_srh_sig.log").exists()


def test_tw_srh_not_significant_no_posthoc(monkeypatch, df_balanced_ns):
    ana = TwoWayAnalysis(df_balanced_ns, "y", "A", "B", 0.05, helper=AnalysisHelper(0.05))

    monkeypatch.setattr(ana, "normality_ok", lambda: False)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: False)

    class _FakeSRH:
        def __init__(self, *a, **k): pass
        def fit(self, *a, **k): return self
        def to_dataframe(self):
            return pd.DataFrame({"df":[1,1,1], "H":[1,2,3], "H_adj":[1,2,3], "p-value":[0.5,0.6,0.7]},
                                index=["A","B","A:B"])
        def any_significant(self, alpha): return False
        def summary(self): return "fake srh"

    import fornma.Statistics.TwoWayAnalysis as twmod
    monkeypatch.setattr(twmod, "ScheirerRayHare", _FakeSRH)

    res = ana.run()
    assert isinstance(res["main_result"], pd.DataFrame)
    assert res["posthoc"] is None


def test_tw_dunn_pairs_of_interest(monkeypatch, df_balanced_sig):
    pairs = {("A1 | B1", "A2 | B2")}
    ana = TwoWayAnalysis(df_balanced_sig, "y", "A", "B", 0.05,
                         pairs_of_interest=pairs, helper=AnalysisHelper(0.05))

    # força SRH e sua significância
    monkeypatch.setattr(ana, "normality_ok", lambda: False)
    monkeypatch.setattr(ana, "homoscedasticity_ok", lambda: False)

    class _FakeSRH:
        def __init__(self, *a, **k): pass
        def fit(self, *a, **k): return self
        def to_dataframe(self):
            return pd.DataFrame({"df":[1,1,1], "H":[3,4,5], "H_adj":[3,4,5], "p-value":[0.02,0.03,0.9]},
                                index=["A","B","A:B"])
        def any_significant(self, alpha): return True
        def summary(self): return "fake"
    import fornma.Statistics.TwoWayAnalysis as twmod
    monkeypatch.setattr(twmod, "ScheirerRayHare", _FakeSRH)

    captured = {}
    def fake_dunn():
        captured["pairs"] = pairs
        # retorna só os pares de interesse
        return pd.DataFrame({"grupo1":["A1 | B1"], "grupo2":["A2 | B2"],
                             "p_ajustado":[0.01], "significativo":[True]})
    monkeypatch.setattr(ana, "dunn_post_hoc", fake_dunn)

    res = ana.run()
    assert captured.get("pairs") == pairs
    assert isinstance(res["posthoc"], pd.DataFrame) and not res["posthoc"].empty


# =========================
# Dado real do usuário
# =========================

@pytest.mark.skipif(
    not Path("tests/data/statistics/dados_fig_2.csv").exists(),
    reason="CSV real não encontrado em tests/data/statistics/dados_fig_2.csv"
)
def test_tw_with_real_table(tmp_path):
    csv_path = Path("tests/data/statistics/dados_fig_2.csv")
    df = pd.read_csv(csv_path)

    # colunas informadas
    assert {"Condition", "NMA_category", "Area"}.issubset(df.columns)

    helper = AnalysisHelper(alpha=0.05, log_file=str(tmp_path / "tw_real.log"))
    ana = TwoWayAnalysis(
        df=df,
        numeric_col="Area",
        group_col1="Condition",
        group_col2="NMA_category",
        alpha=0.05,
        helper=helper,
    )

    # não forço rota — apenas garanto que roda e retorna estrutura
    res = ana.run()
    assert isinstance(res, dict) and {"main_result", "posthoc", "summary"} <= set(res.keys())
    assert isinstance(res["summary"], pd.DataFrame) and not res["summary"].empty
