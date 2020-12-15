# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 10:28:23 2020

@author: Luiza Cherobini
"""
import cv2 as cv
import math 
import numpy as np
import copy
from skimage.feature import local_binary_pattern
from skimage.segmentation import clear_border
from foci_class import foci

class cell:
    def __init__(self, n, cnt, ring_size, rf, image, binary_img, wants_foci, mag):
        self.n = n
        self.rf = rf
        self.mag = mag
        self.cnt = cnt
        self.image = image
        self.binary_img = binary_img
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
        self.nuc, self.mask = self.calc_nuc_mask()
        self.mean_intensity = self.calc_mean_intensity()
        self.bbox2= self.calc_bbox2()
        self.expand_nuc = self.calc_expand_nuc()
        self.ring = self.find_ring()
        self.lbp = None
        self.foci_cnt = None
        self.foci = None
        self.foci_cnt_im = None
        self.foci_list =  None
        self.tot_foci_area = None
        self.tot_foci_mean = None
        if wants_foci == True:
            self.lbp = self.calc_lbp()
            self.foci_cnt, self.mask_foci = self.calc_foci_cnt()
            self.foci = len(self.foci_cnt)
            self.foci_cnt_im = self.find_cnt_at_image()
            self.foci_list = self.calc_nuc_foci()
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
        return max(radius) / min(radius)
        
    def calc_NII(self):
        nii = self.aspect-self.extent + self.radius_ratio + self.roundness
        return nii
    
    def calc_nuc_mask(self):
        nuc = self.image[self.bbox_y:self.bbox_y+self.bbox_h, 
                         self.bbox_x:self.bbox_x+self.bbox_w]
        mask = self.binary_img[self.bbox_y:self.bbox_y+self.bbox_h, 
                               self.bbox_x:self.bbox_x+self.bbox_w]
        return (nuc, mask)
    
    def calc_mean_intensity(self): 
        mean_I= cv.mean(self.nuc,mask =self.mask)
        return mean_I[0]
    
    def calc_bbox2(self):
        factor = self.ring_size*2
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
        return (x2,y2,w2,h2)
        
    def calc_expand_nuc(self):
        '''returns the integer mask (np.array) of the expanded nuc'''
        x2 = self.bbox2[0] 
        y2 = self.bbox2[1] 
        w2 = self.bbox2[2] 
        h2 = self.bbox2[3] 
        kernel = np.ones((3,3), np.uint8)
        nuc2 = self.binary_img[y2:y2+h2, x2:x2+w2]
        #nuc2 = clear_border(nuc2)
        nuc_mask = nuc2
        nuc_expanded = cv.dilate (nuc2, kernel, iterations=round(14*self.rf))
        nuc_expanded_mask = nuc_expanded
        return nuc_mask, nuc_expanded_mask
        
    def find_ring(self):
        '''returns the ring mask (int) and de mean intensity of it'''
        a= cv.bitwise_not(self.expand_nuc[0])
        b= self.expand_nuc[1]
        ring = cv.bitwise_and(a,b)
        return ring
        
    def calc_lbp(self):
        '''no lbp esse radius depende do n pixels e magnificação
        devolve uma msk com lbp'''
        nuc = self.nuc
        mask = self.mask
        radius = 3
        n_points = 8 * radius
        METHOD = 'uniform'
        lbp = local_binary_pattern(nuc, n_points, radius, METHOD)
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
        for i in range(6):
            dots = cv.GaussianBlur(dots_binary,(3,3),2)
        
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
        return (contours_foci, dots)
    
    def find_cnt_at_image(self):
        cnts = copy.deepcopy(self.foci_cnt)
        for cnt in cnts:
            for pix in cnt:
                pix[0][0] = pix[0][0] + self.bbox_x
                pix[0][1] = pix[0][1] + self.bbox_y
        return cnts
     

    def calc_nuc_foci(self):
        mask = self.mask
        nuc = self.nuc
        nuc_masked = np.ma.masked_where(mask==254, nuc)
        foci_list = []
        if len(self.foci_cnt) == 0: 
              foci_list = []           
        else:
            for i in range(len(self.foci_cnt)):
                new_foci = foci( i, self.foci_cnt[i], nuc_masked, self.mask_foci)
                foci_list.append (new_foci)           
        return foci_list
    
    def calc_tot_foc_area(self):
        tot_area= 0
        if len(self.foci_list) > 0:
            for foci in self.foci_list:
                tot_area = tot_area + foci.area  
        return tot_area
    
    def calc_foci_mean_int(self):
       mean =  cv.mean(self.nuc,mask =self.mask_foci)
       return mean[0]