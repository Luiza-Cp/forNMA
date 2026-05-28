#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 15:35:41 2022

@author: luiza
"""

import numpy as np
import cv2 as cv
import warnings
from cellpose import models, utils
from typing import Optional, List
from .find_contours import load_image
from .filters import filter_contours

CELLPOSE_MODEL_TYPES = ("nuclei", "cyto3", "cyto2", "cyto")
_MODEL_CACHE = {}


def get_cellpose_model(model_type: str = "nuclei", use_gpu: bool = False):
    """Load and cache Cellpose models by model type and GPU setting."""
    if model_type not in CELLPOSE_MODEL_TYPES:
        raise ValueError(
            f"Unknown Cellpose model '{model_type}'. Choose one of: {', '.join(CELLPOSE_MODEL_TYPES)}."
        )

    cache_key = (model_type, bool(use_gpu))
    if cache_key not in _MODEL_CACHE:
        _MODEL_CACHE[cache_key] = models.CellposeModel(
            pretrained_model=model_type,
            gpu=use_gpu,
        )
    return _MODEL_CACHE[cache_key]


def clear_cellpose_model_cache():
    """Clear cached Cellpose models. Mostly useful for tests or long sessions."""
    _MODEL_CACHE.clear()


def _mask_for_outlines(masks: np.ndarray) -> np.ndarray:
    """Return the 2D label mask expected by Cellpose outline extraction."""
    masks = np.asarray(masks)
    if masks.ndim == 3 and masks.shape[0] == 1:
        return masks[0]
    return masks


def _valid_contours(contours: List[np.ndarray]) -> List[np.ndarray]:
    """Keep only non-empty 2D contours that OpenCV can measure."""
    valid = []
    for cnt in contours:
        cnt = np.asarray(cnt)
        if cnt.ndim != 2 or cnt.shape[1] != 2 or len(cnt) < 6:
            continue
        cnt = np.ascontiguousarray(cnt, dtype=np.int32)
        if cv.contourArea(cnt) <= 0 or cv.moments(cnt)["m00"] == 0:
            continue
        valid.append(cnt)
    return valid


def remove_edge_cnt(outlines_cnt, shape):
    """ Gets a list of contours and removes contours that touches the image borders."""
    cnts_not_border = []
    for cnt in outlines_cnt:
        touch_edge = [f for f in cnt if 0 in f]
        touch_x_max = [f for f in cnt if f[0] == shape[0] - 1]
        touch_y_max = [f for f in cnt if f[1] == shape[1] - 1]
        if len(touch_edge) < 10 and len(touch_x_max) < 10 and len(touch_y_max) < 10:
            cnts_not_border.append(cnt)

    return cnts_not_border


def run_cellpose(image_path: str,
                 use_gpu: bool,
                 diameter: Optional[int],
                 mag: int,
                 px_s: float,
                 shape: float,
                 eccentricity: float,
                 min_size: int,
                 max_size: int,
                 min_radius: int,
                 max_radius: int,
                 model_type: str = "nuclei",
                 invert: bool = True,
                 normalize: bool = True,
                 resample: bool = True,
                 rescale_intensity: bool = False,
                 remove_bg: bool = False,
                 radius_bg: int = 30,
                 flow_threshold: float = 0.4,
                 cellprob_threshold: float = 0,
                 model=None,
                 ) -> List[np.ndarray]:
    """
    Runs Cellpose in a specified image and returns a list of filtered contours.
    """
    warnings.warn(
                "⚠️ Even if you selected GPU, Cellpose may still be running on CPU. "
        "This can be very slow. For better performance, make sure CUDA is installed "
        "and that you are using a GPU-enabled version of PyTorch.",
        UserWarning
    )
    image = load_image(
        image_path,
        rescale_intensity=rescale_intensity,
        remove_bg=remove_bg,
        radius_bg=radius_bg,
    )
    if model is None:
        model = get_cellpose_model(model_type=model_type, use_gpu=use_gpu)

    masks, flows, styles = model.eval(
        image,
        channels=[0, 0],
        invert=invert,
        normalize=normalize,
        resample=resample,
        flow_threshold=flow_threshold,
        min_size=5,
        diameter=diameter,
        cellprob_threshold=cellprob_threshold,
        augment=False,
    )

    mask = _mask_for_outlines(masks)
    outlines_cnt = _valid_contours(utils.outlines_list(mask))
    outlines_cnt = remove_edge_cnt(outlines_cnt, image.shape)
    outlines_cnt = filter_contours(
        outlines_cnt,
        mag,
        px_s,
        shape,
        eccentricity,
        min_size,
        max_size,
        min_radius,
        max_radius,
        apply_default_size_filter=False,
    )

    return outlines_cnt
