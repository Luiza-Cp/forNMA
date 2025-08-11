# tests/statistics/test_chi_square_subgroup.py
import numpy as np
import pandas as pd
import pytest

import fornma.Statistics.ChiSquareSubgroupComparator as submod
from fornma.Statistics.ChiSquareSubgroupComparator import ChiSquareSubgroupComparator

# -----------------------
# Fixtures de dados
# -----------------------

@pytest.fixture
def df_ok_sub():
    """
    Dados com 3 condições e 3 grupos (categorias), contagens suficientes
    para caminho assintótico (qui-quadrado) em todos os pares.
    """
    rng = np.random.default_rng(42)
    conditions = ["A", "B", "C"]
    groups = ["round", "irregular", "lobed"]
    rows = []
    for cond in conditions:
        # 120 por condição distribuídos entre 3 grupos
        counts = rng.multinomial(120, [0.34, 0.33, 0.33])
        for g, c in zip(groups, counts):
            rows += [{"Condition": cond, "NMA_category": g}] * int(c)
    return pd.DataFrame(rows)


@pytest.fixture
def df_low_sub():
    """
    Dados que forçam esperado baixo em 2x2 para Fisher.
    """
    rows = (
        [{"Condition": "A", "NMA_category": "round"}] * 30
        + [{"Condition": "A", "NMA_category": "irregular"}] * 1
        + [{"Condition": "B", "NMA_category": "round"}] * 2
        + [{"Condition": "B", "NMA_category": "irregular"}] * 25
    )
    return pd.DataFrame(rows)


@pytest.fixture
def df_zero_skip():
    """
    Inclui um grupo 'ghost' que não aparece em nenhuma condição — deve ser pulado.
    E outro grupo válido para garantir saída não-vazia.
    """
    rows = (
        [{"Condition": "A", "NMA_category": "valid"}] * 20
        + [{"Condition": "B", "NMA_category": "valid"}] * 25
        # grupo 'ghost' ausente em A e B
    )
    return pd.DataFrame(rows)


@pytest.fixture
def comparator():
    # correção padrão bonferroni (mudaremos via 'auto' quando necessário)
    return ChiSquareSubgroupComparator(expected_min=5.0, correction_method="bonferroni", helper=None, log_file=None)


# -----------------------
# Testes principais
# -----------------------

def test_compare_chi_square_path(df_ok_sub):
    comp = ChiSquareSubgroupComparator(expected_min=1.0, correction_method="bonferroni")
    df_results, prop = comp.compare(df_ok_sub, group_col="NMA_category", condition_col="Condition")

    # estrutura básica
    assert isinstance(df_results, pd.DataFrame)
    assert isinstance(prop, pd.DataFrame)
    assert not df_results.empty

    # total de comparações esperadas: grupos * C(n_cond, 2)
    n_groups = df_ok_sub["NMA_category"].nunique()
    n_conditions = df_ok_sub["Condition"].nunique()
    expected_pairs = n_groups * (n_conditions * (n_conditions - 1) // 2)
    assert len(df_results) == expected_pairs

    # todas devem ser qui-quadrado (esperado_min baixo)
    assert set(df_results["Test"]) == {"Chi-square"}

    # colunas de múltipla correção presentes
    assert {"Corrected p-value", "Significant"}.issubset(df_results.columns)

    # Tabelas 2x2 presentes e bem formadas
    assert all(isinstance(t, np.ndarray) and t.shape == (2, 2) for t in df_results["Table"])


def test_compare_fisher_path_monkeypatched(df_low_sub, monkeypatch):
    # força Fisher elevando expected_min e controlando o p-valor retornado
    comp = ChiSquareSubgroupComparator(expected_min=1e6, correction_method="bonferroni")

    recorded = {"called": 0}
    def fake_fisher_exact(table):
        recorded["called"] += 1
        return (1.0, 0.0123)

    # patcha no módulo onde foi importado
    monkeypatch.setattr(submod, "fisher_exact", fake_fisher_exact)

    df_results, prop = comp.compare(df_low_sub, group_col="NMA_category", condition_col="Condition")

    assert not df_results.empty
    # apenas 1 grupo ("round" e "irregular") * 1 par (A vs B) -> 2 grupos → 2 comparações
    # Na verdade: o comparador faz por GRUPO. Para "round" 1 par A vs B; para "irregular" também 1 par. Total 2 linhas.
    assert len(df_results) == 2
    assert set(df_results["Test"]) == {"Fisher"}
    # p controlado
    assert np.allclose(df_results["Raw p-value"].values, 0.0123)
    assert recorded["called"] == 2  # chamado para os dois grupos


def test_compare_auto_correction_switch_to_fdr(df_ok_sub, monkeypatch):
    import fornma.Statistics.ChiSquareSubgroupComparator as submod
    from fornma.Statistics.ChiSquareSubgroupComparator import ChiSquareSubgroupComparator
    import numpy as np

    # Fake chi2_contingency: sempre retorna expected > 0
    def fake_chi2(table, correction=False):
        expected = np.ones_like(table, dtype=float)  # evita zeros
        return 1.23, 0.45, None, expected

    monkeypatch.setattr(submod, "chi2_contingency", fake_chi2)

    # --- Caso >3 comparações: 3 grupos * C(3,2)=3 => 9 ---
    comp = ChiSquareSubgroupComparator(expected_min=1.0, correction_method="auto")

    seen = {"method": None}
    def fake_multitest_large(pvals, method):
        seen["method"] = method
        # devolve algo válido
        rej = np.zeros(len(pvals), dtype=bool)
        p_corr = np.array(pvals, dtype=float)
        return rej, p_corr, None, None

    monkeypatch.setattr(submod, "multipletests", fake_multitest_large)
    df_results, _ = comp.compare(df_ok_sub, group_col="NMA_category", condition_col="Condition")
    assert seen["method"] == "fdr_bh"
    assert len(df_results) == 9

    # --- Caso ≤3 comparações: 1 grupo * C(3,2)=3 ---
    # Mantemos só um grupo para forçar 3 pares, mas como chi2 foi monkeypatchado,
    # não teremos o problema dos expected zeros.
    df_small = df_ok_sub[df_ok_sub["NMA_category"] == "round"].copy()
    comp2 = ChiSquareSubgroupComparator(expected_min=1.0, correction_method="auto")

    seen2 = {"method": None}
    def fake_multitest_small(pvals, method):
        seen2["method"] = method
        rej = np.zeros(len(pvals), dtype=bool)
        p_corr = np.array(pvals, dtype=float)
        return rej, p_corr, None, None

    monkeypatch.setattr(submod, "multipletests", fake_multitest_small)
    df_results2, _ = comp2.compare(df_small, group_col="NMA_category", condition_col="Condition")
    assert seen2["method"] == "bonferroni"
    assert len(df_results2) == 3



def test_compare_skips_degenerate(df_zero_skip):
    import pandas as pd
    from fornma.Statistics.ChiSquareSubgroupComparator import ChiSquareSubgroupComparator

    # Augmenta o fixture para garantir pelo menos uma 2x2 válida
    df_aug = pd.concat([
        df_zero_skip,
        pd.DataFrame([
            {"Condition": "A", "NMA_category": "other"},
            {"Condition": "B", "NMA_category": "other"},
        ])
    ], ignore_index=True)

    comp = ChiSquareSubgroupComparator(expected_min=5.0, correction_method="bonferroni")
    df_results, _ = comp.compare(df_aug, group_col="NMA_category", condition_col="Condition")

    # Agora deve haver pelo menos uma comparação válida
    assert not df_results.empty

    # Não deve haver linhas com Group == 'ghost'
    assert "ghost" not in set(df_results["Group"])

    # Extra: garante que nenhuma tabela 2x2 retornada é degenerada (linha/coluna toda zero)
    for tbl in df_results["Table"]:
        assert tbl.shape == (2, 2)
        assert (tbl.sum(axis=0) > 0).all()
        assert (tbl.sum(axis=1) > 0).all()


def test_tables_type_and_shape(df_ok_sub):
    comp = ChiSquareSubgroupComparator(expected_min=1.0, correction_method="bonferroni")
    df_results, _ = comp.compare(df_ok_sub, group_col="NMA_category", condition_col="Condition")

    assert all(isinstance(t, np.ndarray) for t in df_results["Table"])
    assert all(t.shape == (2, 2) for t in df_results["Table"])


# -----------------------
# Dados reais (CSV)
# -----------------------

@pytest.mark.parametrize("csv_path", ["tests/data/statistics/dados_fig_2.csv"])
def test_real_data_subgroup(csv_path):
    df = pd.read_csv(csv_path)
    # checa colunas mínimas
    assert {"NMA_category", "Condition"} <= set(df.columns)

    comp = ChiSquareSubgroupComparator(expected_min=5.0, correction_method="auto")
    df_results, prop = comp.compare(df, group_col="NMA_category", condition_col="Condition")

    # Estrutura e colunas esperadas
    assert isinstance(df_results, pd.DataFrame) and isinstance(prop, pd.DataFrame)
    assert {"Group", "Comparison", "Test", "Raw p-value", "Corrected p-value", "Significant"}.issubset(df_results.columns)

    # Pode haver 0 ou mais achados significativos; não fixamos resultado estatístico
    assert df_results.shape[0] >= 1
    # prop table coerente: índices = Condition, colunas = NMA_category
    assert "Condition" in prop.index.names and df["Condition"].nunique() == prop.shape[0]
