# -*- coding: utf-8 -*-
"""
Created on Sun May 16 14:32:54 2021

@author: Luiza

Função que processa a imagem principal (ch 1) e encontra os nucleos.
Busca os contornos somente (no load não vai remover bg ou match histog.)

Análoga à RUN_IMAGE

"""


from skimage import  img_as_ubyte, exposure
from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
import copy
import math
from initializing_functions_multichannel import load_image, adjust_binary_image, find_nuc_contours, erase_image
from Divide_contours import Segmenting, select_right_contour
from thresholding import threshold_dict
from typing import Optional, List, Tuple
      

     
def find_contours(
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
) -> List[np.ndarray]:
    """
    Performs all the operations in one image to generate a contour list.
    It first Loads the image removing background and rescaling intensities,
    if required by user.
    Then, it applies a threshold and makes the necessary adjustments.
    From the binary image, the contours are obtained.
    If user do not enable fast_mode, all objects within a image will be 
    erased with a black box and the image will be analyzed again, in a maximum
    range of 6 times, allowing for low fluorescence nuclei to be detected.
    If nothing is detected, the image will be considered empty, 
    untill thresholding settings are changed by user.
    """
    
    img = load_image(image_path, rescale_intensity= rescale_intensity, 
                     remove_bg = remove_bg, radius_bg = radius_bg)
    if magnification < 10:
        pixel_size = 0.5        # standard for small objects   
    resolution_factor = img.size/4194304        # used to compensate some iterations
 
    binary = threshold_dict[threshold](img, offset)
    binary= adjust_binary_image(binary, pixel_size, resolution_factor, blur, 
                                magnification, adjust_size)
   
    all_contours = [] 
   

    if not binary.any() == False:   #if binary image is not empty, it searches for nuclei 
        nuc_contours = find_nuc_contours(binary, img, 
                                        resolution_factor, pixel_size,
                                         magnification, cut_edges, adjust_size,
                                         shape, eccentricity, min_size, max_size,
                                         min_radius, max_radius, fast_detection)
        
        if len(nuc_contours) > 0:   #if it finds nuclear contours, it create a Cell object for each contour
            for i in range(len(nuc_contours)):
                all_contours.append(nuc_contours[i])
               
            
    else:
        nuc_contours = [] 
    img_to_fill =img.copy()
    if fast_detection == False:
        #it tries to find nuclei with less ifluorescence intensity by covering 
        #the already detected ones. If after 6 rounds of covering nuclei it still 
        #finds objects, forNMA will ignore them
        n = 0
        while len(nuc_contours) > 0 and n < 6:
            n = n + 1
            image_erased = erase_image(nuc_contours, img_to_fill, resolution_factor)
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
                                             min_radius, max_radius, fast_detection)
                   
                    if len(nuc_contours) > 0:
                        for i in range(len(nuc_contours)):
                            all_contours.append(nuc_contours[i])
                            
                            
            
    return all_contours 
 
    
 
    
#im = 'C:\\Users\\Luiza Cherobini\\Desktop\\R\\RED\\red dap.tif'
#cnt = find_contours(im, 20)

#im = '/media/luiza/DATA/àrea de trabalho/video kaka/registradas/r/red/VID429-karine-red-erk53bp1-30min_B5_19_2021y02m28d_16h35m.tif'
#cnt = find_contours(im, 20, rescale_intensity= True)
