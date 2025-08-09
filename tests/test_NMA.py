import pytest
import os
from fornma.NMA.NMA_settings import NMA_control
import pickle
from fornma.NMA.show_NMA_settings import show_nma_settings
from fornma.NMA.plot_NMA import plot_NMA
from fornma.NMA.NMA_settings import NMA_control
import fornma.NMA as nma_module


CONFIG_FILE = os.path.join(os.path.dirname(nma_module.__file__), "control_parameters.pickle")


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data", "nma")

CSV_1 = os.path.join(DATA_DIR, "Control_Results.csv")
CSV_2 = os.path.join(DATA_DIR, "Gemcitabine_Results.csv")
CSV_3 = os.path.join(DATA_DIR, "Paclitaxel_Results.csv")

RESULTS_DIR = os.path.join(BASE_DIR, "results", "nma", "plots")

NMA_DIR = os.path.dirname(nma_module.__file__)

@pytest.fixture(scope="module")
def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    return RESULTS_DIR


@pytest.fixture
def chdir_to_nma(monkeypatch):
    """Troca o CWD para a pasta do módulo NMA durante o teste."""
    monkeypatch.chdir(NMA_DIR)


@pytest.fixture
def ensure_config(chdir_to_nma):
    """
    Gera o control_parameters.pickle na pasta NMA se não existir,
    usando a própria NMA_control (config real).
    """
    if not os.path.exists(CONFIG_FILE):
        NMA_control(path=CSV_1, sd_area=1.5, sd_nii=3.0, headless=True)
    yield


def test_nma_control_creates_config_headless():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

    # Roda a função
    NMA_control(
        path=CSV_1,
        sd_area=1.5,
        sd_nii=3.0,
        headless=True
    )

    assert os.path.exists(CONFIG_FILE), "Arquivo de configuração não foi criado"

    with open(CONFIG_FILE, "rb") as f:
        config = pickle.load(f)


    assert "sd_area" in config and config["sd_area"] == 1.5
    assert "sd_NII" in config and config["sd_NII"] == 3.0
    assert "fig" in config and config["fig"] is None


def test_nma_control_creates_config():

    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

    # Roda a função
    NMA_control(
        path=CSV_1,
        sd_area=1.5,
        sd_nii=3.0,
        headless= False
    )

    assert os.path.exists(CONFIG_FILE), "Arquivo de configuração não foi criado"

    # Carrega o pickle para validar conteúdo
    with open(CONFIG_FILE, "rb") as f:
        config = pickle.load(f)

    assert "fig" in config and config["fig"] is not None


def test_show_nma_settings():
    show_nma_settings()


def test_plot_nma_raises_without_config(chdir_to_nma, ensure_results_dir):
    # garante ausência do config
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

    with pytest.raises(Exception, match="NMA settings were not defined"):
        plot_NMA(
            path_list=[CSV_1],
            saving_path=ensure_results_dir,
            graph_type="dot",
            single=None,
            overtime=False
        )


def test_plot_nma_generates_outputs(ensure_config, chdir_to_nma, ensure_results_dir):
    plot_NMA(
        path_list=[CSV_1, CSV_2, CSV_3],
        saving_path=ensure_results_dir,
        graph_type="dot",
        sample_size= None,
        single=None,
        overtime=False
    )

    # Verifica log criado/atualizado
    log_path = os.path.join(ensure_results_dir, "logs-fornma.txt")
    assert os.path.exists(log_path), "log não foi criado em saving_path"

    # Verifica pasta com tabelas anotadas
    dest = os.path.join(ensure_results_dir, "Tables with NMA annotation")
    assert os.path.isdir(dest), "pasta 'Tables with NMA annotation' não foi criada"

    # Deve ter pelo menos um CSV anotado
    out_csvs = [f for f in os.listdir(dest) if f.lower().endswith(".csv")]
    assert out_csvs, "nenhum CSV anotado foi salvo em 'Tables with NMA annotation'"


@pytest.mark.parametrize("graph_type", ["dot", "heatmap", "jointplot"])
def test_plot_nma_graph_types(ensure_config, chdir_to_nma, ensure_results_dir, graph_type):
    plot_NMA(
        path_list=[CSV_1, CSV_2, CSV_3],
        saving_path=ensure_results_dir,
        graph_type=graph_type,
        sample_size= None,
        single=None,
        overtime=False
    )

    # Verifica log criado
    log_path = os.path.join(ensure_results_dir, "logs-fornma.txt")
    assert os.path.exists(log_path), f"log não foi criado para graph_type={graph_type}"

    # Verifica pasta de tabelas anotadas
    dest = os.path.join(ensure_results_dir, "Tables with NMA annotation")
    assert os.path.isdir(dest), f"pasta 'Tables with NMA annotation' não foi criada para graph_type={graph_type}"

    # Deve ter pelo menos um CSV anotado
    out_csvs = [f for f in os.listdir(dest) if f.lower().endswith(".csv")]
    assert out_csvs, f"nenhum CSV anotado foi salvo para graph_type={graph_type}"