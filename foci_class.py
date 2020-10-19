# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 11:09:28 2020

@author: Luiza Cherobini
"""
import cv2 as cv


class foci:
    def __init__(self, n, cnt, orig_nuc, mask_foci):
        self.n = n
        self.cnt = cnt
        self.orig_nuc = orig_nuc
        self.mask_foci = mask_foci
        self.area = cv.contourArea(self.cnt)
        self.bx, self.by, self.bw, self.bh = cv.boundingRect(self.cnt)
        self.mean_int = self.calc_intensity()

    def calc_intensity(self):
        mask = self.mask_foci[self.by:self.by+self.bh, 
                              self.bx:self.bx+self.bw]
        nuc = self.orig_nuc[self.by:self.by+self.bh, 
                            self.bx:self.bx+self.bw]
    
        mask = mask.astype('uint8')
        mean = cv.mean(nuc, mask= mask)
        return mean[0]