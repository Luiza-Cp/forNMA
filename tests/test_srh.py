import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from fornma.Statistics.Scheirer_ray_hare import ScheirerRayHare

@pytest.fixture
def df_sokal():
    # Sokal & Rohlf (1995) – balanced 2x2 with n=3 per cell
    Value = [709, 679, 699, 657, 594, 677, 592, 538, 476, 508, 505, 539]
    Sex   = ["Male"]*3 + ["Female"]*3 + ["Male"]*3 + ["Female"]*3
    Fat   = ["Fresh"]*6 + ["Rancid"]*6
    return pd.DataFrame({"Value": Value, "Sex": Sex, "Fat": Fat})

@pytest.fixture
def df_with_ties():
    # 2x2 with deliberate ties in y
    y = [1,1,2,2, 3,3,3, 4,4,4, 2,2]
    A = ["A"]*6 + ["B"]*6
    B = ["X","X","X","Y","Y","Y"]*2
    return pd.DataFrame({"y": y, "A": A, "B": B})

@pytest.fixture
def df_with_na():
    # same structure as Sokal, but with two NAs in y
    Value = [709, 679, None, 657, 594, 677, 592, 538, 476, None, 505, 539]
    Sex   = ["Male"]*3 + ["Female"]*3 + ["Male"]*3 + ["Female"]*3
    Fat   = ["Fresh"]*6 + ["Rancid"]*6
    return pd.DataFrame({"Value": Value, "Sex": Sex, "Fat": Fat})


# =========================
# Sokal & Rohlf (1995)
# =========================

def test_sokal_type2_matches_reference(df_sokal):
    """
    Esperado do R (rcompanion::scheirerRayHare) para Type II:
      D = 1, MS total = 13 (n=12)
      Df  Sum Sq      H       p.value
      Sex       1   8.333   0.6410   0.42334
      Fat       1 108.000   8.3077   0.00395
      Sex:Fat   1   5.333   0.4103   0.52184
      Residuals 8  21.333
    """
    srh = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False)
    srh.fit(df_sokal, formula="Value ~ Sex * Fat")
    out = srh.to_dataframe()

    # ordem e linhas
    assert list(out.index) == ["Sex", "Fat", "Sex:Fat", "Residuals"]

    # D e denominador (MS total)
    assert pytest.approx(srh.D_, abs=1e-12) == 1.0
    assert pytest.approx(srh.denom_, abs=1e-12) == 13.0

    # Numeros ~ R (tolerâncias pequenas)
    assert pytest.approx(out.loc["Sex","sum_sq"],  rel=1e-3) == 8.333
    assert pytest.approx(out.loc["Sex","H"],       rel=1e-3) == 0.6410
    assert pytest.approx(out.loc["Sex","p-value"], rel=5e-3) == 0.42334

    assert pytest.approx(out.loc["Fat","sum_sq"],  rel=1e-3) == 108.000
    assert pytest.approx(out.loc["Fat","H"],       rel=1e-3) == 8.3077
    assert pytest.approx(out.loc["Fat","p-value"], rel=5e-3) == 0.00395

    assert pytest.approx(out.loc["Sex:Fat","sum_sq"],  rel=1e-3) == 5.333
    assert pytest.approx(out.loc["Sex:Fat","H"],       rel=1e-3) == 0.4103
    assert pytest.approx(out.loc["Sex:Fat","p-value"], rel=5e-3) == 0.52184

    # resíduos presentes
    assert pytest.approx(out.loc["Residuals","sum_sq"], rel=1e-3) == 21.333
    assert pytest.approx(out.loc["Residuals","df"],     rel=1e-12) == 8
    # H/p vazios (NaN)
    assert np.isnan(out.loc["Residuals","H"])
    assert np.isnan(out.loc["Residuals","p-value"])


def test_sokal_type3_close_to_type2_in_balanced(df_sokal):
    """Em desenho balanceado, Type II e III devem coincidir nos SS/H."""
    srh2 = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False).fit(
        df_sokal, formula="Value ~ Sex * Fat"
    )
    out2 = srh2.to_dataframe().loc[["Sex","Fat","Sex:Fat"], ["sum_sq","H"]]

    srh3 = ScheirerRayHare(type=3, tie_correct=True, ss=True, verbose=False).fit(
        df_sokal, formula="Value ~ Sex * Fat"
    )
    out3 = srh3.to_dataframe().loc[["Sex","Fat","Sex:Fat"], ["sum_sq","H"]]

    # comparação aproximada
    pd.testing.assert_frame_equal(out2.round(6), out3.round(6))

# =========================
# Empates, NAs e validações
# =========================

def test_ties_change_D_and_pvalues(df_with_ties):
    """Com empates, D < 1 quando tie_correct=True; p-values devem mudar."""
    # com correção
    srh_t = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False)
    srh_t.fit(df_with_ties, formula="y ~ A * B")
    out_t = srh_t.to_dataframe()
    assert srh_t.D_ < 1.0  # há empates

    # sem correção
    srh_f = ScheirerRayHare(type=2, tie_correct=False, ss=True, verbose=False)
    srh_f.fit(df_with_ties, formula="y ~ A * B")
    out_f = srh_f.to_dataframe()

    # p-values devem diferir pelo menos para algum efeito
    assert not np.allclose(
        out_t.loc[["A","B","A:B"], "p-value"].values,
        out_f.loc[["A","B","A:B"], "p-value"].values
    )


def test_na_rows_are_dropped_and_residuals_present(df_with_na):
    srh = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False)
    srh.fit(df_with_na, formula="Value ~ Sex * Fat")
    out = srh.to_dataframe()
    # teve NA dropado: n deve ser 10
    assert srh.n_ == 10
    # residuals
    assert "Residuals" in out.index
    assert "sum_sq" in out.columns


def test_order_and_columns(df_sokal):
    srh = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False).fit(
        df_sokal, formula="Value ~ Sex * Fat"
    )
    out = srh.to_dataframe()
    assert list(out.index) == ["Sex", "Fat", "Sex:Fat", "Residuals"]
    for col in ["df", "sum_sq", "H", "H_adj", "p-value"]:
        assert col in out.columns


def test_formula_vs_names_equivalence(df_sokal):
    srh1 = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False).fit(
        df_sokal, formula="Value ~ Sex * Fat"
    )
    out1 = srh1.to_dataframe()

    srh2 = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False).fit(
        df_sokal, y="Value", x1="Sex", x2="Fat"
    )
    out2 = srh2.to_dataframe()

    pd.testing.assert_frame_equal(out1.sort_index(), out2.sort_index())


def test_type1_runs(df_sokal):
    # apenas garantir que roda sem erro (sequencial)
    srh = ScheirerRayHare(type=1, tie_correct=True, ss=True, verbose=False)
    srh.fit(df_sokal, formula="Value ~ Sex * Fat")
    out = srh.to_dataframe()
    assert "Residuals" in out.index


def test_degenerate_factor_raises():
    df = pd.DataFrame({
        "y":  [1,2,3,4,5,6],
        "A":  ["a","a","a","b","b","b"],
        "B":  ["x","x","x","x","x","x"],  # degenerado: só 1 nível
    })
    with pytest.raises(ValueError, match=r"degenerate|one observed level"):
        ScheirerRayHare(type=3, tie_correct=True, ss=True, verbose=False).fit(
            df, formula="y ~ A * B"
        )


def test_empty_cells_warning():
    df = pd.DataFrame({
        "y":  [1,2,3,4,5,6],
        "A":  ["a","a","a","b","b","b"],
        "B":  ["x","x","x","x","x","x"],
    })
    # força nível ausente 'y' em B (sem degenerar A/B)
    df["A"] = pd.Categorical(df["A"], categories=["a","b"])
    df["B"] = pd.Categorical(df["B"], categories=["x","y"])

    with pytest.warns(UserWarning, match=r"Empty cells"):
        ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False).fit(
            df, formula="y ~ A * B"
        )


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "statistics"
CSV_FILE = DATA_DIR / "dados_fig_2.csv"   # é um arquivo, renomeei para refletir

RESULTS_DIR = BASE_DIR / "results" / "Statistics"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def test_srh_with_datafile_and_save():
    assert CSV_FILE.exists(), f"Arquivo não encontrado: {CSV_FILE}"

    df = pd.read_csv(CSV_FILE)
    srh = ScheirerRayHare(type=2, tie_correct=True, ss=True, verbose=False)
    srh.fit(df, y="Area", x1="NMA_category", x2="Condition")
    out = srh.to_dataframe()

    output_file = RESULTS_DIR / "srh_result.csv"
    out.to_csv(output_file, index=True)

    assert "Residuals" in out.index
    assert output_file.exists()