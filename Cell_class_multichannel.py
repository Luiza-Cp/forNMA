# -*- coding: utf-8 -*-
"""
Created on Mon May 17 09:19:03 2021

@author: Luiza

Cell mas sem um segundo canal (analisa tudo no p´roprio canal de acordo com os 
                               parâmetros passados no dict)
Sem as partes do cálculo de NMA 
"""

import cv2 as cv
import numpy as np
from scipy import signal
from skimage.feature import local_binary_pattern
from skimage.segmentation import clear_border
from foci_class import Foci
import pandas as pd
from typing import List


#talvez eu não precise a binária -> excluir
class Cell:
    """
    Stores and measures proprieties of a image object, i.e. the nucleus of a 
    cell.
    """
    def __init__(self, n, cnt, mag, ps, image, image_name, ch_name,
                 wants_ktr, ring_size,  wants_foci, foci_min_size, foci_max_size,
                 foci_min_int,foci_max_int,foci_proeminence, use_el):
        """
        Atributes
        
        self.n = number of the cell at a given image
        self.cnt = contour of the object(the nucleus) at image
        self.rf = resolution factor of a given image
        self.mag = the magnification of a iven image
        self.ps = pixel size ofimage
        self.ring_size = user defined ring size in pixels
        self.image = image with the nucleus represented by this specific Object
        self.image_name = str representing the name of the image at this channel
        self.wants_ktr = boolean user-defined  #A: esse KTR é aquela medida do aro no citoplasma
        self.use_el = boolean defined by user to choose between a ring or ellipse for translocation measurments
        
        self.wants_foci = boolean user-defined
        self.foci_min_size = user-input minimun foci size
        self.foci_max_size = user-input maximum foci size
        self.foci_min_int = user-input foci minimum intensity
        self.foci_max_int = user-input foci maximum intensity
        self.foci_proeminence = user-input foci intensity proeminence
        
        self.area = area inside the contour (in pixels)
        sefl.fellipse = fitting ellipse of the contour
        self.bbox_x1 = bounding rectangle x coordinate
        self.bbox_y1 = bounding rectangle y coordinate
        self.bbox_w1 = bounding rectangle width
        self.bbox_h1 = bounding rectangle height
        self.nuc = ROI of nucleus at self.image1
        self.bbox_x2 = expanded bounding rectangle x coordinate
        self.bbox_y2 = expanded bounding rectangle y coordinate
        self.bbox_w2 = expanded bounding rectangle width
        self.bbox_h2 = expanded bounding rectangle height
        self.nuc2 = ROI of nucleus at self.image1 using the expanded bounding box
        
        self.nuc_mask = mask of nucleus created form self.cnt
        sefl.nuc_mask_ex = mask of the nucleus in the expanded bbox
        self.expand_nuc = de dilation of nucleus mask (self.nuc_mask)
        
        self.min_int = minimum intensity of self.image1
        self.max_int = maximum intensity of self.image1
        self.image_mean = mean intensity of self.image1
        self.mean_int = normalized mean intensity of the nucleus (given by self.nuc1)
        self.median_int = meadian intensity of the nucleus
        self.error_mean = nucleus mean divided by image mean
        
        self.ring_mask = is the mask of cytoplasmatic ring, or None if cytoplasm analysis is not required
        self.ring_cnt = contour of cytoplasmatic ring
        self.ellipse_mask = is the mask of cytoplasmatic ellitpical ring
        self.ellipse_cnt = contour of cytoplasmatic elliptical ring
        self.ring_mean = mean intensity of the cytoplasmatic ring
        self.ellipse_mean = mean intensity of the cytoplasmatic ellipse
        self.cn_ring = ratio between mean intnsity of cytoplasmatic ring and nucleus
        self.nc_ring = ratio between mean intnsity of nucleus and cytoplasmatic ring 
        self.cn_ellipse = ratio between mean intnsity of cytoplasmatic ellipse and nucleus
        self.nc_ellipse = ratio between mean intnsity of nucleus and cytoplasmatic ellipse 
        
        self.ring_median = Nonemedian intensity of the cytoplasmatic ring
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
        self.foci_list= filtered self.foci_raw_list
        self.foci_n = Number o foci at cell
        self.foci_cnt_im = contors of all foci wit xy positions adjusted for image
        self.tot_foci_area = sum of foci area
        self.tot_foci_mean = mean of all foci together
        self.df_all_foci = dataframe of cell foci 
        
        self.df = dataframe with all main information of this cell
        
        
        * All mean intensities are normalized by the minimun e maximum image value
        using the formula: (Mean of object - Image Min) / (Image Max - Image Min)
        """    
        
        
        self.n = n
        self.cnt = cnt
        self.rf = image.size/4194304
        self.mag = mag
        self.ps = ps
        self.ring_size = round(ring_size)
        self.image = image
        self.image_name = image_name
        self.ch_name = ch_name
        self.wants_ktr = wants_ktr
        self.use_el = use_el
     
        self.wants_foci = wants_foci
        self.foci_min_size = foci_min_size
        self.foci_max_size = foci_max_size
        self.foci_min_int = foci_min_int
        self.foci_max_int = foci_max_int
        self.proeminence = foci_proeminence

        self.area = cv.contourArea(cnt) 
        self.fellipse = cv.fitEllipse(cnt)   #fitting ellipse
        self.bbox_x1, self.bbox_y1, self.bbox_w1, self.bbox_h1 = cv.boundingRect(self.cnt)
        self.nuc = self.image[self.bbox_y1:self.bbox_y1+self.bbox_h1, 
                              self.bbox_x1:self.bbox_x1+self.bbox_w1]
        self.bbox_x2, self.bbox_y2, self.bbox_w2, self.bbox_h2= self.calc_bbox2()
        self.nuc2 = self.image[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                              self.bbox_x2:self.bbox_x2+self.bbox_w2]
        self.nuc_mask,self.nuc_mask_ex, self.expand_nuc = self.calc_expand_nuc()
        
        self.min_int,self.max_int,  __, __  = cv.minMaxLoc(self.image)
        self.image_mean = cv.mean(self.image)[0]
        self.mean_int = (cv.mean(self.nuc,mask =self.nuc_mask)[0] - self.min_int)/(self.max_int-self.min_int)
        self.median_int =  self.calc_median(self.nuc,self.nuc_mask)
    
        
        #add 1 caso para não dar float division by 0
        self.ring_mask = None
        self.ring_cnt = None
        self.ellipse_mask = None
        self.ellipse_cnt = None
        self.ring_mean = None
        self.ellipse_mean = None
        self.cn_ring = None
        self.nc_ring = None
        self.cn_ellipse = None
        self.nc_ellipse = None
        self.cyto_ring_cnt = None
       
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
        self.df_all_foci = None
        
        
        if wants_ktr == True:
             self.ring_mask, self.ring_cnt = self.find_ring_mask()
             self.ellipse_mask, self.ellipse_cnt = self.find_ring_from_ellipse()
             self.ring_mean =  (cv.mean(self.nuc2, mask = self.ring_mask)[0] - self.min_int)/(self.max_int- self.min_int)
             self.ellipse_mean = (cv.mean(self.nuc2, mask = self.ellipse_mask)[0] - self.min_int)/(self.max_int - self.min_int)
             self.cyto_ring_cnt = self.ellipse_cnt if self.use_el==True else self.ring_cnt 
             if self.mean_int == 0:
                 self.cn_ring = None
                 self.cn_ellipse = None
             else:
                 self.cn_ring = self.ring_mean/self.mean_int
                 self.cn_ellipse = self.ellipse_mean/self.mean_int
             if self.ring_mean == 0:
                 self.nc_ring = None
             else:
                 self.nc_ring = self.mean_int/self.ring_mean
             if self.ellipse_mean == 0:
                self.nc_ellipse = None
             else:
                self.nc_ellipse = self.mean_int/self.ellipse_mean
                
             #conferir mean e median  da ellipse e ring 
      
             self.ring_median = self.calc_median(self.nuc2, self.ring_mask)
             self.ellipse_median = self.calc_median(self.nuc2, self.ellipse_mask)
             self.cn_ring_med = self.ring_median/self.median_int
             self.nc_ring_med = self.median_int/self.ring_median
             self.cn_ellipse_med = self.ellipse_median/self.median_int
             self.nc_ellipse_med = self.median_int/self.ellipse_median
             
             
        if wants_foci == True:
            self.GaussianKernel = self.calc_GaussianKernel()
            self.tophat = cv.morphologyEx(self.nuc, cv.MORPH_TOPHAT, self.GaussianKernel)
            self.lbp = self.calc_lbp()
            #testar o inverso do LBP para nucléolo nas coisas da daph
            self.foci_cnt, self.mask_foci = self.calc_foci_cnt()
            self.foci_raw_list = self.calc_nuc_foci()
            self.foci_list = self.filter_foci()
            self.foci_n = len(self.foci_list)
            self.foci_cnt_im = self.find_cnt_at_image()
            self.tot_foci_area = self.calc_tot_foc_area()
            self.tot_foci_mean = self.calc_foci_mean_int()
            self.df_all_foci = self.get_foci_dfs()
           
        self.df = self.create_df() 
       
        
    
    def calc_bbox2(self) -> int:
        """ Retrieves the coordinates of an expanded bounding box."""
        factor = self.ring_size*3
        x2 = round(self.bbox_x1 - factor)
        y2 = round(self.bbox_y1 - factor)
        w2 = round(self.bbox_w1 + 2*factor)
        h2 = round(self.bbox_h1 + 2*factor)
        if x2 < 0:
            x2 = 0
        if y2 < 0:
            y2=0
        if w2 > self.image.shape[1]:
            w2 = self.image.shape[1]
        if h2 > self.image.shape[0]:
            h2 = self.image.shape[0]
        
        return x2,y2,w2,h2
  
    
    def calc_expand_nuc(self) -> np.ndarray:
        """
        Draws the contour at an np.zeros array generating a mask for the nucleus 
        and dilates it, generating the expanded mask. Returns both masks.
        """
        kernel = np.ones((3,3), np.uint8)
        blank_image = np.zeros(((self.image).shape), np.uint8)
        cv.drawContours(blank_image, [self.cnt], -1, (255,255,255), -1)
        nuc_mask= blank_image[self.bbox_y1:self.bbox_y1+self.bbox_h1, 
                              self.bbox_x1:self.bbox_x1+self.bbox_w1]
        nuc_mask_ex= blank_image[self.bbox_y2:self.bbox_y2+self.bbox_h2, 
                              self.bbox_x2:self.bbox_x2+self.bbox_w2]
        nuc_diletade_mask_ex = cv.dilate (nuc_mask_ex, kernel, iterations= self.ring_size)
      
        return nuc_mask, nuc_mask_ex, nuc_diletade_mask_ex
    
    
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
        ellipse_image = np.zeros(((self.image).shape), np.uint8)
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
    
    
    def calc_nuc_foci(self) -> List[Foci]:
        """ 
        Gets the nucleus image, masks it and use self.foci_cnt to create Foci 
        objcts. Returns a list of Foci or an empty list, if none are found.
        """
        mask = self.nuc_mask
        nuc = self.nuc
        nuc_masked = np.ma.masked_where(mask==0, nuc)
        
        foci_list = []
        if len(self.foci_cnt) == 0: 
              foci_list = []           
        else:
            for i in range(len(self.foci_cnt)):
                new_foci = Foci(i, self.foci_cnt[i], nuc_masked, self.tophat, 
                                self.mask_foci, self.min_int, self.max_int)
                foci_list.append (new_foci)
        foci_list2 = []  
        for foc in foci_list:
            binary = self.nuc_mask
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
 
        
        mean_no_foci = (cv.mean(self.nuc,mask = new_mask)[0] -self.min_int)/(self.max_int-self.min_int)
        
        new_foci_list2 = []
        for foc2 in new_foci_list:
            if (foc2.mean_int/(mean_no_foci)) > self.proeminence:
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
        if len(self.foci_list)== 0:
            mean = 0
        else:
            blank_mask = np.zeros(((self.nuc).shape), np.uint8)
            for i in range(len(self.foci_list)):
                blank_mask = cv.drawContours(blank_mask, self.foci_list[i].cnt, -1, (255,255,255), -1)
            mean =  (cv.mean(self.nuc, mask =blank_mask)[0] - self.min_int)/(self.max_int -self.min_int + 1)
    
        return mean
    
                      
    def get_foci_dfs(self):
        if len(self.foci_list) ==0:
            df = None
        else:
            foci_dfs = [f.df for f in self.foci_list] 
            df = pd.concat(foci_dfs)
            df.insert(0, "Origin_nucleus", self.n)
            df.insert(0, "Image_name", self.image_name)
            df.insert(0, "Channel", self.ch_name)

        return df
        
    
    def create_df(self):
        if self.wants_foci == False:
            foci_area_fraction = None
        else:
            foci_area_fraction = (self.tot_foci_area/self.area)
        cell_info = {"Cell" : [self.n],
                     "Image_" + self.ch_name: [self.image],
                     "Image_name_" + self.ch_name: [self.image_name],
                     "Min_image_" + self.ch_name: [self.min_int],
                     "Max_image_" + self.ch_name: [self.max_int],
                     "Mean_" + self.ch_name: [self.mean_int],
                     "Median_" + self.ch_name: [self.median_int],
                     "Mean_ring_" + self.ch_name: [self.ring_mean],
                     "Median_ring_" + self.ch_name: self.ring_median,
                     "Mean_ellipse_" + self.ch_name: [self.ellipse_mean],
                     "Median_ellipse_" + self.ch_name: [self.ellipse_median],
                     "Mean_Ring/Nucleus_" + self.ch_name: [self.cn_ring],
                     "Median_Ring/Nucleus_" + self.ch_name: [self.cn_ring_med],
                     "Mean_Nucleus/Ring_" + self.ch_name: [self.nc_ring],
                     "Median_Nucleus/Ring_" + self.ch_name: [self.nc_ring_med],
                     "Mean_Ellipse/Nucleus_" + self.ch_name: [self.cn_ellipse],
                     "Median_Ellipse/Nucleus_" + self.ch_name: [self.cn_ellipse_med],
                     "Mean_Nucleus/Ellipse_" + self.ch_name: [self.nc_ellipse],
                     "Median_Nucleus/Ellipse_" + self.ch_name : [self.nc_ellipse_med],
                     "Total_foci_" + self.ch_name: [self.foci_n],
                     "Total_foci_area_" + self.ch_name: [self.tot_foci_area],
                     "Total_foci_mean_" + self.ch_name: [self.tot_foci_mean],
                     "Foci_area_fraction_" + self.ch_name: [foci_area_fraction],
                     "Nuc_cnt_" + self.ch_name: [self.cnt],
                     "Cyto_ring_cnt_" + self.ch_name: [self.cyto_ring_cnt],
                     "Foci_cnt_" + self.ch_name: [self.foci_cnt_im],
                     "Y_draw_" + self.ch_name: [self.bbox_y1],
                     "foci_df_"+ self.ch_name: [self.df_all_foci]
                     }
        df_cell = pd.DataFrame(cell_info) 
        
        return df_cell
                     
   
                     
                     
            
        #cria aqui a linha do df completão
        
    