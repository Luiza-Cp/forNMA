# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 08:53:50 2020

@author: Luiza Cherobini
"""

from skimage import io, img_as_float, exposure,color
from skimage.filters import  threshold_triangle, threshold_yen
from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
import copy
from cell_class import cell 



def set_thresh_triangle (equalized_image):
    thresh = threshold_triangle(equalized_image)
    binary_img = equalized_image <= thresh 
    
    return binary_img

def set_thresh_yen (equalized_image):
    thresh = threshold_yen(equalized_image)
    binary_img = equalized_image <= thresh 
    return binary_img


def read_image(image):
    try:
        img1= img_as_float(io.imread(image,  plugin='pil'))
        equalized_img1 = exposure.equalize_adapthist(img1) 
        img2= cv.imread(image, 0)
        binary = set_thresh_triangle(equalized_img1)
    except:
        img1 = cv.imread(image, 0)
        equalized_img1 = exposure.equalize_adapthist(img1) 
        img2= cv.imread(image, 0)
        binary = set_thresh_yen(equalized_img1)  
    return (equalized_img1, img2, binary)

def adjust_small_nuc_binary_img(binary_image, kernel, rf):
    erode =  cv.erode (binary_image, kernel, iterations=1)
    dilate =  cv.dilate (erode, kernel, iterations=round(6*rf))
    return dilate

def adjust_large_nuc_binary_img(binary_image, kernel, rf):
    erode =  cv.erode (binary_image, kernel, iterations=1)
    opening = cv.morphologyEx(erode, cv.MORPH_OPEN, kernel, iterations=round(2*rf))
    dilate =  cv.dilate (opening, kernel, iterations=round(6*rf))
    binary_img=  cv.erode (dilate, kernel, iterations=round(6*rf))
   
    return binary_img

def adjust_binary_image (binary_image, rf, mag):
    binary_image = binary_image.astype(float)
    kernel = np.ones((3,3), np.uint8)
    if mag > 20:
       bin_im = adjust_large_nuc_binary_img(binary_image, kernel, rf)
    else:
        bin_im = adjust_small_nuc_binary_img(binary_image, kernel, rf)
    
    bin_im = bin_im.astype(np.uint8)
    for i in range(round(12*rf)):
        bin_im = cv.blur(bin_im,(9,9))
    bin_im = bin_im <1 
    bin_im = clear_border(bin_im) 
    bin_im = bin_im.astype('uint8')
    return bin_im

def find_arBox(contour):
    x,y,w,h = cv.boundingRect(contour)
    a = cv.contourArea(contour)
    arbox = a/(h*w)
    return arbox, x, y, w, h

def find_bigger_bbox(image, x, y, w, h, rf):
    x2 = x - round(50 *rf)
    y2 = y - round(50 *rf)
    w2 = w + round(100 *rf)
    h2 = h + round(100 *rf)
    if x2 < 0:
        x2 = 0
    if y2 < 0:
        y2=0
    if w2 > image.shape[1]:
        w2 = image.shape[1]
    if h2 > image.shape[0]:
        h2 = image.shape[0]
        
    return x2,y2,w2,h2

def find_roi_bigger_bbox (image, binary_image, x, y, w, h):
    roi_binary_image = binary_image[y:y+h,x:x+w]
    roi_binary_image = clear_border(roi_binary_image)
    roi_image = image[y:y+h,x:x+w]
    
    return roi_image, roi_binary_image

def find_backgroud_foreground_unkown (binary_image, kernel, rf):
    sure_bg = cv.dilate(binary_image, kernel, iterations=round(14*rf))
    dist_transform = cv.distanceTransform(binary_image,cv.DIST_L2,3)
    ret, sure_fg = cv.threshold(dist_transform,0.3*dist_transform.max(),255, 0)
    sure_fg= np.uint8(sure_fg) 
    unknown= cv.subtract(sure_bg, sure_fg)
    
    return sure_bg, sure_fg, unknown

def find_markers(image, foreground, unknown):
      ret_a, markers = cv.connectedComponents(foreground)
      markers = markers+10
      markers[unknown==1] = 0
      img =cv.cvtColor(image,cv.COLOR_GRAY2BGR)
      markers =cv.watershed(img, markers)
      img[markers == -1] = [0, 255, 255]
      img = color.label2rgb(markers, bg_label=0)
      markers = markers.astype(np.uint8)
      
      return markers
    

def watershed(image, binary_image, rf):
    binary = binary_image.astype('uint8') 
    image = image.astype('uint8') 
    kernel = np.ones((3,3), np.uint8)
    
    bg, fg, unk = find_backgroud_foreground_unkown (binary, kernel, rf)
    markers = find_markers(image, fg, unk)  
    
    ret, image2 = cv.threshold(markers, 0, 255, cv.THRESH_BINARY|cv.THRESH_OTSU)
    
    for i in range(round(rf*22)):
         image2 = cv.blur(image2,(3,3))
    image2 =  cv.erode (image2, kernel, iterations=round(6*rf))
    
    contours, hierarchy = cv.findContours(image2, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    
    return (contours, hierarchy)


def select_right_contour(contour_list, hierarchy):
     cnt_adjusted = [] 
     for i in range(len(contour_list)):
         if hierarchy[0,i,2] == -1:
             cnt_adjusted.append(np.array(contour_list[i]))
     return cnt_adjusted
 
def adjust_contour_for_image(contour_list, x, y):
    adjusted_contour =[]
    for contour in contour_list:
        for pix in contour:
            pix[0][0] = pix[0][0] + x
            pix[0][1] = pix[0][1] + y
        adjusted_contour.append(contour)  
    return adjusted_contour

def divide_contours(contours_list,bin_img, img, rf):
    '''pega a lista de contours e aplica ws no que for necessário'''
    new_cnt_list = []
    for contour in contours_list:
        arbox, x, y, w, h = find_arBox(contour)

        if arbox > 0.57:
            new_cnt_list.append(contour)
        
        else:
            x2,y2,w2,h2 = find_bigger_bbox(bin_img, x, y, w, h, rf)
            roi_img, roi_binary = find_roi_bigger_bbox(img, bin_img, x2, y2, w2, h2)
            
            new_contour, hrc = watershed(roi_img, roi_binary, rf)
            new_contour = select_right_contour(new_contour, hrc)
          
            
            if x2==0 or y2==0 or w2 == bin_img.shape[1] or h2 == bin_img.shape[0] and len(new_contour) < 2:
                new_cnt_list.append(contour)
            
            else:     
            
                if len(new_contour) < 2:
                    new_cnt_list.append(contour)
                else:
                     new_contour = adjust_contour_for_image(new_contour, x2, y2)
                     for cnt in new_contour:
                         new_cnt_list.append(cnt)
    
    return(new_cnt_list)

def filter_contour_by_size(contours_list):
    areas = []
    for cnt in contours_list:
        areas.append(cv.contourArea(cnt))
    area2 = copy.deepcopy(areas)
    i = round( len(areas)/2)
    area2.sort()
    median = area2[i]
    max_a = 15*median
    min_a = median/5
    contours_list2 = [b for a, b in zip(areas, contours_list) if a > min_a]  
    contours_list2 = [b for a, b in zip(areas, contours_list2) if a < max_a] 
    return (contours_list2)  

def find_nuc_contours(binary_image, image, rf):
    contours, hierarchy = cv.findContours(binary_image, cv.RETR_TREE, 
                                                  cv.CHAIN_APPROX_SIMPLE)
    contours = [a for a in contours if len(a)>4]
    contours = divide_contours(contours, binary_image, image, rf)
    contours = filter_contour_by_size(contours) 
    
    return contours
   
    

def calc_ring_size(magnification, resolution):
    if magnification <= 7:
        ring = 1.25
    if  7 < magnification <= 16:
        ring = 2.5
    if 16 < magnification <= 30:
        ring = 5
    if 30 < magnification <= 50:
        ring = 10
    if 50 < magnification <= 75:
        ring = 15
    if 75 < magnification <= 100:
        ring= 25
    ring = round(ring * resolution)
    
    return ring
    

def generate_cell_list(filename, magnification, wants_foci):
    eq_img, img, binary_img = read_image(filename)
    resolution_factor = img.size/4194304
    '''RF == resolution factor'''
    ring_size = calc_ring_size(magnification, resolution_factor)
        
    binary_img = adjust_binary_image(binary_img, resolution_factor, magnification)
    nuc_contours = find_nuc_contours(binary_img, img, resolution_factor)
        
    cells_list = []
    position = 1
    for i in range (len(nuc_contours)):
        new_cell = cell(position, nuc_contours[i], ring_size, resolution_factor, 
                        img, binary_img, wants_foci, magnification)
        cells_list.append(new_cell)
        position = position + 1
        
    return cells_list


