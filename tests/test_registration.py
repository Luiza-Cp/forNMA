import pytest
import os
from fornma.Registration.registration import registration

# Lista explícita de pastas para registrar
FOLDERS_TO_REGISTER = [
    "tests/data/Red/Control red",
    "tests/data/Green/Control green",
    # adicione mais conforme for criando
]

RESULTS_BASE = "tests/results/registration"


@pytest.fixture(scope="module")
def setup_results_dir():
    """
    Garante que as pastas de resultados existam antes dos testes.
    """
    crop_dir = os.path.join(RESULTS_BASE, "crop")
    no_crop_dir = os.path.join(RESULTS_BASE, "no_crop")
    os.makedirs(crop_dir, exist_ok=True)
    os.makedirs(no_crop_dir, exist_ok=True)
    return {"crop": crop_dir, "no_crop": no_crop_dir}


def test_registration_with_crop(setup_results_dir):
    output_dir = setup_results_dir["crop"]
    registration(FOLDERS_TO_REGISTER, path_to_save=output_dir, crop=True)

    files = os.listdir(output_dir)
    assert len(files) > 0, "Nenhum arquivo foi gerado com crop=True"


def test_registration_without_crop(setup_results_dir):
    output_dir = setup_results_dir["no_crop"]
    registration(FOLDERS_TO_REGISTER, path_to_save=output_dir, crop=False)

    files = os.listdir(output_dir)
    assert len(files) > 0, "Nenhum arquivo foi gerado com crop=False"
