import pytest
import toml
import os
from fornma.Segmentation.check_user_inputs import check_user_inputs
from fornma.Segmentation.run import run

@pytest.fixture
def parameters_no_cellpose():
    dic = toml.load("tests/data/parameters.toml")
    outdir = 'tests/results/segmentation/fornma'
    os.makedirs(outdir, exist_ok=True)
    dic['path_to_save'] = outdir
    check_user_inputs(dic)
    return dic

@pytest.fixture
def parameters_cellpose():
    dic = toml.load("tests/data/parameters_cellpose.toml")
    outdir = 'tests/results/segmentation/cellpose'
    os.makedirs(outdir, exist_ok=True)
    dic['path_to_save'] = outdir
    check_user_inputs(dic)
    return dic

def test_run_no_cellpose(parameters_no_cellpose):
    run(parameters_no_cellpose, preview=False)
    assert any(os.scandir(parameters_no_cellpose['path_to_save']))

def test_run_cellpose(parameters_cellpose):
    run(parameters_cellpose, preview=False)
    assert any(os.scandir(parameters_cellpose['path_to_save']))
