# -*- coding: utf-8 -*-
"""
Created on Sun May 16 15:09:48 2021

@author: Luiza
Contain all the necessary functions for processing the image for segmentation
"""

from skimage import  img_as_ubyte, exposure, restoration
from skimage.exposure import match_histograms
from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
import copy
import math
from Divide_contours import Segmenting, select_right_contour
from thresholding import threshold_dict
from typing import Optional, List, Tuple

#   A: esse lista serve pra guardar imagens que eventiualmente ele não consiga abrir
#e vão ser exibidas em forma de aviso na interface

not_processed = []
#remover Nones dessa lista no fim -> [x for x in L if x is not None]
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
        background = restoration.rolling_ball(img, radius = radius_bg )
        img = img-background
     
    return img
   

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
    for i in range(round(blur*rf)):     #the amount of blur deppends on the input and the resolution factor
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
        kernel_size = 9     # a bigger kernel makes the blur most efficient
    else: 
        bin_im = adjust_high_res_binary_img(binary_image, kernel, pixel_size)
        kernel_size = round(1/pixel_size)
        if kernel_size %2 ==0:
            kernel_size = kernel_size+1     # the blur kernel depends on the image resolution, except for low resolution images
    bin_im = bin_im.astype(np.uint8)
    bin_im = blur_binary(bin_im, magnification, blur, kernel_size, rf)
    bin_im =  adjust_binary_size(bin_im, adjust_size)
  
    return bin_im


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
    It checks if a contour is regular - a high extent_hull value - or irregular. A
    irregular contour can mean that two nuclei are together and were not divided during
    thresholding. When this happens, we will try to segment them in olther manners.
    """
    new_cnt_list = []
    for contour in contours_list:
        extent_hull, x, y, w, h = find_extent_convex_hull(contour)
        if extent_hull > 0.95: #objects with smaller values will pass to a segmentation class, that tries to divide them
            new_cnt_list.append(contour)  
        else:
            segmented = Segmenting(contour, img, rf, px_s, extent_hull, x, y, w, h, cut_edges)
            for cnt in segmented.true_contour: 
                #sometimes Segmenting returns a list containig the contour, 
                #so we check this first
                if isinstance(cnt, np.ndarray):
                   new_cnt_list.append(cnt)
                else: #If it returns the list, we just have to append the contour inside it
                    new_cnt_list.append(cnt[0])           
    
    return new_cnt_list


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
    int_in_list = [] 
    int_out_list= []
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
            int_in_list.append(int_in) 
            int_out_list.append(int_out)
            if int_out > 0.5:     # contour smaller the the nucleus
               new_cnt = adjust_small_contour(cnt, img, rf, px_s, mag)
               new_cnt_list.append(new_cnt)
            elif int_in < 0.7:      # contour bigger than the nucleus
               new_cnt = adjust_large_contour(cnt, img, rf, px_s, mag)
               new_cnt_list.append(new_cnt)
            else:       # right contour
                new_cnt_list.append(cnt)
   
    return new_cnt_list, int_in_list, int_out_list
  

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
        in_l: List[float],
        out_l: List[float]
)-> Tuple[List[np.ndarray], List[float], List[float]]:
    """ Filter objects according to the input values or sets 1/3 of the mean
    area as minimum value and 10 times the median as maximun value.
    """
    area_list2 =  copy.deepcopy(area_list)
    if min_size == None:
        min_size = (sum(area_list2)/len(area_list2))/3
    if max_size == None:
        i = round( len(area_list2)/2)
        area_list2.sort()
        median = area_list[i]
        max_size = 10*median
    filtered_contours = [b for a, b in zip(area_list, contours) if  min_size < a < max_size]  
    filtered_in_l = [b for a, b in zip(area_list, in_l) if  min_size < a < max_size] 
    filtered_out_l = [b for a, b in zip(area_list, out_l) if  min_size < a < max_size] 
    
    return filtered_contours, filtered_in_l, filtered_out_l


def radius_and_eccentricity_filter(
        contours: List[np.ndarray], 
        eccentricity: float, 
        min_radius: int, 
        max_radius: int,
        in_l: List[float],
        out_l: List[float]
) -> Tuple[List[np.ndarray], List[float], List[float]]:
    """
    Filters objects according to the given values of eccentricity, min radius 
    and max radius. If none of then is given, the filter is not applied. 
    This function will measure min and max radius af the fitting ellipse of the 
    object and the eccinticity is given by: 
        sqrt((major ellipse axis**2)-(minor ellipse axis** 2))/major ellipse axis'''
    """
    new_cnt_list = []
    new_in_l = []
    new_out_l = []
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
                new_in_l.append(in_l[i])
                new_out_l.append(out_l[i])
        else:
            continue
        
    return new_cnt_list, new_in_l, new_out_l
            
def hull_filter(
        contours: np.ndarray, 
        shape: float,
        in_l: List[float],
        out_l: List[float]
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
    filtered_in_l = [b for a, b in zip(extent_hull, in_l) if a > shape]
    filtered_out_l = [b for a, b in zip(extent_hull, out_l) if a > shape]
    return contours_list, filtered_in_l, filtered_out_l


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
        in_l: List[float],
        out_l: List[float]
) -> Tuple[List[np.ndarray], List[float], List[float]]:
    """
    Given a set of standard and user-defined parameters, it filters the contours 
    that does not match the conditions. Returns the filtered contour list.
    """
    areas = []
    for cnt in contour_list:
        areas.append(cv.contourArea(cnt))
    contours, in_l, out_l = size_filter(contour_list, areas, min_size, max_size, in_l, out_l)

    if len(contours) == 0:
        return  [], [], []
    contours, in_l, out_l = hull_filter(contours, shape,  in_l, out_l)
    
    if len(contours) == 0:
        return [], [], []
    if eccentricity != None or min_radius != None or max_radius !=None:
        contours, in_l, out_l = radius_and_eccentricity_filter(contours, eccentricity, 
                                            min_radius, max_radius, in_l, out_l)
    
    return contours, in_l, out_l
   

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
        fast: bool
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
    if mag >= 10 or fast == False:
        contours, in_l, out_l= fluorescence_of_rings(contours, image, rf, px_s, mag)
    if len(contours)> 0:
        contours, in_l, out_l = filter_contours(contours, mag, px_s, shape, eccentricity, min_size,
                               max_size, min_radius, max_radius, in_l, out_l)
    
    return contours, in_l, out_l


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
