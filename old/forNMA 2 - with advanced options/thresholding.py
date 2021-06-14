# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 10:25:32 2021

@author: Luiza

This file contains the information for applying thresholds and a dictionary of thresholds
"""
from skimage.filters import threshold_isodata,threshold_li, threshold_local, threshold_mean, threshold_minimum, threshold_multiotsu, threshold_otsu, threshold_triangle, threshold_yen
import scipy 
import cv2 as cv
import numpy as np


def isodata(image: np.ndarray, offset: int) -> np.ndarray:
    """ Applies skimage isodata threshold. """
    thresh = threshold_isodata(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def li(image: np.ndarray, offset: int) -> np.ndarray:
    """ Applies skimage li threshold. """
    thresh = threshold_li(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def mean(image: np.ndarray, offset: int) -> np.ndarray:
    """ Applies skimage mean threshold. """
    thresh = threshold_mean(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def minimum(image: np.ndarray, offset: int) -> np.ndarray:
    """ Applies skimage minimum threshold. """
    thresh = threshold_minimum(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def otsu(image: np.ndarray, offset: int) -> np.ndarray:
    """ Applies skimage otsu threshold. """
    thresh = threshold_otsu(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def triangle(image: np.ndarray, offset: int) -> np.ndarray:
    """ Applies skimage triangle threshold. """
    thresh = threshold_triangle(image)
    print ('ok')
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary  

def yen(image: np.ndarray, offset: int) -> np.ndarray:
    """ Applies skimage yen threshold. """
    thresh = threshold_yen(image)
    binary = image <= thresh
    binary = binary.astype('uint8')
    return binary 

def median(image: np.ndarray, offset: int) -> np.ndarray:
    """Measures median of image and sets it as threshold. """
    thresh = np.median(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 
   
def multiotsu(image: np.ndarray, offset: int) -> np.ndarray:
    """ 
    Applies skimage mulitsu threshold, fill holes and
    inverts the image values.
    """
    thresh = threshold_multiotsu(image)
    binary = np.digitize(image, bins=thresh)
    binary = scipy.ndimage.morphology.binary_fill_holes(binary)
    binary = binary.astype('uint8')
    binary = cv.bitwise_not(binary)
    return binary

def local_mean(image: np.ndarray, offset: int) -> np.ndarray:
    """ 
    Applies skimage local threshold setting meran parameter then
    fills holes and inverts the image.
    """
    thresh = threshold_local(image, 37, offset= offset, method = 'mean')
    binary = image <= thresh 
    binary = scipy.ndimage.morphology.binary_fill_holes(binary)
    binary = binary.astype('uint8')
    binary = cv.bitwise_not(binary)
    binary = binary.astype('uint8')
    return binary

def local_gaussian(image: np.ndarray, offset: int) -> np.ndarray:
    """ 
    Applies skimage local threshold setting gaussian parameter then
    fills holes and inverts the image.
    """
    thresh = threshold_local(image, 37, offset= offset, method = 'gaussian')
    binary = image <= thresh 
    binary = scipy.ndimage.morphology.binary_fill_holes(binary)
    binary = binary.astype('uint8')
    binary = cv.bitwise_not(binary)
    binary = binary.astype('uint8')
    return binary

   
threshold_dict = {'isodata': isodata,'li': li,  'mean': mean, 'minimun': minimum,
                  'otsu': otsu, 'triangle': triangle, 'yen': yen, 'median': median,
                  'multiotsu': multiotsu, 'local_mean': local_mean, 
                  'local_gaussian': local_gaussian}

