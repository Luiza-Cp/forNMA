#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 15:35:41 2022

@author: luiza
"""

import numpy as np
import warnings
from cellpose import models, utils
from typing import Optional, List
from .find_contours import load_image
from .filters import filter_contours


def remove_edge_cnt(outlines_cnt, shape):
    """ Gets a list of contours and removes contours that touches the image borders."""
    cnts_not_border = []
    for cnt in outlines_cnt:
        touch_edge = [f for f in cnt if 0 in f]
        touch_x_max = [f for f in cnt if f[0] == shape[0] - 1]
        touch_y_max = [f for f in cnt if f[1] == shape[0] - 1]
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
                 invert: bool = True,
                 normalize: bool = True,
                 resample: bool = True,
                 flow_threshold: float = 0.4,
                 cellprob_threshold: float = 0
                 ) -> List[np.ndarray]:
    """
    Runs cellpose nuclear model in a specified image and returns a
    list of filtered nuclei contours.
    """

    warnings.warn(
                "⚠️ Even if you selected GPU, Cellpose may still be running on CPU. "
        "This can be very slow. For better performance, make sure CUDA is installed "
        "and that you are using a GPU-enabled version of PyTorch.",
        UserWarning
    )
    image = load_image(image_path)
    model = models.CellposeModel(
        pretrained_model="nuclei",
        gpu=use_gpu,
    )

    masks, flows, styles = model.eval(
        image,
        channels=[0, 0],
        invert=invert,
        normalize=normalize,
        resample= False,#resample,
        flow_threshold= 0.0, #flow_threshold,
        min_size= 5 ,#-1 if min_size is None else min_size,
        diameter= None, #diameter,
        cellprob_threshold= -6, # cellprob_threshold,
        augment=False,
    )

    outlines_cnt = utils.outlines_list(masks[0])
    print(image.shape)
    print (len(outlines_cnt))
    print(masks[0].max())
    print(invert, normalize, resample, flow_threshold, min_size, diameter, cellprob_threshold)
    print(len(outlines_cnt))
    outlines_cnt = remove_edge_cnt(outlines_cnt, image.shape)
    print(len(outlines_cnt))
    if len(outlines_cnt) > 0:
        outlines_cnt = filter_contours(outlines_cnt, mag, px_s, shape, eccentricity,
                                       min_size, max_size, min_radius, max_radius)

    return outlines_cnt
