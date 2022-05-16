# -*- coding: utf-8 -*-
"""
Created on Sun May 16 14:32:54 2021

@author: Luiza

Code with all contour finding functions
"""

import cv2 as cv
import numpy as np
from skimage import  img_as_ubyte, exposure, restoration
from skimage.exposure import match_histograms
from typing import Optional, List, Tuple
from segmentation.thresholding import threshold_dict
from segmentation.Divide_contours import Segmenting, select_right_contour  
from segmentation.weak_label import fluorescence_of_rings, adjust_binary_image
from segmentation.filters import filter_debree, filter_contours

not_processed = [] # PENSAR NO QUE FAZER COM ISSO 

def load_image(
        filename: str,
        rescale_intensity: bool = False,
        remove_bg: bool = False,
        radius_bg: int = 30,
        ref: Optional[np.ndarray] = None
) -> Optional[np.array]:
    """ 
    It opens the image, performs intensity adjustments, if required, and
    converts image to ubyte. If file can not be opened, adds the file
    to not_procesed list.
    """
    print ('file: ',filename)
    img = cv.imread(filename,cv.IMREAD_ANYDEPTH)
    if  img is None or img.size == 0:
        not_processed.append(filename)
        return None
    
    if ref is not None:
        img = match_histograms(img, ref)
        img =img.astype('ubyte')

    if rescale_intensity == True:
        img = exposure.rescale_intensity(img, in_range='image', out_range='dtype')
    elif img.dtype.kind == 'f' and (np.any(img>1) or np.any(img<-1)):
        img = exposure.rescale_intensity(img, in_range='image', out_range='dtype')
        
    img = img_as_ubyte(img) 

    if remove_bg == True:
        img = cv.GaussianBlur(img,(5,5),0)
        background = restoration.rolling_ball(img, radius = radius_bg )
        img = img-background
     
    return img      


def find_extent_convex_hull(contour: np.ndarray
) -> Tuple[float, int, int, int, int]:
    """ 
    Given a contour, it measures the ratio between the object area and its 
    convex hull.This value will be called extent_hull. 
    Returns the extent_hull and bounding rectangle coordinates information.
    """
    x,y,w,h = cv.boundingRect(contour)
    a = cv.contourArea(contour)
    hull = cv.convexHull(contour)
    hull_a = cv.contourArea(hull)
    if hull_a == 0:
        extent_hull = 0
    else:
        extent_hull = a/hull_a
   
    return extent_hull, x, y, w, h


def divide_contours(
        contours_list: List[np.ndarray],
        bin_img: np.ndarray, 
        img: np.ndarray, 
        rf: float, 
        px_s: float, 
        cut_edges: float
) -> List[np.ndarray]:
    """
    It checks if a contour is regular - a high extent_hull value - or irregular. An
    irregular contour can mean that two nuclei are together and were not divided during
    thresholding. When this happens, we will try to segment them in other manners.
    """
    new_cnt_list = []
    for contour in contours_list:
        extent_hull, x, y, w, h = find_extent_convex_hull(contour)
        if extent_hull > 0.95: # objects with smaller values will pass to a segmentation class, that tries to divide them
            new_cnt_list.append(contour)  
        else:
            segmented = Segmenting(contour, img, rf, px_s, extent_hull, x, y, w, h, cut_edges)
            for cnt in segmented.true_contour: 
                # sometimes Segmenting returns a list containig the contour, 
                # so we check this first
                if isinstance(cnt, np.ndarray):
                   new_cnt_list.append(cnt)
                else: # If it returns the list, we just have to append the contour inside it
                    new_cnt_list.append(cnt[0])           
     
   
    return new_cnt_list


def find_nuc_contours(
        binary_img: np.ndarray, 
        image: np.ndarray, 
        rf: float, 
        px_s: float, 
        mag: int, 
        cut_edges: float, 
        adjust_size: int, 
        shape: float, 
        eccentricity: float, 
        min_size: int, 
        max_size: int, 
        min_radius: int, 
        max_radius: int, 
        fast: bool,
        weakly_labeled: bool
) -> List[np.ndarray]:
    """ 
    Given an image, its binary and a set of parameters, aplies a series of
    functions to find nuclei contours and filter them.
    It returns the contours list of the image.
    """
    contours, hierarchy = cv.findContours(binary_img, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    contours = select_right_contour(contours, hierarchy)
    contours = [a for a in contours if len(a)>4]
    contours = divide_contours(contours, binary_img, image, rf, px_s, cut_edges)
    contours = filter_debree(contours, mag, px_s, rf)
   
    if weakly_labeled == True:
        contours = fluorescence_of_rings(contours, image, rf, px_s, mag)
        
    if len(contours)> 0:
        contours = filter_contours(contours, mag, px_s, shape, eccentricity, min_size,
                               max_size, min_radius, max_radius)
    
    return contours


def erase_image(
        contour_list: np.ndarray, 
        image: np.ndarray, 
        rf: float
)-> np.ndarray:
    """
    Creates a box at image covring the object. The box color will be given by
    the intensity of pixel corresponding to 0.1 quantile of the image.
    Returns the image with erased objects.
    """
    f = np.quantile(image, 0.1)
    for cnt in contour_list:
        x,y,w,h = cv.boundingRect(cnt)
        x2 = x - round(7*rf)
        y2 = y - round(7*rf)
        w2 = w + round(14*rf)
        h2 = h + round(14*rf)
        image_erased = cv.rectangle(image,(x2,y2),(x2+w2,y2+h2),(f,f,f),-1)
   
    return image_erased  

     
def fornma_contour_finding(
        image_path: str, 
        magnification: int, 
        pixel_size: Optional[float] = 0.5, 
        rescale_intensity: Optional[bool] = False, 
        remove_bg: Optional[bool] = False,
        radius_bg: Optional[int] = None,
        threshold: Optional[str] = 'triangle', 
        offset: Optional[int] = 0, 
        blur: Optional[int] = 12, 
        adjust_size: Optional[int] = 0, 
        cut_edges: Optional[float] = 0.7, 
        shape: Optional[float] = 0.88, 
        eccentricity: Optional[float] = None, 
        min_size: Optional[int] = None, 
        max_size: Optional[int] = None, 
        min_radius: Optional[int] = None, 
        max_radius: Optional[int] = None, 
        fast_detection: bool = False,
        weakly_labeled: bool = False
) -> List[np.ndarray]:
    """
    Performs all the operations in one image to generate a contour list.
    It first Loads the image removing background and rescaling intensities,
    if required by user.
    Then, it applies a threshold and makes the necessary adjustments and 
    obtains contours form the binary image.
    If user do not enable fast_mode, all objects within a image will be 
    erased with a black box and the image will be analyzed again, in a maximum
    range of 6 times, allowing for low fluorescence nuclei to be detected.
    If nothing is detected, the image will be considered empty, 
    untill thresholding settings are changed by user.
    """
    
    img = load_image(image_path, rescale_intensity= rescale_intensity, 
                     remove_bg = remove_bg, radius_bg = radius_bg)
    
    if magnification < 10:
        pixel_size = 0.5                        # standard for small objects   
    resolution_factor = img.size/4194304        # used to compensate some iterations
 
    binary = threshold_dict[threshold](img, offset) # binarize images
    binary= adjust_binary_image(binary, pixel_size, resolution_factor, blur, 
                                magnification, adjust_size)
   
    all_contours = [] 
   

    if not binary.any() == False:   #if binary image is not empty, it searches for nuclei 
        nuc_contours = find_nuc_contours(binary, img, 
                                         resolution_factor, pixel_size,
                                         magnification, cut_edges, adjust_size,
                                         shape, eccentricity, min_size, max_size,
                                         min_radius, max_radius, fast_detection,
                                         weakly_labeled)
        
        if len(nuc_contours) > 0:   # if it finds nuclear contours, it create a Cell object for each contour
            for i in range(len(nuc_contours)):
                all_contours.append(nuc_contours[i])
               
            
    else:
        nuc_contours = [] 
    image_erased =img.copy()
    if fast_detection == True: 
        # fast_detection mudou o nome para find low intensity. Se é true, busca mais nucs em novas rodadas
       
        # it tries to find nuclei with less ifluorescence intensity by covering 
        # the already detected ones. If after 6 rounds of covering nuclei it still 
        # finds objects, forNMA will ignore them
        
        n = 0
        while len(nuc_contours) > 0 and n < 6:
            n = n + 1
            image_erased = erase_image(nuc_contours,image_erased, resolution_factor)
            if not image_erased.any() == False:
                new_binary = threshold_dict[threshold](image_erased, offset)
                new_binary = adjust_binary_image(new_binary, pixel_size, resolution_factor, blur, 
                                              magnification, adjust_size)

                if not new_binary.any() ==True:
                    nuc_contours = []
                else:
                    nuc_contours= find_nuc_contours(new_binary, 
                                             img, resolution_factor, pixel_size,
                                             magnification, cut_edges, adjust_size,
                                             shape, eccentricity, min_size, max_size,
                                             min_radius, max_radius, fast_detection,
                                             weakly_labeled)
                   
                    if len(nuc_contours) > 0:
                        for i in range(len(nuc_contours)):
                            all_contours.append(nuc_contours[i])
 
            
    return all_contours 
 
    
 