# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 10:25:32 2021

@author: Luiza
"""
from skimage.filters import threshold_isodata,threshold_li, threshold_local, threshold_mean, threshold_minimum, threshold_multiotsu, threshold_otsu, threshold_triangle, threshold_yen
import scipy 
import cv2 as cv
import numpy as np


def isodata(image, offset):
    thresh = threshold_isodata(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def li(image, offset):
    thresh = threshold_li(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def mean(image, offset):
    thresh = threshold_mean(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def minimum(image, offset):
    thresh = threshold_minimum(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def otsu(image, offset):
    thresh = threshold_otsu(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 

def triangle(image, offset):
    thresh = threshold_triangle(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary  

def yen(image, offset):
    thresh = threshold_yen(image)
    binary = image <= thresh
    binary = binary.astype('uint8')
    return binary 

def median(image, offset):
    thresh = np.median(image)
    binary = image <= thresh 
    binary = binary.astype('uint8')
    return binary 
   
def multiotsu(image, offset):
    thresh = threshold_multiotsu(image)
    binary = np.digitize(image, bins=thresh)
    binary = scipy.ndimage.morphology.binary_fill_holes(binary)
    binary = binary.astype('uint8')
    binary = cv.bitwise_not(binary)
    return binary

def local_mean(image, offset):
    thresh = threshold_local(image, 37, offset= offset, method = 'mean')
    binary = image <= thresh 
    binary = scipy.ndimage.morphology.binary_fill_holes(binary)
    binary = binary.astype('uint8')
    binary = cv.bitwise_not(binary)
    binary = binary.astype('uint8')
    return binary

def local_gaussian(image, offset):
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

