import numpy as np
import pytest

from fornma.core.Segmentation.check_user_inputs import check_user_inputs
from fornma.core.Segmentation.analyze import _drawable_contours
from fornma.core.Segmentation.measure.Cell import Cell
from fornma.core.Segmentation.segmentation import cellpose_integration


def _valid_parameters(tmp_path):
    channel = tmp_path / "channel"
    condition = channel / "condition"
    output = tmp_path / "output"
    condition.mkdir(parents=True)
    output.mkdir()

    return {
        "channel_path_list": [str(channel)],
        "names": ["DAPI"],
        "subfolder_names": ["condition"],
        "channel_with_nuclei": str(channel),
        "overtime": False,
        "path_to_save": str(output),
        "save_images": True,
        "segmentation": {
            "magnification": 20,
            "pixel_size": 0.5,
            "rescale_intensity": False,
            "remove_background": False,
            "rolling_ball_radius": 40,
            "shape": 0.88,
            "eccentricity": False,
            "minimum_size": False,
            "maximum_size": False,
            "minimum_radius": False,
            "maximum_radius": False,
            "forNMA": {
                "use_fornma": False,
                "threshold": "triangle",
                "offset": 5,
                "smooth": 13,
                "adjust_size": -1,
                "cut_edges": 0.9,
                "find_low_intensity_nucleus": False,
                "weakly_labeled": False,
            },
            "cellpose": {
                "use_cellpose": True,
                "model_type": "cyto3",
                "diameter": 25,
                "flow_threshold": 0.4,
                "mask_threshold": 0.0,
                "use_gpu": False,
                "invert": True,
                "cellprob_threshold": -3,
            },
        },
        "channel_parameters": {
            "channel1": {
                "rescale_intensity": True,
                "remove_background": True,
                "rolling_ball_radius": 40,
                "match_histograms": False,
                "measure_translocation": False,
                "ring_size": False,
                "use_ellipse": False,
                "measure_foci": True,
                "foci_min_size": 7,
                "foci_max_size": False,
                "foci_min_int": False,
                "foci_max_int": False,
                "foci_prominence": 1.2,
            }
        },
    }


def test_check_user_inputs_accepts_cyto_models(tmp_path):
    params = _valid_parameters(tmp_path)

    for model_type in ("nuclei", "cyto3", "cyto2", "cyto"):
        params["segmentation"]["cellpose"]["model_type"] = model_type
        check_user_inputs(params)


def test_check_user_inputs_rejects_unknown_cellpose_model(tmp_path):
    params = _valid_parameters(tmp_path)
    params["segmentation"]["cellpose"]["model_type"] = "not-a-model"

    with pytest.raises(Exception, match="Cellpose model"):
        check_user_inputs(params)


def test_run_cellpose_passes_selected_model_to_cellpose(monkeypatch):
    created = {}
    eval_kwargs = {}
    outline_inputs = []
    cellpose_integration.clear_cellpose_model_cache()

    class FakeCellposeModel:
        def __init__(self, pretrained_model, gpu):
            created["pretrained_model"] = pretrained_model
            created["gpu"] = gpu

        def eval(self, *args, **kwargs):
            eval_kwargs.update(kwargs)
            return np.zeros((1, 5, 5), dtype=np.uint8), None, None

    monkeypatch.setattr(cellpose_integration.models, "CellposeModel", FakeCellposeModel)
    monkeypatch.setattr(cellpose_integration, "load_image", lambda path, **kwargs: np.zeros((5, 5), dtype=np.uint8))

    def fake_outlines_list(mask):
        outline_inputs.append(mask.shape)
        return []

    monkeypatch.setattr(cellpose_integration.utils, "outlines_list", fake_outlines_list)

    contours = cellpose_integration.run_cellpose(
        image_path="image.tif",
        use_gpu=True,
        diameter=50,
        mag=20,
        px_s=0.5,
        shape=None,
        eccentricity=None,
        min_size=None,
        max_size=None,
        min_radius=None,
        max_radius=None,
        model_type="cyto2",
        resample=True,
        flow_threshold=0.55,
        cellprob_threshold=-2,
    )

    assert contours == []
    assert created == {"pretrained_model": "cyto2", "gpu": True}
    assert eval_kwargs["diameter"] == 50
    assert eval_kwargs["flow_threshold"] == 0.55
    assert eval_kwargs["cellprob_threshold"] == -2
    assert eval_kwargs["resample"] is True
    assert outline_inputs == [(5, 5)]
    cellpose_integration.clear_cellpose_model_cache()


def test_get_cellpose_model_reuses_cached_model(monkeypatch):
    created = []
    cellpose_integration.clear_cellpose_model_cache()

    class FakeCellposeModel:
        def __init__(self, pretrained_model, gpu):
            created.append((pretrained_model, gpu))

    monkeypatch.setattr(cellpose_integration.models, "CellposeModel", FakeCellposeModel)

    first = cellpose_integration.get_cellpose_model("nuclei", False)
    second = cellpose_integration.get_cellpose_model("nuclei", False)
    third = cellpose_integration.get_cellpose_model("cyto3", False)

    assert first is second
    assert third is not first
    assert created == [("nuclei", False), ("cyto3", False)]
    cellpose_integration.clear_cellpose_model_cache()


def test_run_cellpose_ignores_empty_outlines(monkeypatch):
    cellpose_integration.clear_cellpose_model_cache()

    class FakeCellposeModel:
        def __init__(self, pretrained_model, gpu):
            pass

        def eval(self, *args, **kwargs):
            masks = np.zeros((5, 5), dtype=np.uint8)
            masks[2:4, 2:4] = 1
            return masks, None, None

    monkeypatch.setattr(cellpose_integration.models, "CellposeModel", FakeCellposeModel)
    monkeypatch.setattr(cellpose_integration, "load_image", lambda path, **kwargs: np.zeros((5, 5), dtype=np.uint8))
    monkeypatch.setattr(
        cellpose_integration.utils,
        "outlines_list",
        lambda masks: [
            np.array([], dtype=float).reshape(0, 2),
            np.array([[1, 1], [1, 2]], dtype=np.int64),
            np.array([[1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1]], dtype=np.int64),
        ],
    )

    contours = cellpose_integration.run_cellpose(
        image_path="image.tif",
        use_gpu=False,
        diameter=25,
        mag=20,
        px_s=0.5,
        shape=None,
        eccentricity=None,
        min_size=None,
        max_size=None,
        min_radius=None,
        max_radius=None,
    )

    assert contours == []
    cellpose_integration.clear_cellpose_model_cache()


def test_run_cellpose_applies_selected_contour_filters_without_automatic_size_bounds(monkeypatch):
    class FakeCellposeModel:
        def __init__(self, pretrained_model, gpu):
            pass

        def eval(self, *args, **kwargs):
            masks = np.zeros((20, 20), dtype=np.uint8)
            masks[5:8, 5:8] = 1
            return masks, None, None

    tiny_contour = np.array([[5, 5], [6, 5], [7, 6], [7, 7], [6, 8], [5, 7]], dtype=np.int64)

    monkeypatch.setattr(cellpose_integration.models, "CellposeModel", FakeCellposeModel)
    monkeypatch.setattr(cellpose_integration, "load_image", lambda path, **kwargs: np.zeros((20, 20), dtype=np.uint8))
    monkeypatch.setattr(cellpose_integration.utils, "outlines_list", lambda masks: [tiny_contour])

    contours = cellpose_integration.run_cellpose(
        image_path="image.tif",
        use_gpu=False,
        diameter=25,
        mag=20,
        px_s=0.5,
        shape=None,
        eccentricity=None,
        min_size=None,
        max_size=None,
        min_radius=None,
        max_radius=None,
    )

    assert len(contours) == 1
    np.testing.assert_array_equal(contours[0], tiny_contour.astype(np.int32))

    contours = cellpose_integration.run_cellpose(
        image_path="image.tif",
        use_gpu=False,
        diameter=25,
        mag=20,
        px_s=0.5,
        shape=None,
        eccentricity=None,
        min_size=1000,
        max_size=None,
        min_radius=None,
        max_radius=None,
    )

    assert contours == []
    cellpose_integration.clear_cellpose_model_cache()


def test_cell_measurement_handles_constant_intensity_images():
    contour = np.array([[[2, 2]], [[4, 2]], [[5, 3]], [[4, 5]], [[2, 5]], [[1, 3]]], dtype=np.int32)
    image = np.full((10, 10), 12, dtype=np.uint8)

    cell = Cell(
        1,
        contour,
        20,
        0.6,
        image,
        "constant.tif",
        "Channel",
        False,
        3,
        False,
        7,
        False,
        False,
        False,
        1.2,
        False,
    )

    assert cell.mean_int == 0


def test_drawable_contours_accepts_cellpose_and_fornma_formats():
    cellpose_cnt = np.array([[1, 1], [5, 1], [5, 5], [1, 5]], dtype=np.int64)
    fornma_cnt = np.array([[[1, 1]], [[5, 1]], [[5, 5]], [[1, 5]]], dtype=np.int64)
    empty_cnt = np.array([], dtype=float).reshape(0, 2)

    contours = _drawable_contours([cellpose_cnt, [fornma_cnt], empty_cnt, None])

    assert [cnt.shape for cnt in contours] == [(4, 2), (4, 1, 2)]
    assert all(cnt.dtype == np.int32 for cnt in contours)
