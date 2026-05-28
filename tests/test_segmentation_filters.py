import numpy as np

from fornma.core.Segmentation.segmentation.filters import filter_contours


def test_filter_contours_skips_shape_filter_when_disabled():
    contour = np.array([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]], dtype=np.int32)

    filtered = filter_contours(
        [contour],
        mag=20,
        px_s=0.5,
        shape=None,
        eccentricity=None,
        min_size=None,
        max_size=None,
        min_radius=None,
        max_radius=None,
    )

    assert len(filtered) == 1


def test_filter_contours_cellpose_mode_skips_automatic_size_bounds():
    tiny = np.array([[[0, 0]], [[2, 0]], [[2, 2]], [[0, 2]]], dtype=np.int32)
    large = np.array([[[0, 0]], [[20, 0]], [[20, 20]], [[0, 20]]], dtype=np.int32)

    filtered = filter_contours(
        [tiny, large],
        mag=20,
        px_s=0.5,
        shape=None,
        eccentricity=None,
        min_size=None,
        max_size=None,
        min_radius=None,
        max_radius=None,
        apply_default_size_filter=False,
    )

    assert len(filtered) == 2


def test_filter_contours_cellpose_mode_still_applies_selected_size_bound():
    tiny = np.array([[[0, 0]], [[2, 0]], [[2, 2]], [[0, 2]]], dtype=np.int32)
    large = np.array([[[0, 0]], [[20, 0]], [[20, 20]], [[0, 20]]], dtype=np.int32)

    filtered = filter_contours(
        [tiny, large],
        mag=20,
        px_s=0.5,
        shape=None,
        eccentricity=None,
        min_size=20,
        max_size=None,
        min_radius=None,
        max_radius=None,
        apply_default_size_filter=False,
    )

    assert len(filtered) == 1
    np.testing.assert_array_equal(filtered[0], large)
