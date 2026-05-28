import pandas as pd
import numpy as np

from fornma.core.Segmentation.analyze import (
    create_nuclei_cytoplasm_mapping,
    save_nuclei_cytoplasm_mapping,
)


def _box(x1, y1, x2, y2):
    return np.array(
        [
            [[x1, y1]], [[(x1 + x2) // 2, y1]], [[x2, y1]], [[x2, (y1 + y2) // 2]],
            [[x2, y2]], [[(x1 + x2) // 2, y2]], [[x1, y2]], [[x1, (y1 + y2) // 2]],
        ],
        dtype=np.int32,
    )


def test_create_mapping_preserves_multiple_and_unmatched_objects():
    nuclei = [
        _box(2, 2, 4, 4),
        _box(6, 6, 8, 8),
        _box(40, 40, 42, 42),
        _box(22, 22, 24, 24),
    ]
    cytoplasm = [
        _box(0, 0, 10, 10),
        _box(20, 20, 26, 26),
        _box(21, 21, 27, 27),
        _box(60, 60, 70, 70),
    ]

    mapping = create_nuclei_cytoplasm_mapping(
        nuclei,
        cytoplasm,
        frame=3,
        condition="Control",
        is_overtime=False,
        nucleus_image_name="dapi.tif",
        cytoplasm_image_name="bright.tif",
        origin_folder="Control",
    )

    assert len(mapping) == 6
    assert set(mapping["Pair_status"]) == {
        "multinucleated",
        "ambiguous",
        "nucleus_without_cytoplasm",
        "cytoplasm_without_nucleus",
    }
    paired_to_first = mapping[mapping["Cytoplasm_ID"] == 1]
    assert set(paired_to_first["Nucleus_ID"]) == {1, 2}
    assert set(paired_to_first["N_nuclei_in_cytoplasm"]) == {2}
    ambiguous = mapping[mapping["Nucleus_ID"] == 4]
    assert set(ambiguous["Cytoplasm_ID"]) == {2, 3}
    assert set(ambiguous["N_cytoplasms_for_nucleus"]) == {2}


def test_save_mapping_writes_one_relationship_table_per_condition(tmp_path):
    mapping = create_nuclei_cytoplasm_mapping(
        [_box(2, 2, 4, 4)],
        [_box(0, 0, 10, 10)],
        frame=0,
        condition="Control",
        is_overtime=False,
        nucleus_image_name="dapi.tif",
        cytoplasm_image_name="bright.tif",
        origin_folder="Control",
    )

    save_nuclei_cytoplasm_mapping(mapping, str(tmp_path))
    save_nuclei_cytoplasm_mapping(mapping.assign(Frame=1), str(tmp_path))

    output = pd.read_csv(tmp_path / "Control" / "Nuclei Cytoplasm Mapping.csv")
    assert list(output["Frame"]) == [0, 1]
    assert "origin_folder" not in output.columns
    assert output.loc[0, "Pair_status"] == "matched"
