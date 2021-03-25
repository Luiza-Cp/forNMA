# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 08:00:35 2021

@author: Luiza-
"""

from matplotlib import pyplot as plt
from skimage import io, img_as_float, exposure,color
from skimage.filters import   threshold_isodata,threshold_li, threshold_local, threshold_mean, threshold_minimum, threshold_multiotsu, threshold_niblack, threshold_otsu, threshold_sauvola, threshold_triangle, threshold_yen
from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
import copy
from Cell_class_new import Cell 
import os
import math


def set_threshold(image, thresholding_method):
    if thresholding_method == 'isodata':
        thresh = threshold_isodata(image)
        binary = image <= thresh 
    if thresholding_method == 'li':
        thresh = threshold_li(image)
        binary = image <= thresh 
    if thresholding_method == 'local': # Não sei como usar isso - remover maybe
        thresh = threshold_local(image, 37, offset= 0, method = 'gaussian')
        binary = image >= thresh 
    if thresholding_method == 'mean':
        thresh = threshold_mean(image)
        binary = image <= thresh 
    if thresholding_method == 'minimum':
        thresh = threshold_minimum(image)
        binary = image <= thresh 
    if thresholding_method == 'multiotsu':
        thresholds = threshold_multiotsu(image)
        binary = np.digitize(image, bins=thresholds)
    if thresholding_method == 'otsu':
        thresh = threshold_otsu(image)
        binary = image <= thresh  
    if thresholding_method == 'triangle':
        thresh = threshold_triangle(image)
        binary = image <= thresh 
    if thresholding_method == 'yen':
        thresh = threshold_yen(image)
        binary = image <= thresh 
    binary = binary.astype('uint8')
    
    return binary 
        
        
def read_image(file):
    img = cv.imread(file,cv.IMREAD_ANYDEPTH)
    if  img is None or img.size ==0:
        raise ValueError ("This file can not be opened")
    return (img)


#generate_cell_list = run image
#valores com None aceitam números 
     
def run_image(filename, magnification, pixel_size = 0.5, filename2= None, 
              threshold = 'triangle' , blur = 12, adjust_size = 0, cut_edges = 0.7,
              extent = None, eccentricity = None, min_size = None, max_size = None, 
              error= None, wants_ktr = False, ring_size = 1.75, use_ellipse = False, 
              wants_foci = None, foci_channel2 = False, foci_min_size = None, 
              foci_max_size = None, foci_min_int = None, foci_max_int = None,
              foci_min_rel_int = None, foci_max_re_int = None, foci_eccentricity=None):
    
    

    
    img= read_image(filename)
    binary = set_threshold(img, threshold)
    if filename2 is not None:
        img2 = read_image(filename2)
    
    ring_size = round(ring_size/pixel_size)
    
    plt.imshow(binary, cmap = 'gray')
    
    
    

um = 'D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\clonogenico 2 kaka\\Pre TMZ\\Cyto\\Green\\VID53_D6_7_2020y12m18d_23h00m.tif'
dois= 'D:\\Doutorado\\53BP1\\Outras img\\40x\\a.tif'
tres = 'D:\\Doutorado\\53BP1\\Outras img\\20x\\a.tif'
quatro = 'C:\\Users\\Luiza Cherobini\\Desktop\\Nucear detection validation\\40x\\Slide 1_RPE WT PDS 4uM 4hrs_FOV 00285_DAPI.tif'
run_image(um,  20, pixel_size = 0.65)
