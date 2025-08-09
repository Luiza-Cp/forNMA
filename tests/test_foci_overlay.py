import pytest
import os
from fornma.Foci_overlay.foci_overlay import foci_overlay, plot_profile

# Caminho fixo para os resultados em .pkl (dados de entrada para o teste)
PKL_RESULTS_FOLDER = "tests/data/foci/pkl-data"
RESULTS_BASE = "tests/results/foci_overlay"

@pytest.fixture(scope="module")
def setup_results_dir():
    """
    Garante que a pasta de resultados exista antes dos testes.
    """
    os.makedirs(RESULTS_BASE, exist_ok=True)
    return RESULTS_BASE


def test_foci_overlay_with_channels(setup_results_dir):
    # Chama a função com a lista de canais fornecida
    foci_overlay(
        pkl_results_folder_path=PKL_RESULTS_FOLDER,
        path_to_save=setup_results_dir,
        channel_list=['DAPI', 'LC3']
    )

    # Verifica se gerou arquivos de saída
    files = os.listdir(setup_results_dir)
    assert len(files) > 0, "Nenhum arquivo foi gerado com os canais ['DAPI', 'LC3']"


def test_foci_overlay_without_channels(setup_results_dir):
    # Chama a função sem passar channel_list (usa o padrão = None)
    foci_overlay(
        pkl_results_folder_path=PKL_RESULTS_FOLDER,
        path_to_save=setup_results_dir
    )

    files = os.listdir(setup_results_dir)
    assert len(files) > 0, "Nenhum arquivo foi gerado sem channel_list"


def test_plot_profile_with_channels(setup_results_dir):
    plot_profile(
        path_pickle_data=PKL_RESULTS_FOLDER,
        path_save=setup_results_dir,
        columns=['DAPI', 'LC3']
    )
    files = os.listdir(setup_results_dir)
    assert files, "Nenhum arquivo gerado em plot_profile com colunas"


def test_plot_profile_without_channels(setup_results_dir):
    plot_profile(
        path_pickle_data=PKL_RESULTS_FOLDER,
        path_save=setup_results_dir
    )
    files = os.listdir(setup_results_dir)
    assert files, "Nenhum arquivo gerado em plot_profile sem colunas"