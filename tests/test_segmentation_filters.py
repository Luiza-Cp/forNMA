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
