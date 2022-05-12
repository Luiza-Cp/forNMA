#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 11 19:02:13 2022

@author: luiza

Code with auxiliary filter functions 
"""
import cv2 as cv
import numpy as np
import copy
import math
from typing import  List, Tuple


def filter_debree(
        contour_list: List[np.ndarray], 
        mag: int, 
        ps: float, 
        rf: float
) -> List[np.ndarray]:
    """
    Elimiates small objects based on the magnification (mag) and pixel size (ps). 
    This will prevent the code from analyzing spurious contours.
    """
    min_val = 15*mag*ps*rf      # this is an arbitrary small value
    areas = []
    for cnt in contour_list:
        areas.append(cv.contourArea(cnt))
    contour_list2 = [b for a, b in zip(areas, contour_list) if a > min_val]  
    
    return contour_list2


def size_filter(
        contours: np.ndarray, 
        area_list: List[float], 
        min_size: int, 
        max_size: int,
        
)-> Tuple[List[np.ndarray], List[float], List[float]]:
    """ 
    Filter objects according to the input values or sets 1/4 of the mean
    area as minimum value and 10 times the median as maximun value.
    """
    area_list2 =  copy.deepcopy(area_list)
    if min_size == None:
        min_size = (sum(area_list2)/len(area_list2))/4
    if max_size == None:
        i = round( len(area_list2)/2)
        area_list2.sort()
        median = area_list[i]
        max_size = 30*median
    filtered_contours = [b for a, b in zip(area_list, contours) if  min_size < a < max_size]  
   
    
    return filtered_contours


def radius_and_eccentricity_filter(
        contours: List[np.ndarray], 
        eccentricity: float, 
        min_radius: int, 
        max_radius: int,
) -> Tuple[List[np.ndarray], List[float], List[float]]:
    """
    Filters objects according to the given values of eccentricity, min radius 
    and max radius. If none of then is given, the filter is not applied. 
    This function will measure min and max radius of the fitting ellipse of the 
    object and the eccinticity is given by: 
        sqrt((major ellipse axis**2)-(minor ellipse axis** 2))/major ellipse axis
    """
    new_cnt_list = []
    if min_radius == None:
        min_radius = 0
    if eccentricity ==None:
        eccentricity = 1
    for i in range(len(contours)):
        center, axis, rotation = cv.fitEllipse(contours[i])
        w = axis[0]      # minor axis
        h = axis[1]         # major axis
        e = math.sqrt((h**2)- (w**2))/h**2       # eccentricity
        if max_radius == None or  h < max_radius:
            if w > min_radius and e < eccentricity:
                new_cnt_list.append(contours[i])
        else:
            continue
        
    return new_cnt_list
            

def hull_filter(
        contours: np.ndarray, 
        shape: float,
) -> Tuple[List[np.ndarray], List[float], List[float]]:
    """
    This function divides the area of the convex hull of a contour by its area 
    and removes the objects below this user-defined value.
    """
    extent_hull = []
    for cnt in contours:
        a = cv.contourArea(cnt)
        hull = cv.convexHull(cnt)
        hull_a = cv.contourArea(hull)
        if hull_a == 0:
            extent_hull = 0
        else:
            ex = a/hull_a
            extent_hull.append(ex)
    contours_list = [b for a, b in zip(extent_hull, contours) if a > shape]    
    
    return contours_list


def filter_contours(
        contour_list: List[np.ndarray], 
        mag: int, 
        px_s: float, 
        shape: float, 
        eccentricity: float, 
        min_size: int, 
        max_size: int, 
        min_radius: int, 
        max_radius: int,
        
) -> Tuple[List[np.ndarray], List[float], List[float]]:
    """
    Given a set of standard and user-defined parameters, it filters the contours 
    that does not match the conditions. Returns the filtered contour list.
    """
    areas = []
    for cnt in contour_list:
        areas.append(cv.contourArea(cnt))
    contours = size_filter(contour_list, areas, min_size, max_size)         

    if len(contours) == 0:
        return  []
    contours = hull_filter(contours, shape)
    
    if len(contours) == 0:
        return []
    if eccentricity != None or min_radius != None or max_radius !=None:
        contours = radius_and_eccentricity_filter(contours, eccentricity, 
                                            min_radius, max_radius)
    
    return contours
   