import cv2 as cv
import numpy as np

from fornma.core.image_io import imread, imwrite


def test_image_io_handles_spaces_and_accents(tmp_path):
    image_dir = tmp_path / "condição com espaço"
    image_path = image_dir / "núcleo 01.tif"
    image = (np.arange(100, dtype=np.uint16).reshape(10, 10) * 10)

    assert imwrite(image_path, image)

    loaded = imread(image_path, cv.IMREAD_ANYDEPTH)

    assert loaded is not None
    assert loaded.dtype == image.dtype
    assert loaded.shape == image.shape
    np.testing.assert_array_equal(loaded, image)
