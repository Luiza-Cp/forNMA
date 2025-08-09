import pytest
import os
from fornma.Filters.filters import filters  # ajuste conforme sua estrutura

# Arquivos/pastas de entrada
TABLE_FILE = "tests/data/filters/Results.csv"  # precisa de uma tabela de teste
PICKLE_FOLDER = "tests/data/filters/pkl-data"   # precisa existir se for testar draw=True
RESULTS_BASE = "tests/results/filters"

@pytest.fixture(scope="module")
def setup_results_dir():
    os.makedirs(RESULTS_BASE, exist_ok=True)
    return RESULTS_BASE


def test_filters_without_draw(setup_results_dir):
    # Executa sem desenhar imagens
    filters(
        path_to_table=TABLE_FILE,
        path_to_save=setup_results_dir,
        draw=False,
        column_x="Area",
        column_y="NII"
    )

    # Verifica se o log foi criado
    log_path = os.path.join(setup_results_dir, "logs-fornma.txt")
    assert os.path.exists(log_path), "Log não foi criado em draw=False"

    # Verifica se contém as colunas esperadas no log
    with open(log_path, "r") as f:
        content = f.read()
    assert "Area" in content and "NII" in content, "Log não contém informações de filtro"


def test_filters_with_draw(setup_results_dir):
    filters(
        path_to_table=TABLE_FILE,
        path_to_save=setup_results_dir,
        draw=True,
        column_x="Area",
        column_y="NII",
        path_to_piclke_folder=PICKLE_FOLDER
    )

    # Verifica se o log foi atualizado
    log_path = os.path.join(setup_results_dir, "logs-fornma.txt")
    assert os.path.exists(log_path), "Log não foi criado em draw=True"

    # (Opcional) verifica se alguma imagem foi salva
    files = os.listdir(setup_results_dir)
    has_image = any(
        f.endswith((".png", ".jpg", ".tif"))
        for root, _, files in os.walk(RESULTS_BASE)
        for f in files
    )
    assert has_image, "Nenhuma imagem gerada em draw=True"
