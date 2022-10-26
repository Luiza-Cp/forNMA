#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 11 18:52:58 2022

@author: luiza

Functions to find nucleus that are either smaller or bigger than the contour
provided based on intensity adjacent to nucleus.
"""


from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
from .thresholding import threshold_dict
from typing import  List, Tuple


def adjust_low_res_binary_img(
        binary_image: np.ndarray, 
        kernel: np.ndarray, 
        px_s: float
) -> np.ndarray:
    """ Performs morphological operations in the given image. """
    dilate =  cv.dilate (binary_image, kernel, iterations=round(0.65/px_s))
    erode =  cv.erode (dilate, kernel, iterations=1)
   
    return erode


def adjust_high_res_binary_img(
        binary_image: np.ndarray, 
        kernel: np.ndarray, 
        px_s: float
) -> np.ndarray:
    """ Performs morphological operations in the given image. """
    dilate =  cv.dilate (binary_image, kernel, iterations=round(0.65/px_s))
    close = cv.morphologyEx(dilate, cv.MORPH_CLOSE, kernel, iterations=round(0.22/px_s))
    erode =  cv.erode (close, kernel, iterations=2)
    
    return erode


def blur_binary(
        binary_img: np.ndarray,
        mag: int,
        blur: int,
        kernel_size: int,
        rf: float
) -> np.ndarray:        
    """ It applyes a series of blur to image in order to smooth contours. """   
    if mag < 20: 
        blur = blur/4   #Too much blur can make small objects disapear, so we reduce the user input value in these cases
    range_to_use = round(blur*rf)
    if range_to_use == 0:
        range_to_use =1
    for i in range(round(range_to_use)):     #the amount of blur deppends on the input and the resolution factor
        binary = cv.blur(binary_img,(kernel_size,kernel_size))
    binary = clear_border(cv.bitwise_not(binary)) 
    
    return binary.astype('uint8')   


def adjust_binary_size(
        binary_img: np.ndarray,
        adjust_size: int
) -> np.ndarray:
     """ Applies morphological transformations according to user's input. """
     kernel = np.ones((3,3), np.uint8)  
     if adjust_size > 0: #here we dilate and erode according to user's needs
        binary_img= cv.dilate(binary_img, kernel, iterations=adjust_size)
     if adjust_size < 0:
        binary_img = cv.erode(binary_img, kernel, iterations=adjust_size*-1) 
    
     return binary_img
    
    
def adjust_binary_image(
        binary_image: np.ndarray, 
        pixel_size: float, 
        rf: float, 
        blur: int, 
        magnification: int, 
        adjust_size: int
) -> np.ndarray:
    """
    This function applies adjust_low_res_binary_img and adjust_high_res_binary_img 
    according to the image resolution given by its pixel_size and creates a blur
    kernel proportional to its resolution. Then it applies ajust_binary_size.
    """
    kernel = np.ones((3,3), np.uint8) 
    if pixel_size > 0.3:
        bin_im = adjust_low_res_binary_img(binary_image, kernel, pixel_size)
        kernel_size = 9     # a bigger kernel makes blur more efficient
    else: 
        bin_im = adjust_high_res_binary_img(binary_image, kernel, pixel_size)
        kernel_size = round(1/pixel_size)
        if kernel_size %2 ==0:
            kernel_size = kernel_size+1     # the blur kernel depends on the image resolution, except for low resolution images
    bin_im = bin_im.astype(np.uint8)
    bin_im = blur_binary(bin_im, magnification, blur, kernel_size, rf)
    bin_im =  adjust_binary_size(bin_im, adjust_size)
  
    return bin_im


def find_rings(
        image: np.ndarray, 
        contour: np.ndarray, 
        rf: float, 
        mag: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ Create the mask for the inner ring, outter ring and inner small nucleus """
    blank_img = np.full((image.shape), 255, dtype = "uint8")
    object_img =  cv.drawContours(blank_img, [contour], 0, (0,0,0), -1)
    kernel = np.ones((3,3), np.uint8)
    nuc_mask = cv.bitwise_not(object_img)
    if mag < 15:
        erode_nuc = cv.erode(nuc_mask.copy(), kernel, iterations=round(2*rf))
        dilate_nuc = cv.dilate(nuc_mask.copy(), kernel, iterations=round(2*rf))
    else:
        erode_nuc = cv.erode(nuc_mask.copy(), kernel, iterations=round(7*rf))
        dilate_nuc = cv.dilate(nuc_mask.copy(), kernel, iterations=round(7*rf))
    outter_ring_mask = cv.bitwise_and(dilate_nuc, object_img.copy())
    inner_nuc_mask = erode_nuc
    inner_ring_mask = cv.bitwise_xor(inner_nuc_mask, nuc_mask.copy())

    return nuc_mask, inner_ring_mask, outter_ring_mask, inner_nuc_mask
   
    
def find_bigger_bbox(
        x: int,
        y: int,
        w: int,
        h: int, 
        img: np.ndarray, 
        rf: float
) -> Tuple[int, int, int, int]:
    """Finds coordinates for a new bounding box 120*resolution_factor pixesl bigger """
    x2 = x - round(60*rf)
    y2 = y - round(60*rf)
    w2 = w + round(120*rf)
    h2 = h + round(120*rf)
    if x2 < 0:
        x2 = 0
    if y2 < 0:
        y2=0
    if w2 > img.shape[1]:
        w2 = img.shape[1] 
    if h2 > img.shape[0]:
        h2 = img.shape[0]   
   
    return x2,y2,w2,h2


def adjust_contour_for_image(
        contour_list: List[np.ndarray], 
        x: int, 
        y: int
) -> List[np.ndarray]:
    """ For each position in the contour, adds a value in x and y to fit in the whole image"""
    adjusted_contour =[]
    for contour in contour_list:
        for pix in contour:
            pix[0][0] = pix[0][0] + x
            pix[0][1] = pix[0][1] + y
        adjusted_contour.append(contour)  
    
    return adjusted_contour


def adjust_small_contour(
        contour: np.ndarray, 
        img: np.ndarray, 
        rf: float, 
        px_s: float, 
        mag: int
) -> np.ndarray:
    """ 
    Applied when a given contour is considered smaller than the nucleus it
    represents. This function gets a ROI of the image with the wrong contoured
    nucleus and thresholds it again utilizing the mean algorithm, adjusts the
    binary image generated and finds a new contour. 
    """
    x,y,w,h = cv.boundingRect(contour)
    x2,y2,w2,h2 = find_bigger_bbox(x, y, w, h, img, rf)
    binary = threshold_dict['mean'](img[y2:y2+h2, x2:x2+w2], 0)
    for i in range(round(rf*5)):
        binary = cv.blur(binary, (3, 3), 2)
    binary= adjust_binary_image(binary, px_s, rf, 12, mag, 0)
    new_contour, hrc = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    new_contour = adjust_contour_for_image(new_contour, x2, y2)
    if len(new_contour) > 0:
        cnt = new_contour[0]
    else: 
        cnt = contour

    return cnt


def adjust_large_contour(
        contour: np.ndarray, 
        img: np.ndarray, 
        rf: float, 
        px_s: float, 
        mag: int
) -> np.ndarray:
    """ 
    Applied when a given contour is considered bigger than the nucleus it
    represents. This function gets a ROI of the image with the wrong contoured
    nucleus and thresholds it again utilizing the mean algorithm, adjusts the
    binary image generated and finds a new contour. 
    """
    x,y,w,h = cv.boundingRect(contour)
    x2,y2,w2,h2 = find_bigger_bbox(x, y, w, h, img, rf)
    binary = threshold_dict['mean'](img[y2:y2+h2, x2:x2+h2], 0)
    for i in range(round(rf*5)):
        binary = cv.blur(binary, (3, 3), 2)
    binary= adjust_binary_image(binary, px_s, rf, 12, mag, 0)
    new_contour, hrc = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    new_contour = adjust_contour_for_image(new_contour, x2, y2)
    if len(new_contour) > 0:
        cnt = new_contour[0]
    else: 
        cnt = contour

    return cnt

# Não testei o large, preciso encontrar imagens de exemplo pra ver o que aconteceeeee
# TESTAR O LARGE AQUI 

def fluorescence_of_rings(
        contour_list: List[np.ndarray], 
        img: np.ndarray, 
        rf: float, 
        px_s: float, 
        mag: int
) -> List[np.ndarray]:
    """ 
    This function will measure the fluorescence mean intensity of a ring in the
    outside and inside of the nucleus and chek wether it is well delimited.
    If contour is bigger or smaller than the nucleus at image, it will be
    adjusted and the function returns the corrected contours.
    
    """
    new_cnt_list = []
   
    for cnt in contour_list:
        nuc, inner_ring, outter_ring, inner_nuc = find_rings(img, cnt, rf, mag)
        mean_inner_ring = cv.mean(img, mask = inner_ring)[0]
        mean_outter_ring = cv.mean(img, mask = outter_ring)[0]
        mean_inner_nuc = cv.mean(img, mask = inner_nuc)[0]
        mean_nuc = cv.mean(img, mask = nuc)[0]
        if mean_nuc == 0 or mean_inner_nuc == 0:
            continue
        else:
            int_out = mean_outter_ring/mean_nuc 
            int_in = mean_inner_ring/mean_inner_nuc 
            
            if int_out > 0.5:     # contour smaller the the nucleus
               new_cnt = adjust_small_contour(cnt, img, rf, px_s, mag)
               new_cnt_list.append(new_cnt)
            elif int_in < 0.7:      # contour bigger than the nucleus
               new_cnt = adjust_large_contour(cnt, img, rf, px_s, mag)
               new_cnt_list.append(new_cnt)
            else:       # right contour
                new_cnt_list.append(cnt)
                
     
   
    return new_cnt_list
  
