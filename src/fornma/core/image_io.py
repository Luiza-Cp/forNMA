from pathlib import Path
from typing import Any

import cv2 as cv
import numpy as np


def imread(path: str | Path, flags: int = cv.IMREAD_COLOR) -> np.ndarray | None:
    """Read an image from paths with spaces or non-ASCII characters."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv.imdecode(data, flags)


def imwrite(path: str | Path, image: np.ndarray, params: Any = None) -> bool:
    """Write an image to paths with spaces or non-ASCII characters."""
    path = Path(path)
    ext = path.suffix or ".png"
    encode_params = [] if params is None else params
    ok, encoded = cv.imencode(ext, image, encode_params)
    if not ok:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded.tofile(str(path))
    except OSError:
        return False
    return True
