# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 05:22:04 2020

@author: Luiza

vai ser o initializing diferente
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 23:13:03 2020

@author: Luiza
"""
from matplotlib import pyplot as plt
from skimage import io, img_as_float, exposure,color
from skimage.filters import  threshold_triangle, threshold_yen
from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
import copy
from cell_class import cell 
import os
import math


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
        img2= cv.imread(image,cv.IMREAD_ANYDEPTH)
        binary = set_thresh_triangle(img2)
        binary = binary.astype('uint8')
    except:
        img1 = cv.imread(image, cv.IMREAD_ANYDEPTH)
        equalized_img1 = exposure.equalize_adapthist(img1) 
        img2= cv.imread(image, cv.IMREAD_ANYDEPTH)
        binary = set_thresh_yen(img2)  
        binary = binary.astype('uint8')
    return (equalized_img1, img2, binary)


def adjust_low_res_binary_img(binary_image, kernel, px_s):
    erode =  cv.erode (binary_image, kernel, iterations=1)
    dilate =  cv.dilate (erode, kernel, iterations=round(0.65/px_s))
    
    return dilate

def adjust_binary_img(binary_image, kernel, px_s):
    erode =  cv.erode (binary_image, kernel, iterations=1)
    opening = cv.morphologyEx(erode, cv.MORPH_OPEN, kernel, iterations=round(0.22/px_s))
    dilate =  cv.dilate (opening, kernel, iterations=round(0.65/px_s))
    binary_img=  cv.erode (dilate, kernel, iterations=round(0.65/px_s))
    return binary_img

def adjust_binary_image (binary_image, pixel_size, rf):
    binary_image = binary_image.astype(float)
    kernel = np.ones((3,3), np.uint8)
    
    if pixel_size > 0.3:
        bin_im = adjust_low_res_binary_img(binary_image, kernel, pixel_size)
       
        kernel_size = 9
    else: 
        bin_im = adjust_binary_img(binary_image, kernel, pixel_size)
        kernel_size = round(1/pixel_size)
        if kernel_size %2 ==0:
            kernel_size = kernel_size+1
          
    bin_im = bin_im.astype(np.uint8)
    for i in range(round(12*rf)):
        bin_im = cv.blur(bin_im,(kernel_size,kernel_size))
    
    bin_im = bin_im <1 
    bin_im = clear_border(bin_im) 
    bin_im = bin_im.astype('uint8')
   
    return bin_im

def find_extent_convex_hull(contour):
    x,y,w,h = cv.boundingRect(contour)
    a = cv.contourArea(contour)
    hull = cv.convexHull(contour)
    hull_a = cv.contourArea(hull)
    extent_hull = a/hull_a
    return extent_hull, x, y, w, h

def find_bigger_bbox(image, x, y, w, h, rf):
    x2 = x - round(60 *rf)
    y2 = y - round(60 *rf)
    w2 = w + round(120 *rf)
    h2 = h + round(120 *rf)
    if x2 < 0:
        x2 = 0
    if y2 < 0:
        y2=0
    if w2 > image.shape[1]:
        w2 = image.shape[1]
    if h2 > image.shape[0]:
        h2 = image.shape[0]   
    return x2,y2,w2,h2

def create_mask_binary_roi(x, y, w, h, contour, image):
    mask =  np.zeros((image.shape), dtype = "uint8")
    cv.drawContours(mask, [contour], -1, (255,255,255), -1)
    mask_roi = mask[y:y+h,x:x+w]
    return mask_roi    

def find_roi_bigger_bbox (image, binary_image, x, y, w, h, contour):
    roi_binary_image = binary_image[y:y+h,x:x+w]
    roi_binary_image = clear_border(roi_binary_image)
    roi_image = image[y:y+h,x:x+w]
    mask = create_mask_binary_roi(x, y, w, h, contour, image)
    roi_binary_image = cv.bitwise_and(roi_binary_image,roi_binary_image,mask = mask)
    roi_image = cv.bitwise_and(roi_image,roi_image,mask = mask)
    return roi_image, roi_binary_image

def find_backgroud_foreground_unkown (binary_image, kernel, rf):
    sure_bg = cv.dilate(binary_image, kernel, iterations=round(14*rf))
    dist_transform = cv.distanceTransform(binary_image,cv.DIST_L2,3)
    ret, sure_fg = cv.threshold(dist_transform,0.5*dist_transform.max(),255, 0)
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
 
def watershed(image, binary_image, rf, px_s):
    binary = binary_image.astype('uint8') 
    image = image.astype('uint8') 
    kernel = np.ones((3,3), np.uint8)
    bg, fg, unk = find_backgroud_foreground_unkown (binary, kernel, rf)
    markers = find_markers(image, fg, unk)  
    ret, image2 = cv.threshold(markers, 0, 255, cv.THRESH_BINARY|cv.THRESH_OTSU)
    for i in range(round(rf*22)):
         image2 = cv.blur(image2,(3,3))
    image2 =  cv.erode (image2, kernel, iterations=round(3*rf))
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

def main_defects(convexity_defects, contour):
    coordinate_far_list = []
    for i in range(convexity_defects.shape[0]):
        s,e,f,d = convexity_defects[i,0]
        far = tuple(contour[f][0])
        if d>300: #is 300 aplicable for all images? Maybe not - take a closer look
            coordinate_far_list.append(far)
    return coordinate_far_list

def find_smallest_distance(coordinate_list):
    coordinate_list2 = coordinate_list.copy()
    line_coord_list = []
    for coord1 in coordinate_list:
         dist_list = []
         for coord2 in coordinate_list2:
             if coord1 != coord2:
                 dist = math.sqrt((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)
                 dist_list.append(dist)
            
         if len(dist_list) > 0:            
             index = dist_list.index(min(dist_list))
             line_coord = (coordinate_list[index],coord1)
             line_coord_list.append(line_coord)
                     
    final_coord_dist = []
    for coord1, coord2 in line_coord_list:
        dist = math.sqrt((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)
        final_coord_dist.append(dist)
    f = np.array(final_coord_dist)
    i= np.where(f==np.min(f[np.nonzero(f)]))[0][0]
    dis = final_coord_dist[i]
    final = line_coord_list[i]
    return final, dis
           
def section_nuc(coordinate_list, binary_image, radius, x, y):
    if len(coordinate_list) == 2:
        dist = math.sqrt((coordinate_list[0][0]-coordinate_list[1][0])**2 + 
                         (coordinate_list[0][1]-coordinate_list[1][1])**2)
        if radius[0]*0.7 > dist:
            a = (coordinate_list[0][0]-x, coordinate_list[0][1]- y)
            b = (coordinate_list[1][0]-x, coordinate_list[1][1]- y)
            cv.line(binary_image,a, b,[0,0,0],3)            
    if len(coordinate_list)>2:
        new_line, dist2 = find_smallest_distance(coordinate_list)
        if radius[0]*0.7 > dist2:
            a = (new_line[0][0]-x, new_line[0][1]- y)
            b =  (new_line[1][0]-x, new_line[1][1]- y)
            cv.line(binary_image, a,b ,[0,0,0],3)     
    return binary_image    
            
def hull_defects(contour, binary_image,x,y):
    hull = cv.convexHull(contour,returnPoints=False)
    defects = cv.convexityDefects(contour, hull)
    if np.all(defects) != None :
        coordinate_far_list = main_defects(defects, contour) 
        if len(coordinate_far_list) == 0:
            return [contour]
        else:
            pos, radius, degree = cv.fitEllipse(contour)
            binary_image = section_nuc(coordinate_far_list, binary_image, radius,x,y) 
            new_contours, hierarchy =  cv.findContours(binary_image, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
            return new_contours
    else:
        return [contour]

def divide_contours(contours_list,bin_img, img, rf, px_s):
    '''pega a lista de contours e aplica ws no que for necessário'''
    new_cnt_list = []
    for contour in contours_list:
        extent, x, y, w, h = find_extent_convex_hull(contour)
        if extent > 0.95:
            new_cnt_list.append(contour)     
        else:
            x2,y2,w2,h2 = find_bigger_bbox(bin_img, x, y, w, h, rf)
            roi_img, roi_binary = find_roi_bigger_bbox(img, bin_img, x2, y2, w2, h2, contour)
            new_contour, hrc = watershed(roi_img, roi_binary, rf, px_s)
            new_contour = select_right_contour(new_contour, hrc)
            
            if x2==0 or y2==0 or w2 == bin_img.shape[1] or h2 == bin_img.shape[0] and len(new_contour) < 2:
                new_contour_hull = hull_defects(contour, roi_binary, x2, y2)
                if len(new_contour_hull) < 2:
                    new_cnt_list.append(contour)
                else:
                    new_contour_hull = adjust_contour_for_image(new_contour_hull, x2, y2)
                    for cnt_hull in new_contour_hull:
                        new_cnt_list.append(cnt_hull)
            
            else:     
                if len(new_contour) < 2:
                     new_contour_hull = hull_defects(contour, roi_binary,x2,y2)
                     if len(new_contour_hull) < 2:
                         new_cnt_list.append(contour)
                     else:
                         new_contour_hull = adjust_contour_for_image(new_contour_hull, x2, y2)
                         for cnt_hull in new_contour_hull:
                             new_cnt_list.append(cnt_hull)
                else:
                    new_contour_hull_list=[]
                    for cnt in new_contour:
                        new_contour_hull = hull_defects(contour, roi_binary,x2,y2)
                        for cnt_hull in new_contour_hull:
                            new_contour_hull_list.append(cnt_hull)      
                    if len(new_contour) < len(new_contour_hull_list):
                         new_contour_hull = adjust_contour_for_image(new_contour_hull, x2, y2)
                         for cnt_hull in new_contour_hull:
                             new_cnt_list.append(cnt_hull)  
                    else:    
                         new_contour = adjust_contour_for_image(new_contour, x2, y2)
                         for cnt in new_contour:
                             new_cnt_list.append(cnt)                                              
    return(new_cnt_list)


def filter_contour_by_size(contours_list, magnification, pixel_size):
    areas = []
    for cnt in contours_list:
        areas.append(cv.contourArea(cnt))
    area2 = copy.deepcopy(areas)
    if len (area2) > 0:
        i = round( len(areas)/2)
        area2.sort()
        median = area2[i]
        max_a = 15*median
        min1 = (sum(area2)/len(area2))/3
    
    else:
        max_a=0
        min1 = 0
    min2 = 15*magnification*pixel_size
    if min1>min2:
        min_a = min1
    else:
        min_a = min2
    contours_list2 = [b for a, b in zip(areas, contours_list) if a > min_a]  
    contours_list2 = [b for a, b in zip(areas, contours_list2) if a < max_a] 
    extent_hull = []
    for cnt in contours_list2:
        ex,_,_,_,_ = find_extent_convex_hull(cnt)
        extent_hull.append(ex)
    contours_list2 = [b for a, b in zip(extent_hull, contours_list2) if a > 0.88]    
    return (contours_list2)  

def find_nuc_contours(binary_image, image, rf, px_s, mag):
    contours, hierarchy = cv.findContours(binary_image, cv.RETR_TREE, 
                                                  cv.CHAIN_APPROX_NONE)
    contours = [a for a in contours if len(a)>4]
    contours = divide_contours(contours, binary_image, image, rf, px_s)
    contours = filter_contour_by_size(contours, mag, px_s)  
    return contours
    
def new_binary(image, pixel_size, resolution_factor):
    '''this function will generate the new binary without strong fluorescence nuc'''
    image = image.astype('uint8')
    binary = set_thresh_triangle(image)
    binary  =  adjust_binary_image(binary, pixel_size, resolution_factor)
    binary = binary.astype('uint8')
    print (not binary.any())
    return binary
    
def create_cells (contour_list, position, ring_size, resolution_factor, 
                        img, binary_img, wants_foci, magnification, pixel_size):
     cells_list = []
     for i in range (len(contour_list)):
            new_cell = cell(position, contour_list[i], ring_size, resolution_factor, 
                        img, binary_img, wants_foci, magnification, pixel_size)
            cells_list.append(new_cell)
            position = position + 1
     return  cells_list
            
            
            
#add msg sobre o pixel size, qie será considerado como 1 qdo não informado
#colocar um help com direcionamento para site do lab de como achar isso nas fotos
def generate_cell_list(filename, magnification, wants_foci, pixel_size = 0.5):
    eq_img, img, binary_img = read_image(filename)
    ring_size = round(1.75/pixel_size) 
    '''ring of 1.75um'''
    resolution_factor = img.size/4194304
    '''RF == resolution factor'''
    
    binary_img = adjust_binary_image(binary_img, pixel_size, resolution_factor)
    cells_list = []
    position = 1
    
    if not binary_img.any() == False:
        nuc_contours = find_nuc_contours(binary_img, img, resolution_factor, pixel_size, magnification)
        cells_l = create_cells (nuc_contours, position, ring_size, resolution_factor, 
                        img, binary_img, wants_foci, magnification, pixel_size)
        while len(cells_l) > 0:
            for item in cells_l:
                cells_list.append(item)
            for cnt in nuc_contours: 
                x,y,w,h = cv.boundingRect(cnt)
                x2 = x-3
                y2 = y-3
                w2 = w+6
                h2=h+6
                image_erased = cv.rectangle(img,(x2,y2),(x2+w2,y2+h2),(0,0,0),-1)
            binary_img = new_binary(image_erased, pixel_size, resolution_factor)
 
            if not binary_img.any() ==True:
                print (not binary_img.any())
                cells_l = []
            else:
                nuc_contours = find_nuc_contours(binary_img, img, resolution_factor, pixel_size, magnification)
                cells_l = create_cells (nuc_contours, position, ring_size, resolution_factor, 
                        img, binary_img, wants_foci, magnification, pixel_size)
    return cells_list

