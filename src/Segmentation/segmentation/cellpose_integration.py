#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 15:35:41 2022

@author: luiza
"""

import numpy as np
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
                 invert: bool = False,
                 normalize: bool = True,
                 net_avg: bool = True,
                 resample: bool = True,
                 flow_threshold: float = 0.4,
                 mask_threshold: float = 0.0
                 ) -> List[np.ndarray]:
    """
    Runs cellpose nuclear model in a specified image and returns a
    list of filtered nuclei contours.
    """
    image = load_image(image_path)
    model = models.Cellpose(model_type='nuclei', gpu=use_gpu)
    channels = [[0, 0]]
    masks, flows, styles, diams = model.eval([image], diameter=diameter, channels=channels,
                                             invert=invert, normalize=normalize,
                                             net_avg=net_avg, resample=resample,
                                             flow_threshold=flow_threshold,
                                             mask_threshold=mask_threshold,
                                             min_size=min_size, )
    outlines_cnt = utils.outlines_list(masks[0])
    outlines_cnt = remove_edge_cnt(outlines_cnt, image.shape)
    if len(outlines_cnt) > 0:
        outlines_cnt = filter_contours(outlines_cnt, mag, px_s, shape, eccentricity,
                                       min_size, max_size, min_radius, max_radius)

    return outlines_cnt
