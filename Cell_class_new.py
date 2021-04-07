# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 16:20:21 2021

@author: Luiza
 novo cell class 
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

class Cell:
    def __init__(self, n, cnt, ring_size, rf, image, binary_img, wants_foci, wants_ktr,
                 mag, pixel_size, foci_other_channel, image2):

        self.n = n
        self.rf = rf
        self.mag = mag
        self.ps = pixel_size
        self.cnt = cnt
        self.image = image
        self.image2= image2
        self.binary_img = binary_img
        self.foci_other_channel = foci_other_channel
        self.bbox_x, self.bbox_y, self.bbox_w, self.bbox_h = cv.boundingRect(self.cnt)
        self.ring_size = ring_size
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
        self.NII = self.calc_NII()
        self.nuc = self.image[self.bbox_y:self.bbox_y+self.bbox_h, 
                              self.bbox_x:self.bbox_x+self.bbox_w]
        #mudar para image_mask o self.mask
        self.mask = self.binary_img[self.bbox_y:self.bbox_y+self.bbox_h, 
                                         self.bbox_x:self.bbox_x+self.bbox_w]
        self.mean_intensity = cv.mean(self.nuc,mask =self.mask)[0]
        self.bbox_x2, self.bbox_y2, self.bbox_w2, self.bbox_h2= self.calc_bbox2() #bigger box
        self.nuc_mask, self.expand_nuc = self.calc_expand_nuc()
        self.ring = self.find_ring()
        self.ring_contour = self.find_ring_contour()
        self.ring_ellipse, self.cnt_ring_ellipse = self.find_ring_from_ellipse()
        self.nuc1_expanded = self.image[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                                             self.bbox_x2:self.bbox_x2+self.bbox_w2]
        self.ring_mean_img1 =  cv.mean(self.nuc1_expanded,mask = self.ring)[0]
        self.nuc2 = None
        self.min_nuc2 = None 
        self.max_nuc2 = None
        self.mean_intensity2 = None
        self.image2_min = None
        self.image2_max = None
        self.nuc2_expanded = None
        self.ring_mean = None
        self.ellipse_mean = None
        self.cn_ring = None
        self.cn_ring_norm= None
        self.nc_ring = None
        self.nc_ring_norm = None
        self.cn_ellipse = None
        self.cn_el_norm = None
        self.nc_ellipse = None
        self.nc_el_norm = None
        self.GaussianKernel = None
        self.tophat =  None
        self.lbp = None
        self.foci_cnt = None
        self.mask_foci = None
        self.foci = None
        self.foci_cnt_im = None
        self.foci_list =  None
        self.tot_foci_area = None
        self.tot_foci_mean = None
        
        if not self.image2 is None:
            self.nuc2 = self.image2[self.bbox_y:self.bbox_y+self.bbox_h, 
                         self.bbox_x:self.bbox_x+self.bbox_w]
            self.min_nuc2, self.max_nuc2, __, __ = cv.minMaxLoc(self.nuc2, mask = self.mask)
            self.mean_intensity2  = cv.mean(self.nuc2,mask = self.mask)[0]
            from matplotlib import pyplot as plt
            plt.figure()
            plt.imshow(self.nuc2)
            plt.imshow(self.mask)
            self.image2_min, self.image2_max, __, __ = cv.minMaxLoc(self.image2)#min max from all img
        if wants_ktr == True:
            #bbox2 ao redor do nuc2
            self.nuc2_expanded = self.image2[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                                             self.bbox_x2:self.bbox_x2+self.bbox_w2]
            self.ring_mean =  cv.mean(self.nuc2_expanded,mask = self.ring)[0]
            self.ellipse_mean = cv.mean(self.nuc2_expanded,mask = self.ring_ellipse)[0]
            self.cn_ring = self.ring_mean/self.mean_intensity2
            self.nc_ring= self.mean_intensity2/self.ring_mean
            self.cn_ellipse = self.ellipse_mean/self.mean_intensity2
            self.nc_ellipse = self.mean_intensity2/self.ellipse_mean
            self.cn_ring_norm, self.nc_ring_norm,self.cn_el_norm, self.nc_el_norm = self.calc_normalized()
           
        if wants_foci == True:
            self.GaussianKernel = self.calc_GaussianKernel()
            if self.foci_other_channel == True:
                self.tophat= cv.morphologyEx(self.nuc2, cv.MORPH_TOPHAT, self.GaussianKernel)
            else:
                self.tophat= cv.morphologyEx(self.nuc, cv.MORPH_TOPHAT, self.GaussianKernel)
            self.lbp = self.calc_lbp()
            self.foci_cnt, self.mask_foci = self.calc_foci_cnt()
            self.foci_list = self.calc_nuc_foci()
            self.foci = len(self.foci_list)
            self.foci_cnt_im = self.find_cnt_at_image()
            self.tot_foci_area = self.calc_tot_foc_area()
            self.tot_foci_mean = self.calc_foci_mean_int()
         
    
   
    
    def calc_aspect (self): #raio maior / raio menor da elipse
        if self.fellipse[1][0] > self.fellipse[1][1]:
            asp = self.fellipse[1][0]/self.fellipse[1][1]
        else:
            asp = (self.fellipse[1][1])/(self.fellipse[1][0])
        return asp 
        
    def calc_extent(self): #Object area/ bounding rectangle
        bbox_area = self.bbox_w * self.bbox_h
        return self.area / bbox_area
    
    def calc_radius_ratio(self):
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
        
    def calc_NII(self):
        nii = self.aspect-self.extent + self.radius_ratio + self.roundness
        return nii
    
    def calc_bbox2(self):
        factor = self.ring_size*3
        x2 = self.bbox_x - factor
        y2 = self.bbox_y - factor
        w2 = self.bbox_w + 2*factor
        h2 = self.bbox_h + 2*factor
        if x2 < 0:
            x2 = 0
        if y2 < 0:
            y2=0
        if w2 > self.image.shape[1]:
            w2 = self.image.shape[1]
        if h2 > self.image.shape[0]:
            h2 = self.image.shape[0]
        return x2,y2,w2,h2
    
    def calc_expand_nuc(self):
        '''returns the integer mask (np.array) of the expanded nuc'''
        kernel = np.ones((3,3), np.uint8)
        blank_image = np.zeros(((self.image).shape), np.uint8)
        cv.drawContours(blank_image, [self.cnt], -1, (255,255,255), -1)
        nuc_mask= blank_image[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                              self.bbox_x2:self.bbox_x2+self.bbox_w2]
        nuc_expanded_mask = cv.dilate (nuc_mask, kernel, iterations=self.ring_size)
        return nuc_mask, nuc_expanded_mask
    
    def find_ring(self):
        '''returns the ring mask (int)'''
        a= cv.bitwise_not(self.nuc_mask)
        b= self.expand_nuc
        ring = cv.bitwise_and(a,b)
        return ring
 
    def find_ring_contour(self):
         contours,_ = cv.findContours(self.expand_nuc[1], cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
         
         for cnt in contours:
            for pix in cnt:
                pix[0][0] = pix[0][0] + self.bbox_x2 
                pix[0][1] = pix[0][1] + self.bbox_y2      
         return contours
     
    def find_ring_from_ellipse(self):
        el= self.fellipse
        el_height = el[1][0]+ self.ring_size
        el_width = el[1][1]+2*self.ring_size
        el_expanded = (el[0], (el_height, el_width), el[2])
        ellipse_image = np.zeros(((self.image).shape), np.uint8)
        cv.ellipse(ellipse_image, el_expanded, (255,255,255), -1)
        a= cv.bitwise_not(self.nuc_mask)
        b =  ellipse_image[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                         self.bbox_x2:self.bbox_x2+self.bbox_w2]
        ring = cv.bitwise_and(a,b)
        contours, _ = cv.findContours(ellipse_image, cv.RETR_TREE,  cv.CHAIN_APPROX_NONE)
        return ring, contours
    

    
    def calc_normalized(self):
        '''measures the normalized values for the ratios nucleus /cytoplsm
        according to the formula (mean - image_min)/(image_max - image_min)'''
        nuc = (self.mean_intensity2- self.image2_min)/(self.image2_max - self.image2_min)
        ring = (self.ring_mean - self.image2_min)/(self.image2_max - self.image2_min)
        ellipse = (self.ellipse_mean - self.image2_min)/(self.image2_max - self.image2_min)
        cn_ring = ring/nuc
        nc_ring = nuc/ring
        cn_el = ellipse/nuc
        nc_el = nuc/ellipse
        return cn_ring, nc_ring, cn_el, nc_el
    
    def calc_GaussianKernel(self):
        """Returns a 2D Gaussian kernel array."""
        kernlen =round( 1.6/self.ps)
        if (kernlen % 2) == 0:
            kernlen= kernlen+1
        std= kernlen/5 
        GaussianKernel1d = signal.gaussian(kernlen, std=std).reshape(kernlen, 1)
        GaussianKernel2d = np.outer(GaussianKernel1d, GaussianKernel1d)
        return GaussianKernel2d
    
    def calc_lbp(self):
        '''no lbp esse radius depende do n pixels e magnificação
        devolve uma msk com lbp'''
        mask = self.mask
        radius = 5
        n_points = 8 * radius
        METHOD = 'uniform'
        lbp = local_binary_pattern(self.tophat, n_points, radius, METHOD)
        lbp_masked =  np.ma.masked_where(mask==0, lbp)
                
        return lbp_masked
        
    def calc_foci_cnt(self):
        '''devolve a lista de cnt e a self.imagem dos dots para usar no objeto foci'''
        find_dots = self.lbp < 18
        dots_binary = find_dots.astype('uint8')
        kernel = np.ones((3,3), np.uint8)
        dots = cv.morphologyEx(dots_binary, cv.MORPH_OPEN, kernel, iterations=1)
        dots = cv.morphologyEx(dots, cv.MORPH_CLOSE, kernel, iterations=1)
        dots =  cv.dilate (dots, kernel, iterations=1)
        for i in range(15):
            dots = cv.GaussianBlur(dots,(5,5),1)
        mask = self.mask
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
            min_a = max(areas)/5
            contours_foci = [b for a, b in zip(areas, contours_foci) if a > min_a]  
        return contours_foci, dots
    
    
    def calc_nuc_foci(self):
        mask = self.mask
        if self.foci_other_channel == True:
            nuc = self.nuc2
        else:
            nuc = self.nuc
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
            binary = self.binary_img[self.bbox_y:self.bbox_y+self.bbox_h, 
                               self.bbox_x:self.bbox_x+self.bbox_w]
            int_bin = binary[foc.centroid_y, foc.centroid_x]
            
            if int_bin>0: #and foc.area>(265*self.ps):
                foci_list2.append(foc)
        return foci_list2
    
    def find_cnt_at_image(self):
        cnts = []
        for foc in self.foci_list:
            cnts.append(foc.cnt)
        
        for cnt in cnts:
            for pix in cnt:
                pix[0][0] = pix[0][0] + self.bbox_x
                pix[0][1] = pix[0][1] + self.bbox_y
        return cnts
    
    def calc_tot_foc_area(self):
        tot_area= 0
        if len(self.foci_list) > 0:
            for foc in self.foci_list:
                tot_area = tot_area + foc.area  
        return tot_area
    
    def calc_foci_mean_int(self):
        if self.foci_other_channel == True:
             mean =  cv.mean(self.nuc2,mask =self.mask_foci)
        else:
            mean =  cv.mean(self.nuc,mask =self.mask_foci)
        return mean[0]
    
    def df_foci_ints(self): #talvez não preciso mais disso
    
        mean_no_foci =  cv.mean(self.nuc,mask = cv.bitwise_not(self.mask_foci))[0]
        col_list = [ 'nuc', 'dot', 'nuc_mean', 'nuc_mean_no_dot', 'area', 'perimeter', 'mean_int',
                    'mean_int_th', "cent_int", 'cent_int_th', 'bright', 'bright_th', 'mean_cnt',
                    'mean_cnt_th', 'ext', 'ext4', 'ext_th', 'extr4_th', 'kurtosis', 'kurtosis_th',
                    'laplacian_var', 'laplacian_var_th', 'sec_deriv', 'sec_deriv_th', 'inertia',
                    'bright_cnt_ratio', 't-value', 'p-value']
        df = pd.DataFrame(columns = col_list) 
        
        masked_nuc = np.ma.masked_where(self.mask == 0, self.nuc )
        
        pixel_list = []
        for column in masked_nuc:
            for px in column:
                pixel_list.append(px)
        pixel_list = np.array(pixel_list)
        pixel_list = pixel_list[~np.isnan(pixel_list)]
        
                           
        for foc in self.foci_list:
          
            t, p =  scipy.stats.ttest_ind(pixel_list, foc.px_list, equal_var=False, nan_policy='omit')
            new_line = [self.n, foc.n, self.mean_intensity, mean_no_foci, foc.area,
                        foc.perimeter, foc.mean_int, foc.mean_int_th, foc.cent_int,
                        foc.cent_int_tophat, foc.bright, foc.bright_th, foc.mean_cnt,
                        foc.mean_cnt_tophat, foc.ext, foc.ext4, foc.ext_th, foc.ext4_th,
                        foc.kurtosis, foc.kurtosis_th, foc.lv, foc.lv_th, foc.sec_deriv,
                        foc.sec_deriv_th, foc.inertia, foc.bright_cnt_ratio, t, p]
            df.loc[len(df)] = new_line        
        return df