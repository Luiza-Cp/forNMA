# tests/test_plot_router.py
from pathlib import Path
import os
import pytest
import pandas as pd
from fornma.Graphs.plot import plot


BASE_DIR = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data" / "plots"

# no topo do arquivo de testes
STATIC_CSV1 = DATA_DIR / "Control_Results.csv"
STATIC_CSV2 = DATA_DIR / "Gemcitabine_Results.csv"
STATIC_CSV3 = DATA_DIR / "Paclitaxel_Results.csv"

MULTI_CSVS = [STATIC_CSV1, STATIC_CSV2, STATIC_CSV3]

TEMPORAL_CSV1 = DATA_DIR / "Overtime_Control_Results.csv"
TEMPORAL_CSV2 = DATA_DIR / "Overtime_TMZ_Results.csv"
TEMPORAL_MULTI = [TEMPORAL_CSV1, TEMPORAL_CSV2]


OUT_DIR = BASE_DIR / "results" / "plot"
IMG_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svg", ".pdf"}


@pytest.fixture(scope="module", autouse=True)
def _ensure_out():
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def _any_output_created(out_dir: Path) -> bool:
    for root, _, files in os.walk(out_dir):
        for f in files:
            if Path(f).suffix.lower() in IMG_EXTS:
                return True
    # fallback: aceita exportações em txt/csv com “plot” no nome
    for root, _, files in os.walk(out_dir):
        for f in files:
            if "plot" in f.lower() and Path(f).suffix.lower() in {".csv", ".txt"}:
                return True
    return False


def as_single_and_multi(single: Path, multi_paths: list[Path]):
    """
    Retorna dois cenários:
      1) uma única tabela (string do primeiro CSV)
      2) várias tabelas (lista de strings dos 3 CSVs reais)
    """
    return [str(single), [str(p) for p in multi_paths]]


@pytest.mark.parametrize("path_input", as_single_and_multi(STATIC_CSV1, MULTI_CSVS))
def test_plot_returns_and_logs(path_input):
    # garante que todos os CSVs usados nos cenários existem
    for p in MULTI_CSVS:
        assert p.exists(), f"CSV estático não encontrado: {p}"

    # subpasta específica para single vs multi
    variant = "multi" if isinstance(path_input, (list, tuple)) else "single"
    out = OUT_DIR / f"static_{variant}"
    out.mkdir(parents=True, exist_ok=True)

    ret = plot(
        path=path_input,
        path_save=str(out),
        conditions=None,
        frames=None,
        graph_type="dot",
        gate=False,
        y="NII",
        hue="Condition",
    )

    assert str(out) in ret
    log_path = out / "logs-fornma.txt"
    assert log_path.exists(), "log não foi criado"
    assert log_path.stat().st_size > 0, "log está vazio"
    assert _any_output_created(out), "nenhum arquivo de gráfico foi salvo"


@pytest.mark.parametrize("path_input", as_single_and_multi(STATIC_CSV1, MULTI_CSVS))
@pytest.mark.parametrize(
    "graph_type, kwargs",
    [
        ("violin", {"y": "NII", "hue": "Condition"}),
        ("violin", {"y": "NII", "hue": "Condition", "dot": True}),  # violin-dot
        ("box",    {"y": "NII", "hue": "Condition"}),
        ("box",    {"y": "NII", "hue": "Condition", "dot": True}),  # box-dot
        ("dot",    {"y": "NII", "hue": "Condition"}),
        ("bar",    {"y": "NII", "hue": "Condition"}),
        ("scatter",{"x": "Area", "y": "NII", "hue": "Condition", "size": "Perimeter"}),
    ],
)
def test_plot_non_temporal_types(path_input, graph_type, kwargs):
    # garante que todos os CSVs usados existem
    for p in MULTI_CSVS:
        assert p.exists(), f"CSV estático não encontrado: {p}"

    variant = "multi" if isinstance(path_input, (list, tuple)) else "single"
    out = OUT_DIR / f"non_temporal_{graph_type}_{variant}"
    out.mkdir(parents=True, exist_ok=True)

    plot(
        path=path_input,
        path_save=str(out),
        conditions=None,
        frames=None,
        graph_type=graph_type,
        gate=False,
        **kwargs
    )
    assert _any_output_created(out), f"nenhum output salvo para {graph_type} ({variant})"


@pytest.mark.parametrize("path_input", as_single_and_multi(STATIC_CSV1, MULTI_CSVS))
def test_plot_gate_requires_xy(path_input):
    # garante que todos os CSVs usados existem
    for p in MULTI_CSVS:
        assert p.exists(), f"CSV estático não encontrado: {p}"

    variant = "multi" if isinstance(path_input, (list, tuple)) else "single"
    out = OUT_DIR / f"gate_validation_{variant}"
    out.mkdir(parents=True, exist_ok=True)

    # deve falhar sem x e y quando gate=True
    with pytest.raises(ValueError, match="forneça 'x' e 'y'"):
        plot(
            path=path_input,
            path_save=str(out),
            conditions=None,
            frames=None,
            graph_type="dot",
            gate=True,   # faltam x e y
        )

    # com x,y deve funcionar
    plot(
        path=path_input,
        path_save=str(out),
        conditions=None,
        frames=None,
        graph_type="dot",
        gate=True,
        x="Area",
        y="NII",
        hue="Condition",
    )
    assert _any_output_created(out), f"nenhum output salvo (gate, {variant})"

@pytest.mark.parametrize("graph_type", ["line", "rolling-average", "cpd"])
@pytest.mark.parametrize(
    "path_input",
    as_single_and_multi(STATIC_CSV1, [STATIC_CSV1, STATIC_CSV2, STATIC_CSV3])
)
def test_plot_temporal_requires_overtime(path_input, graph_type):
    # garantimos que os estáticos existem (os temporais não são usados neste teste)
    for p in [STATIC_CSV1, STATIC_CSV2, STATIC_CSV3]:
        assert p.exists(), f"CSV estático não encontrado: {p}"

    variant = "multi" if isinstance(path_input, (list, tuple)) else "single"
    out = OUT_DIR / f"temporal_invalid_{graph_type}_{variant}"
    out.mkdir(parents=True, exist_ok=True)

    # usando arquivos ESTÁTICOS de propósito para falhar (sem Overtime=True)
    with pytest.raises(ValueError):
        plot(
            path=path_input,
            path_save=str(out),
            conditions=None,
            frames=[0, 1],
            graph_type=graph_type,
            gate=False,
            y="NII",
            n=3,            # usado por rolling-average
            control="Ctrl", # usado por cpd
        )


@pytest.mark.parametrize("path_input", as_single_and_multi(TEMPORAL_CSV1, TEMPORAL_MULTI))
@pytest.mark.parametrize(
    "graph_type, kwargs",
    [
        ("line", {"y": "NII", "hue": "Condition"}),
        ("rolling-average", {"y": "NII", "n": 3}),
        ("cpd", {"frames": [0, 1, 2], "control": "Control"}),
    ],
)
def test_plot_temporal_types(path_input, graph_type, kwargs):
    # garante que os temporais existem
    for p in TEMPORAL_MULTI:
        assert p.exists(), f"CSV temporal não encontrado: {p}"

    variant = "multi" if isinstance(path_input, (list, tuple)) else "single"
    out = OUT_DIR / f"temporal_{graph_type}_{variant}"
    out.mkdir(parents=True, exist_ok=True)

    plot(
        path=path_input,
        path_save=str(out),
        conditions=None,
        frames=kwargs.get("frames"),
        graph_type=graph_type,
        gate=False,
        **{k: v for k, v in kwargs.items() if k != "frames"}
    )

    assert _any_output_created(out), f"nenhum output salvo para {graph_type} ({variant})"


def make_missing_condition(src: Path, tmp_path: Path) -> Path:
    """Cria um CSV baseado em src mas sem a coluna Condition."""
    df = pd.read_csv(src)
    df = df.drop(columns=[c for c in df.columns if c.lower() == "condition"])
    p = tmp_path / f"no_condition_{src.name}"
    df.to_csv(p, index=False)
    return p

def make_condition_all_false(src: Path, tmp_path: Path) -> Path:
    """Cria um CSV baseado em src mas com a coluna Condition toda vazia."""
    df = pd.read_csv(src)
    cond_cols = [c for c in df.columns if c.lower() == "condition"]
    if not cond_cols:
        raise ValueError(f"O CSV {src} não tem coluna 'Condition'")
    df[cond_cols[0]] = False  # tudo vazio
    p = tmp_path / f"condition_false_{src.name}"
    df.to_csv(p, index=False)
    return p


def test_multiple_paths_require_condition_missing_raises(tmp_path):
    out = OUT_DIR / "multi_missing_condition"
    out.mkdir(parents=True, exist_ok=True)

    bad_csv = make_missing_condition(STATIC_CSV2, tmp_path)  # remove Condition
    with pytest.raises(ValueError, match="não possui a coluna 'condition'"):
        plot(
            path=[str(STATIC_CSV1), str(bad_csv)],
            path_save=str(out),
            conditions=None,
            frames=None,
            graph_type="dot",
            gate=False,
            y="NII",
            hue="Condition",
        )


def test_multiple_paths_require_condition_all_false_raises(tmp_path):
    out = OUT_DIR / "multi_condition_all_false"
    out.mkdir(parents=True, exist_ok=True)

    bad_csv = make_condition_all_false(STATIC_CSV3, tmp_path)  # deixa Condition vazia

    with pytest.raises(ValueError, match="está vazia ou com valores inválidos"):
        plot(
            path=[str(STATIC_CSV1), str(bad_csv)],
            path_save=str(out),
            conditions=None,
            frames=None,
            graph_type="dot",
            gate=False,
            y="NII",
            hue="Condition",
        )


def test_multiple_paths_ok_when_condition_present():
    out = OUT_DIR / "multi_ok"
    out.mkdir(parents=True, exist_ok=True)

    plot(
        path=[str(STATIC_CSV1), str(STATIC_CSV2), str(STATIC_CSV3)],
        path_save=str(out),
        conditions=None,
        frames=None,
        graph_type="dot",
        gate=False,
        y="NII",
        hue="Condition",
    )
    assert _any_output_created(out), "não salvou saída no caso multi OK"
