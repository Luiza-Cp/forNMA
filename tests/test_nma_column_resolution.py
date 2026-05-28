import pandas as pd

from fornma.gui.utils.nma_helpers import find_nma_measure_columns, _resolve_two_columns


def test_nma_measure_candidates_ignore_derived_area_columns():
    columns = [
        "Nuc_Area",
        "Cytoplasm_Area",
        "Total_foci_area_GFP",
        "Foci_area_fraction_GFP",
        "Mean_ring_GFP",
    ]

    assert find_nma_measure_columns(columns, "Area") == ["Nuc_Area", "Cytoplasm_Area"]


def test_resolve_two_columns_uses_unique_compartment_when_only_one_exists():
    df = pd.DataFrame({"Nuc_Area": [1, 2], "Nuc_NII": [0.1, 0.2]})

    area_col, nii_col = _resolve_two_columns(df, "Area", "NII")

    assert area_col == "Nuc_Area"
    assert nii_col == "Nuc_NII"


def test_resolve_two_columns_refuses_ambiguous_compartment_columns():
    df = pd.DataFrame({
        "Nuc_Area": [1, 2],
        "Cytoplasm_Area": [3, 4],
        "Nuc_NII": [0.1, 0.2],
        "Cytoplasm_NII": [0.3, 0.4],
    })

    area_col, nii_col = _resolve_two_columns(df, "Area", "NII")

    assert area_col is None
    assert nii_col is None


def test_resolve_two_columns_honors_explicit_compartment_selection():
    df = pd.DataFrame({
        "Nuc_Area": [1, 2],
        "Cytoplasm_Area": [3, 4],
        "Nuc_NII": [0.1, 0.2],
        "Cytoplasm_NII": [0.3, 0.4],
    })

    area_col, nii_col = _resolve_two_columns(df, "Cytoplasm_Area", "Cytoplasm_NII")

    assert area_col == "Cytoplasm_Area"
    assert nii_col == "Cytoplasm_NII"
