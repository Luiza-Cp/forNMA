# tests/test_clustering.py
from pathlib import Path
import os
import pandas as pd
import pytest

# ajuste os imports conforme onde as funções vivem no seu pacote
from fornma.UMAP.umap_tools import perform_clustering, plot_elbow, color_umap


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "nma"

CSV_1 = DATA_DIR / "Control_Results.csv"
CSV_2 = DATA_DIR / "Gemcitabine_Results.csv"
CSV_3 = DATA_DIR / "Paclitaxel_Results.csv"

OUT_BASE = BASE_DIR / "results" / "clustering"
OUT_UMAP = OUT_BASE / "umap"
OUT_ELBOW = OUT_BASE / "elbow"
OUT_COLOR = OUT_BASE / "color"

UMAP_CSV_EXISTENTE = OUT_UMAP / "Results with umap coordinates.csv"


@pytest.fixture(scope="module", autouse=True)
def _ensure_dirs():
    OUT_UMAP.mkdir(parents=True, exist_ok=True)
    OUT_ELBOW.mkdir(parents=True, exist_ok=True)
    OUT_COLOR.mkdir(parents=True, exist_ok=True)


def _any_image(out: Path) -> bool:
    img_exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svg", ".pdf"}
    for root, _, files in os.walk(out):
        for f in files:
            if Path(f).suffix.lower() in img_exts:
                return True
    return False


def test_perform_clustering_with_list():
    assert CSV_1.exists() and CSV_2.exists() and CSV_3.exists(), "Ajuste CSV_1/CSV_2 para arquivos reais."

    df_umap = perform_clustering(
        path=[str(CSV_1), str(CSV_2), str(CSV_3)],
        saving_path=str(OUT_UMAP),
        columns=None,           # ou liste colunas específicas se necessário
        n_neighbors=15,
        min_dist=0.1,
        metric="Euclidean",
        scale=True,
    )

    assert isinstance(df_umap, pd.DataFrame)
    assert len(df_umap) > 0

    # Tolerante aos nomes de colunas de UMAP
    cols = {c.lower() for c in df_umap.columns}
    has_umap = {"umap1", "umap_1"}.intersection(cols) and {"umap2", "umap_2"}.intersection(cols)
    assert has_umap, f"Não encontrei colunas UMAP na saída. Colunas: {list(df_umap.columns)}"

    # Pelo menos um arquivo salvo na pasta (caso sua função salve artefatos/CSV)
    assert any(p.is_file() for p in OUT_UMAP.glob("*")), "Nada foi salvo em OUT_UMAP"


def test_perform_clustering_with_single_path():
    assert CSV_1.exists(), "Ajuste CSV_1 para um arquivo real."

    df_umap = perform_clustering(
        path=str(CSV_1),
        saving_path=str(OUT_UMAP),
        columns=None,
        n_neighbors=10,
        min_dist=0.2,
        metric="Euclidean",
        scale=False,
    )

    assert isinstance(df_umap, pd.DataFrame)
    assert len(df_umap) > 0


def test_plot_elbow_saves_plot(tmp_path_factory):
    if UMAP_CSV_EXISTENTE.exists():
        umap_csv = UMAP_CSV_EXISTENTE
    else:
        assert CSV_1.exists(), "Para criar um umap.csv temporário, preciso de CSV_1."
        df_umap = perform_clustering(
            path=str(CSV_1),
            saving_path=str(OUT_UMAP),
            columns=None,
            n_neighbors=15,
            min_dist=0.1,
        )
        # salva um CSV simples para o elbow consumir
        umap_csv = OUT_UMAP / "umap_tmp_for_elbow.csv"
        df_umap.to_csv(umap_csv, index=False)

    plot_elbow(
        path=str(umap_csv),
        saving_path=str(OUT_ELBOW),
        k_min=1,
        k_max=8,
    )

    assert _any_image(OUT_ELBOW), "plot_elbow não gerou figura nenhuma em OUT_ELBOW"


@pytest.fixture(scope="module")
def umap_csv_for_color():
    """
    Fornece um CSV de UMAP para o color_umap.
    Se UMAP_CSV_EXISTENTE existir, usa-o; senão cria um temporário a partir do CSV_1.
    """
    if UMAP_CSV_EXISTENTE.exists():
        return UMAP_CSV_EXISTENTE
    assert CSV_1.exists(), "Ajuste os caminhos dos CSVs."
    df_umap = perform_clustering(
        path=str(CSV_1),
        saving_path=str(OUT_UMAP),
        columns=None,
        n_neighbors=15,
        min_dist=0.1,
    )
    tmp_csv = OUT_UMAP / "umap_tmp_for_color.csv"
    df_umap.to_csv(tmp_csv, index=False)
    return tmp_csv


def test_color_umap_by_column(umap_csv_for_color):
    color_col = "Condition"
    df = pd.read_csv(umap_csv_for_color)
    assert color_col in df.columns, f"Coluna {color_col} não existe em {umap_csv_for_color}. Ajuste o teste."

    color_umap(
        df_umap_path=str(umap_csv_for_color),
        saving_path=str(OUT_COLOR / "by_col"),
        color_col=color_col,
        use_clusters=False,
        n_clusters=None,
    )

    assert _any_image(OUT_COLOR / "by_col"), "color_umap (by column) não salvou nenhuma figura."


def test_color_umap_by_kmeans(umap_csv_for_color):
    # Testa modo de clusters via KMeans
    color_umap(
        df_umap_path=str(umap_csv_for_color),
        saving_path=str(OUT_COLOR / "by_kmeans"),
        color_col=None,
        use_clusters=True,
        n_clusters=4,
    )
    assert _any_image(OUT_COLOR / "by_kmeans"), "color_umap (by kmeans) não salvou nenhuma figura."


def test_color_umap_saving_path_none(umap_csv_for_color):
    """
    saving_path=None → deve salvar ao lado do CSV de entrada (mesma pasta),
    ou de acordo com a convenção da sua função.
    """
    before = {p.name for p in Path(umap_csv_for_color).parent.glob("*")}
    color_umap(
        df_umap_path=str(umap_csv_for_color),
        saving_path=None,
        color_col=None,
        use_clusters=True,
        n_clusters=3,
    )
    after = {p.name for p in Path(umap_csv_for_color).parent.glob("*")}
    new_files = after - before
    # aceita qualquer figura conhecida
    ok = any(Path(n).suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svg", ".pdf"} for n in new_files)
    assert ok, "color_umap com saving_path=None não deixou nenhuma figura nova ao lado do CSV."
