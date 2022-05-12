# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 11:09:28 2020

@author: Luiza Cherobini
"""
import cv2 as cv
import numpy as np
from scipy.stats import kurtosis
from skimage.measure import profile_line
import pandas as pd


class Foci:
    """ Stores and measures proprieties of cell foci """
    
    
    def __init__(self, n, cnt, orig_nuc, orig_nuc_tophat, mask_foci, min_int, max_int):
        """
        Atributes
        
        self.n: foci number (int)
        self.cnt: opencv contour. Is the foci contour
        self.orig_nuc: image representing the nucleus that contains this focus
        self.orig_nuc_tophat: is teh orig_nuc in a tophat transfrom
        self.mask_foci: the mask corresponding to this specific focus
        self.min_int: minimum image intensity 
        self.max_int: maximum image intensity 
        self.area: focus area
        self.perimeter: focus perimeter
        self.bx: x cordinate of focus bounding box
        self.by: y cordinate of focus bounding box
        self.bw: width of focus bounding box
        self.bh: height of focus bounding box
        self.mean_int: focus mean intensity
        self.mean_int_th: focus mean intensity at tophat transformed image
        self.moments: focus inertia moments
        self.centroid_x: focus centroid x coordinate
        self.centroid_y: focus centroid y coordinate
        self.cent_int: intensity of the pixel at focus centroid 
        self.cent_int_tophat =intensity of the pixel at focus centroid at tophat transformed image
        self.img: image of focus
        self.masked: masked image of focus
        self.df: dataframe containing all focus relevant informations
        
        """
              
        self.n = n
        self.cnt = cnt
        self.orig_nuc = orig_nuc
        self.orig_nuc_tophat = orig_nuc_tophat
        self.mask_foci = mask_foci
        self.min_int = min_int
        self.max_int =max_int
        self.area = cv.contourArea(self.cnt)
        self.perimeter = cv.arcLength(self.cnt,True)
        self.bx, self.by, self.bw, self.bh = cv.boundingRect(self.cnt)
        self.mean_int, self.mean_int_th= self.calc_intensity()
        self.moments =  cv.moments(self.cnt)
        self.centroid_x = int(self.moments['m10']/self.moments['m00'])
        self.centroid_y = int(self.moments['m01']/self.moments['m00'])
        self.cent_int = ((self.orig_nuc[self.centroid_y, self.centroid_x])- self.min_int)/(self.max_int- self.min_int)
        self.cent_int_tophat = ((self.orig_nuc_tophat[self.centroid_y, self.centroid_x]) - self.min_int)/(self.max_int- self.min_int)
        self.img, self.masked = self.find_img()
        self.df = self.calc_df()
    
    def calc_intensity(self):
        "Measures foci mean intensity at iamge and at tophat transformed"
        mask = self.mask_foci[self.by:self.by+self.bh, 
                              self.bx:self.bx+self.bw]
        mask = cv.bitwise_not(mask)
        nuc = self.orig_nuc[self.by:self.by+self.bh, 
                            self.bx:self.bx+self.bw]
        nuc_th = self.orig_nuc_tophat[self.by:self.by+self.bh, 
                            self.bx:self.bx+self.bw]
        mask = mask.astype('uint8')
        mean = (cv.mean(nuc, mask= mask)[0] -self.min_int)/(self.max_int- self.min_int)
        mean_th = (cv.mean(nuc_th, mask= mask)[0] - self.min_int)/(self.max_int- self.min_int)
       
        return mean, mean_th
     
    
    def find_img(self):
        """ Segments focus image boundng box and the masked focus image """
        img = np.ma.masked_where(self.mask_foci==255, self.orig_nuc, copy=True)
        img = img[self.by:self.by+self.bh, self.bx:self.bx+self.bw]
        img2 = np.ma.masked_where(self.mask_foci==255, self.orig_nuc_tophat, copy=True)
        img2 = img2[self.by:self.by+self.bh, self.bx:self.bx+self.bw]
        
        return img, img2
    
    
    def calc_df(self):
        """creates the focus dadtaframe"""
        foci_info = {"Focus_number" : [self.n],
                     "Focus_mean_intensity": [self.mean_int],
                     "Focus_Area": [self.area],
                     "Focus_perimeter": [self.perimeter],
                     "Focus_centroid_x":  [self.centroid_x],
                     "Focus_centroid_y" : [self.centroid_y]}
        df_foci = pd.DataFrame(foci_info) 
        
        return df_foci
   