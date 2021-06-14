# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:04:02 2021

@author: Luiza
cell_class_advanced
"""

import cv2 as cv
import math 
import numpy as np
from scipy import signal
from skimage.feature import local_binary_pattern
from skimage.segmentation import clear_border
from foci_class import foci
import pandas as pd
import scipy
from typing import Optional, List, Tuple


#talvez eu não precise a binária -> excluir
class Cell:
    """
    Stores and measures proprieties of a image object, i.e. the nucleus of a 
    cell.
    """
    def __init__(self, n, cnt, rf, mag, ps, image1, binary_image1, image2, 
                 wants_ktr,ring_size, wants_foci, foci_channel_2, 
                 foci_min_size, foci_max_size, foci_min_int, foci_max_int,
                 foci_proeminence, image1_name, image2_name):
        """
        Atributes
        
        self.n = number of the cell at a given image
        self.cnt = contour of the object(the nucleus) at image
        self.rf = resolution factor of a given image
        self.mag = the magnification of a iven image
        self.ps = pixel size ofimage
        self.ring_size = user defined ring size
        self.image1 = image with the nucleus represented by this specific Object
        self.binary_img1 = binary image of image1   
        self.image2= image from second channel
        self.image1_name = str representing the name of the image at channel 1
        self.image2_name = str representing the name of the image at channel 2
        self.wants_foci = boolean user-defined
        self.foci_ch2 = bool. Is true if foci are not in the same channel as the one for nuclear segmentation
        self.foci_min_size = user-input minimun foci size
        self.foci_max_size = user-input maximum foci size
        self.foci_min_int = user-input foci minimum intensity
        self.foci_max_int = user-input foci maximum intensity
        self.foci_proeminence =user-input foci intensity proeminence
        self.bbox_x = bounding rectangle x coordinate
        self.bbox_y = bounding rectangle y coordinate
        self.bbox_w = bounding rectangle width
        self.bbox_h = bounding rectangle height
        self.area = area of self.cnt
        self.fellipse = fitting ellipse of of self.cnt
        self.perimeter =  perimeter of of self.cnt
        self.moments =  moments of self.cnt
        self.aspect = aspect of self.cnt
        self.extent = extent of self.cnt
        self.roundness = roundness of self.cnt
        self.centroid_x = x position of self.cnt centroid
        self.centroid_y = y position of self.cnt  centroid
        self.radius_ratio = radius ratio of self.cnt
        self.NII = Nuclear Irregularity Index of self.cnt
        self.nuc1 = ROI of nucleus at self.image1
        self.bbox_x2 = expanded bounding rectangle x coordinate
        self.bbox_y2 = expanded bounding rectangle y coordinate
        self.bbox_w2 = expanded bounding rectangle width
        self.bbox_h2 = expanded bounding rectangle height
        self.nuc_mask = mask of nucleus created form self.cnt
        sefl.nuc_mask_ex = mask of the nucleus in the expanded bbox
        self.expand_nuc = de dilation of nucleus mask (self.nuc_mask)
        self.min_int1 = minimum intensity of self.image1
        self.max_int1 = maximum intensity of self.image1
        self.mean_int1 = normalized mean intensity of the nucleus (given by self.nuc1)
        self.median_int1 = meadian intensity of the nucleus
        self.nuc2 = ROI of nucleus at self.image2
        self.min_int2 = minimum intensity of self.image2
        self.max_int1 = maximum intensity of self.image2
        self.mean_int2= normalized mean intensity of the nucleus at image2 (given by self.nuc2)
        self.median_int2 = meadian intensity of the nucleus at channel 2
        self.ring_mask = is the mask of cytoplasmatic ring, or None if cytoplasm analysis is not required
        self.ring_cnt = contour of cytoplasmatic ring
        self.ellipse_mask = is the mask of cytoplasmatic ellitpical ring
        self.ellipse_cnt = contour of cytoplasmatic elliptical ring
        self.nuc2_2 = ROI of a the bigger bounding box of nuc2 at image2
        self.ring_mean = mean intensity of the cytoplasmatic ring
        self.ellipse_mean = mean intensity of the cytoplasmatic ellipse
        self.cn_ring = ratio between mean intnsity of cytoplasmatic ring and nucleus
        self.nc_ring = ratio between mean intnsity of nucleus and cytoplasmatic ring 
        self.cn_ellipse = ratio between mean intnsity of cytoplasmatic ellipse and nucleus
        self.nc_ellipse = ratio between mean intnsity of nucleus and cytoplasmatic ellipse 
        self.ellipse_median = median intensity of the cytoplasmatic ellipse
        self.cn_ring_med = ratio between median intnsity of cytoplasmatic ring and nucleus
        self.nc_ring_med = ratio between median intnsity of nucleus and cytoplasmatic ring 
        self.cn_ellipse_med = ratio between median intnsity of cytoplasmatic ellipse and nucleus
        self.nc_ellipse_med = atio between median intnsity of nucleus and cytoplasmatic ellipse
        self.GaussianKernel = contais a gaussian Kernel 
        self.tophat = the tophat transform of the nucleus
        self.lbp = local binary pattens of the nucleus
        self.foci_cnt = Contour of all objects within nucleus (will be filtered after become a foci)
        self.mask_foci = Mask of LBP filtered image
        self.foci_raw_list = list of foci objects generated with self.foci_cnt
         = filtered self.foci_raw_list
        self.foci_n = Number o foci at cell
        self.foci_cnt_im = contors of all foci wit xy positions adjusted for image
        self.tot_foci_area = sum of foci area
        self.tot_foci_mean = mean of all foci together
        
        
        * All mean intensities are normalized by the minimun e maximum image value
        using the formula: (Mean of object - Image Min) / (Image Max - Image Min)
        """    
        
        self.n = n
        self.cnt = cnt
        self.rf = rf
        self.mag = mag
        self.ps = ps
        self.ring_size = ring_size
        self.image1 = image1
        self.binary_img1 = binary_image1    
        self.image2= image2
        self.image1_name = image1_name
        self.image2_name = image2_name
        self.wants_foci = wants_foci
        self.foci_ch2 = foci_channel_2
        self.foci_min_size = foci_min_size
        self.foci_max_size = foci_max_size
        self.foci_min_int = foci_min_int
        self.foci_max_int = foci_max_int
        self.proeminence = foci_proeminence
        self.bbox_x1, self.bbox_y1, self.bbox_w1, self.bbox_h1 = cv.boundingRect(self.cnt)
        self.area = cv.contourArea(cnt) 
        self.fellipse = cv.fitEllipse(cnt)   #fitting ellipse
        self.perimeter=  cv.arcLength(cnt,True)
        self.moments =  cv.moments(cnt)
        self.aspect = self.calc_aspect()
        self.extent = self.calc_extent()
        self.roundness = (self.perimeter **2)/ (4* math.pi * self.area)
        self.centroid_x = int(self.moments['m10']/self.moments['m00'])
        self.centroid_y = int(self.moments['m01']/self.moments['m00'])
        self.radius_ratio = self.calc_radius_ratio()
        self.NII = self.aspect-self.extent + self.radius_ratio + self.roundness
        self.nuc1 = self.image1[self.bbox_y1:self.bbox_y1+self.bbox_h1, 
                              self.bbox_x1:self.bbox_x1+self.bbox_w1]
        self.bbox_x2, self.bbox_y2, self.bbox_w2, self.bbox_h2= self.calc_bbox2()
        self.nuc_mask,self.nuc_mask_ex, self.expand_nuc = self.calc_expand_nuc() 
        self.min_int1,self.max_int1,  __, __  = cv.minMaxLoc(self.image1)        
        self.mean_int1 = (cv.mean(self.nuc1,mask =self.nuc_mask)[0] - self.min_int1)/(self.max_int1- self.min_int1)
        self.median_int1 =  self.calc_median(self.nuc1,self.nuc_mask)
        
        self.nuc2 = None
        self.min_int2 = None 
        self.max_int2 = None
        self.mean_int2= None
        self.median_int2 = None
        self.ring_mask = None
        self.ring_cnt = None
        self.ellipse_mask = None
        self.ellipse_cnt = None
        self.nuc2_2 = None
        self.ring_mean = None
        self.ellipse_mean = None
        self.cn_ring = None
        self.nc_ring = None
        self.cn_ellipse = None
        self.nc_ellipse = None
        self.ring_median = None
        self.ellipse_median = None
        self.cn_ring_med = None
        self.nc_ring_med = None
        self.cn_ellipse_med = None
        self.nc_ellipse_med = None
        self.GaussianKernel = None
        self.tophat = None
        self.lbp = None
        self.foci_cnt = None
        self.mask_foci = None
        self.foci_raw_list = None
        self.foci_list = None
        self.foci_n = None
        self.foci_cnt_im = None
        self.tot_foci_area = None
        self.tot_foci_mean = None
        
        
        
        if not self.image2 is None:
            self.nuc2 = self.image2[self.bbox_y1:self.bbox_y1+self.bbox_h1, 
                         self.bbox_x1:self.bbox_x1+self.bbox_w1]
            self.min_int2, self.max_int2, __, __ = cv.minMaxLoc(self.image2)
            self.mean_int2  = (cv.mean(self.nuc2,mask =self.nuc_mask)[0] - self.min_int2)/(self.max_int2 - self.min_int2)
            self.median_int2 = self.calc_median(self.nuc2,self.nuc_mask)
        
        if wants_ktr == True:
             self.ring_mask, self.ring_cnt = self.find_ring_mask()
             self.ellipse_mask, self.ellipse_cnt = self.find_ring_from_ellipse()
             self.nuc2_2 = self.image2[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                                       self.bbox_x2:self.bbox_x2+self.bbox_w2]
             self.ring_mean =  (cv.mean(self.nuc2_2,mask = self.ring_mask)[0] - self.min_int2)/(self.max_int2- self.min_int2)
             self.ellipse_mean = (cv.mean(self.nuc2_2,mask = self.ellipse_mask)[0] - self.min_int2)/(self.max_int2 - self.min_int2)
             if self.mean_int2 == 0:
                 self.cn_ring = None
                 self.cn_ellipse = None
             else:
                 self.cn_ring = self.ring_mean/self.mean_int2
                 self.cn_ellipse = self.ellipse_mean/self.mean_int2
             if self.ring_mean == 0:
                 self.nc_ring = None
             else:
                 self.nc_ring = self.mean_int2/self.ring_mean
             if self.ellipse_mean == 0:
                self.nc_ellipse = None
             else:
                self.nc_ellipse = self.mean_int2/self.ellipse_mean
                
             
             self.ring_median = self.calc_median(self.nuc2_2, self.ring_mask)
             self.ellipse_median = self.calc_median(self.nuc2_2, self.ellipse_mask)
             self.cn_ring_med = self.ring_median/self.median_int2
             self.nc_ring_med = self.median_int2/self.ring_median
             self.cn_ellipse_med = self.ellipse_median/self.median_int2
             self.nc_ellipse_med = self.median_int2/self.ellipse_median
            
        if wants_foci == True:
            self.GaussianKernel = self.calc_GaussianKernel()
            if self.foci_ch2 == True:
                self.tophat = cv.morphologyEx(self.nuc2, cv.MORPH_TOPHAT, self.GaussianKernel)
            else:
                self.tophat = cv.morphologyEx(self.nuc1, cv.MORPH_TOPHAT, self.GaussianKernel)
            self.lbp = self.calc_lbp()
            #testar o inverso do LBP para nucléolo nas coisas da daph
            self.foci_cnt, self.mask_foci = self.calc_foci_cnt()
            self.foci_raw_list = self.calc_nuc_foci()
            self.foci_list = self.filter_foci()
            self.foci_n = len(self.foci_list)
            self.foci_cnt_im = self.find_cnt_at_image()
            self.tot_foci_area = self.calc_tot_foc_area()
            self.tot_foci_mean = self.calc_foci_mean_int()
        self.df_nucleus = self.create_df() 
     
    def calc_aspect (self) -> float: 
        """Given a fit ellipse, measures the ratio between the major and mino axis."""
        if self.fellipse[1][0] == 0 or  self.fellipse[1][1]==0 :
            print ('zero, usei 1 no lugar ')
            asp =1
            
        elif self.fellipse[1][0] > self.fellipse[1][1]:
            asp = self.fellipse[1][0]/self.fellipse[1][1]
        else:
            asp = (self.fellipse[1][1])/(self.fellipse[1][0])
        
        return asp 
        
    
    def calc_extent(self) -> float:
        """ Measures the extent (object area/object bounding box). """
        bbox_area = self.bbox_w1 * self.bbox_h1
        
        return self.area / bbox_area
    
    
    def calc_radius_ratio(self) -> float:
        """ 
        Finds minor and majo radius of an object in relation to its centroid
        and measures the ratio of each other.
        """
        radius = []
        cx =self.centroid_x
        cy = self.centroid_y
        for i in range(len(self.cnt)):
            a = cx- self.cnt[i,0,0]
            b = cy - self.cnt[i,0,1]
            hipot = math.sqrt(a**2 + b **2)
            radius.append(hipot)
        if min(radius)==0:
            rr = 1
        else:
            rr = max(radius) / min(radius) 
        
        return  rr
        
    
    def calc_bbox2(self) -> int:
        """ Retrieves the coordinates of an expanded bounding box."""
        factor = self.ring_size*3
        x2 = self.bbox_x1 - factor
        y2 = self.bbox_y1 - factor
        w2 = self.bbox_w1 + 2*factor
        h2 = self.bbox_h1 + 2*factor
        if x2 < 0:
            x2 = 0
        if y2 < 0:
            y2=0
        if w2 > self.image1.shape[1]:
            w2 = self.image1.shape[1]
        if h2 > self.image1.shape[0]:
            h2 = self.image1.shape[0]
        
        return x2,y2,w2,h2
  
    
    def calc_expand_nuc(self) -> np.ndarray:
        """
        Draws the contour at an np.zeros array generating a mask for the nucleus 
        and dilates it, generating the expanded mask. Returns both masks.
        """
        kernel = np.ones((3,3), np.uint8)
        blank_image = np.zeros(((self.image1).shape), np.uint8)
        cv.drawContours(blank_image, [self.cnt], -1, (255,255,255), -1)
        nuc_mask= blank_image[self.bbox_y1:self.bbox_y1+self.bbox_h1, 
                              self.bbox_x1:self.bbox_x1+self.bbox_w1]
        nuc_mask_ex= blank_image[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                              self.bbox_x2:self.bbox_x2+self.bbox_w2]
        nuc_expanded_mask = cv.dilate (nuc_mask_ex, kernel, iterations=self.ring_size)
        
        return nuc_mask, nuc_mask_ex, nuc_expanded_mask
    
    
    def find_ring_mask(self) -> np.ndarray:
        """
        Uses the nucleus mask and its dilated mask to create the ring mask, 
        then finds its contourrs and adjusts the xy positions to the image.
        """
        a= cv.bitwise_not(self.nuc_mask_ex)
        b= self.expand_nuc
        ring = cv.bitwise_and(a,b)
        contours,_ = cv.findContours(self.expand_nuc, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
         
        for cnt in contours:
            for pix in cnt:
                pix[0][0] = pix[0][0] + self.bbox_x2 
                pix[0][1] = pix[0][1] + self.bbox_y2 
        
        return ring, contours
    
     
    def find_ring_from_ellipse(self) -> np.ndarray:
        """
        Uses the nucleus mask and a rotated dilated ellipse dilated to find
        the cytoplasmatic ellipitical ring and its contours (already with image
         coordinates)
        """
        el= self.fellipse
        el_height = el[1][0] + self.ring_size
        el_width = el[1][1] + 2*self.ring_size
        el_expanded = (el[0], (el_height, el_width), el[2])
        ellipse_image = np.zeros(((self.image1).shape), np.uint8)
        cv.ellipse(ellipse_image, el_expanded, (255,255,255), -1)
        a= cv.bitwise_not(self.nuc_mask_ex)
        b =  ellipse_image[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                         self.bbox_x2:self.bbox_x2+self.bbox_w2]
        ring = cv.bitwise_and(a,b)
        contours, _ = cv.findContours(ellipse_image, cv.RETR_TREE,  cv.CHAIN_APPROX_NONE)
        
        return ring, contours
    
    
    def calc_median(self, image, mask) -> float:
        """ Given an array and its mask, masks the array and gets its mean intensity."""
        masked_image = np.ma.masked_where(mask==0, image)
        median = np.ma.median(masked_image)
        
        return median
    
    
    def calc_GaussianKernel(self) -> np.ndarray:
        """Returns a 2D Gaussian kernel array, with size and sigma adjusted according to ps."""
        kernlen =round( 1.6/self.ps)
        if (kernlen % 2) == 0:
            kernlen= kernlen+1
        std= kernlen/5 
        GaussianKernel1d = signal.gaussian(kernlen, std=std).reshape(kernlen, 1)
        GaussianKernel2d = np.outer(GaussianKernel1d, GaussianKernel1d)
        
        return GaussianKernel2d
    
    
    def calc_lbp(self) -> np.ndarray:
        """Mweasures the Local Binary Patterns os the nucleus. """
        #não sei se esse raio não tem que ser adaptado de acordo com imagem?
        radius = 5
        n_points = 8 * radius
        METHOD = 'uniform'
        lbp = local_binary_pattern(self.tophat, n_points, radius, METHOD)
        lbp_masked =  np.ma.masked_where(self.nuc_mask==0, lbp)
        
        return lbp_masked
    
    
    def calc_foci_cnt(self):
        """
        Applies morphological Transformations to clean the LBP result, blurs it
        to smooth edges, and then finds its contours and filters the small objects
        according to user inputs or removes small spots.
        Returns a contou list and nucleus image to use in foci object.
        """
        find_dots = self.lbp < 18
        dots = find_dots.astype('uint8')
        if self.mag>20:
            kernel = np.ones((3,3), np.uint8)
            dots = cv.morphologyEx(dots, cv.MORPH_OPEN, kernel, iterations=1)
            dots = cv.morphologyEx(dots, cv.MORPH_CLOSE, kernel, iterations=1)
            dots =  cv.dilate (dots, kernel, iterations=1)
            for i in range(15):
                dots = cv.GaussianBlur(dots,(5,5),1)
        else:
            for i in range(3):
                dots = cv.GaussianBlur(dots,(3,3),1)
        mask = self.nuc_mask
        dots = clear_border(dots)
        dots = dots==0
        dots = np.ma.masked_where(mask==0, dots)
        dots = dots.astype('uint8')
        contours_foci, hierarchy_foci = cv.findContours(dots, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        contours_foci  = [a for a in contours_foci if len(a)>4]
        
        if len(contours_foci) >0:
            areas = []
            for cnt in contours_foci:
                areas.append(cv.contourArea(cnt))
            
            if self.foci_min_size == None:
                min_a = max(areas)/5
            else: 
               min_a = self.foci_min_size
            
            if self.foci_max_size !=  None: 
                contours_foci = [b for a, b in zip(areas, contours_foci) if  min_a < a < self.foci_max_size]
            else:
               contours_foci = [b for a, b in zip(areas, contours_foci) if a > min_a]
              
        return contours_foci, dots
    
    
    def calc_nuc_foci(self) -> List[foci]:
        """ 
        Gets the nucleus image, masks it and use self.foci_cnt to create Foci 
        objcts. Returns a list of Foci or an empty list, if none are found.
        """
        mask = self.nuc_mask
        if self.foci_ch2 == True:
            nuc = self.nuc2
        else:
            nuc = self.nuc1
        nuc_masked = np.ma.masked_where(mask==0, nuc)
        
        foci_list = []
        if len(self.foci_cnt) == 0: 
              foci_list = []           
        else:
            for i in range(len(self.foci_cnt)):
                new_foci = foci(i, self.foci_cnt[i], nuc_masked, self.tophat, self.mask_foci)
                foci_list.append (new_foci)
        foci_list2 = []  
        for foc in foci_list:
            binary = self.binary_img1[self.bbox_y1:self.bbox_y1+self.bbox_h1, 
                               self.bbox_x1:self.bbox_x1+self.bbox_w1]
            int_bin = binary[foc.centroid_y, foc.centroid_x]
            if int_bin>0:       #checks if the objct is inside the nucleus
                foci_list2.append(foc)
                
        return foci_list2
    
    
    def filter_foci(self):
        """
        Filters foci by user defined min and max intensities. Then, it creates
        a new mask to measure the nucleus mean intensity without considering the
        found foci, so it can compare the proeminence of a focus with the 
        background intensity of the nucleus. 
        It returns a filtered foci list.
        """
        if self.foci_min_int == None:
            self.foci_min_int = 0
        if self.foci_max_int == None:
            self.foci_max_int = 255
        if self.proeminence == None:
            self.proeminence = 0
        new_mask = self.nuc_mask.copy()     # used to measure the nuclei intesity without foci
        new_foci_list = []
        for foc in self.foci_raw_list:
            if self.foci_min_int < foc.mean_int < self.foci_max_int:
                new_foci_list.append(foc)
                cv.drawContours(new_mask, [foc.cnt], -1, (0,0,0), -1)
 
        if self.foci_ch2 == True:
            mean_no_foci = (cv.mean(self.nuc2,mask = new_mask)[0] - self.min_int2)/(self.max_int2- self.min_int2)
        else:
            mean_no_foci = (cv.mean(self.nuc1,mask = new_mask)[0] - self.min_int1)/(self.max_int1- self.min_int1)
        
        new_foci_list2 = []
        for foc2 in new_foci_list:
            if mean_no_foci == 0 :
                from matplotlib import pyplot as plt
                plt.imshow(self.nuc)
            if (foc2.mean_int/mean_no_foci) > self.proeminence:
                new_foci_list2.append(foc2)
        
        return new_foci_list2
       
                
    
    def find_cnt_at_image(self) -> np.ndarray:
        """ 
        Adjusts the pixel positions of contours to fit image. Returns the
        adjusted contours.
        """
        cnts = []
        for foc in self.foci_list:
            cnts.append(foc.cnt)
        
        for cnt in cnts:
            for pix in cnt:
                pix[0][0] = pix[0][0] + self.bbox_x1
                pix[0][1] = pix[0][1] + self.bbox_y1
        
        return cnts
    
    
    def calc_tot_foc_area(self) -> float:
        """ Sums up the areal of all foci in the Cell"""
        tot_area= 0
        if len(self.foci_list) > 0:
            for foc in self.foci_list:
                tot_area = tot_area + foc.area  
       
        return tot_area
    
    
    def calc_foci_mean_int(self) -> float:
        """ Returns the mean foci intensity normnalized by image max and min"""
        if self.foci_ch2 == True:
             mean = (cv.mean(self.nuc2,mask =self.mask_foci)[0] - self.min_int2)/(self.max_int2 - self.min_int2)
        else:
            mean =  (cv.mean(self.nuc1, mask =self.mask_foci)[0] - self.min_int2)/(self.max_int1 - self.min_int1)
    
        return mean
    
    
    def create_df(self):
        if self.wants_foci == False:
            foci_area_fraction = None
        else:
            foci_area_fraction =  self.tot_foci_area/self.area,
        cell_info = {"Cell_n": [self.n],
                     "Image_ch1": [self.image1_name],
                     "Ch1_min": [self.min_int1],
                     "Ch1_max": [self.max_int1],
                     "X" : [self.centroid_x],
                     "Y" : [self.centroid_y],
                     "Area": [self.area],
                     "Perimeter": [self.perimeter],
                     "Aspect": [self.aspect],
                     "Extente": [self.extent],
                     "Roundness": [self.roundness],
                     "Radius_ratio": [self.radius_ratio],
                     "NII" : [self.NII],
                     "Mean_ch1": [self.mean_int1],
                     "Median_ch1": [self.median_int1],
                     "Image_ch2": [self.image2_name],
                     "Ch2_min": [self.min_int2],
                     "Ch2_max": [self.max_int2],
                     "Mean_ch2": [self.mean_int2],
                     "Median_ch2": [self.median_int2],
                     "Mean_ring": [self.ring_mean],
                     "Median_ring": self.ring_median,
                     "Mean_ellipse": [self.ellipse_mean],
                     "Median_ellipse": [self.ellipse_median],
                     "Mean_Ring/Nucleus": [self.cn_ring],
                     "Median_Ring/Nucleus": [self.cn_ring_med],
                     "Mean_Nucleus/Ring": [self.nc_ring],
                     "Median_Nucleus/Ring": [self.nc_ring_med],
                     "Mean_Ellipse/Nucleus": [self.cn_ellipse],
                     "Median_Ellipse/Nucleus": [self.cn_ellipse_med],
                     "Mean_Nucleus/Ellipse": [self.nc_ellipse],
                     "Median_Nucleus/Ellipse": [self.nc_ellipse_med],
                     "Total_foci": [self.foci_n],
                     "Total_foci_area": [self.tot_foci_area],
                     "Total_foci_mean": [self.tot_foci_mean],
                     "Foci_area_fraction": [foci_area_fraction[0]],
                     "Nuc_cnt": [self.cnt],
                     "Ring_cnt": [self.ring_cnt],
                     "Ellipse_cnt": [self.ellipse_cnt],
                     "Foci_cnt": [self.foci_cnt_im],
                     "Y_draw": [self.bbox_y1]}
        df_cell = pd.DataFrame(cell_info) 
        
        return df_cell
                     
                     
                     
                     
                     
            
        #cria aqui a linha do df completão
        
    