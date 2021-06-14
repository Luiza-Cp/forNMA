# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 11:09:28 2020

@author: Luiza Cherobini
"""
import cv2 as cv
import numpy as np
from scipy.stats import kurtosis
from skimage.measure import profile_line


# A: essa classe ta toda meio perdida, vou mexer nela com mais calma quando der  husahsuah
# vou deixar pra comentar els quando estiver pronta, aí tu mexe nela depois



class foci:
    def __init__(self, n, cnt, orig_nuc, orig_nuc_tophat, mask_foci):
        
        #Quando refizer essa, preciso normalizar as intensidades, pq o valor de 
        #intensidade do foci ta dando super alto e distoane do resto
        self.n = n
        self.cnt = cnt
        self.orig_nuc = orig_nuc
        self.orig_nuc_tophat = orig_nuc_tophat
        self.mask_foci = mask_foci
        self.area = cv.contourArea(self.cnt)
        self.perimeter = cv.arcLength(self.cnt,True)
        self.bx, self.by, self.bw, self.bh = cv.boundingRect(self.cnt)
        self.mean_int, self.mean_int_th= self.calc_intensity()
        self.moments =  cv.moments(self.cnt)
        self.centroid_x = int(self.moments['m10']/self.moments['m00'])
        self.centroid_y = int(self.moments['m01']/self.moments['m00'])
        self.cent_int = (self.orig_nuc[self.centroid_y, self.centroid_x])
        self.cent_int_tophat = (self.orig_nuc_tophat[self.centroid_y, self.centroid_x])
        self.img, self.bright, self.bright_th, self.px_list, self.px_list_th = self.find_mean_bright_px()
        self.mean_cnt, self.mean_cnt_tophat = self.find_mean_contour_points()
        #self.ext, self.ext4, self.ext_th, self.ext4_th = self.calc_mean_exrtreme_points()
        #self.kurtosis = kurtosis((self.px_list)**2)
        #self.kurtosis_th = kurtosis(self.px_list_th)
        #self.lv, self.lv_th= self.laplacian_var()
        #self.sec_deriv, self.sec_deriv_th = self.second_derivative()
        #self.inertia = self.find_inertia_moment()[0]
        #self.bright_cnt_ratio = self.bright/self.mean_cnt
        
#se o cnt ta com as coordenadas do núcleo, o que eu acabei de fazer n se aplica 
    def calc_intensity(self):
        mask = self.mask_foci[self.by:self.by+self.bh, 
                              self.bx:self.bx+self.bw]
        mask = cv.bitwise_not(mask)
        nuc = self.orig_nuc[self.by:self.by+self.bh, 
                            self.bx:self.bx+self.bw]
        nuc_th = self.orig_nuc_tophat[self.by:self.by+self.bh, 
                            self.bx:self.bx+self.bw]
        mask = mask.astype('uint8')
        mean = cv.mean(nuc, mask= mask)
        mean_th = cv.mean(nuc_th, mask= mask)
        return mean[0], mean_th[0]
               
    def calc_mean_exrtreme_points(self):
        left = tuple(self.cnt[self.cnt[:,:,0].argmin()])[0]
        right = tuple(self.cnt[self.cnt[:,:,0].argmax()])[0]
        top = tuple(self.cnt[self.cnt[:,:,1].argmin()])[0]
        bottom = tuple(self.cnt[self.cnt[:,:,1].argmax()])[0]
        n = self.orig_nuc
        nt = self.orig_nuc_tophat
        
        arr_mean = np.array([(n[left[1], left[0]]), (n[right[1], right[0]]),  
                (n[top[1], top[0]]), (n[bottom[1],bottom[0]])])
        arr_mean = arr_mean[~np.isnan(arr_mean)]
        arr_mean_tophat =np.array([(nt[left[1], left[0]]), (nt[right[1], right[0]]),  
                (nt[top[1], top[0]]), (nt[bottom[1],bottom[0]])])
        arr_mean_tophat = arr_mean_tophat[~np.isnan(arr_mean_tophat)]
       
        if (left[0]-3) < 0:
            out_l = (left[1], 0)
        else: 
            out_l = (left[1], left[0]-3)
        if (right[0]+3) > self.bw:
            out_r = (right[1], self.bw)
        else:
            out_r = (right[1], right[0]+3)
        if (top[1]-3) < 0:
            out_t = (0,top[0])
        else:
            out_t = (top[1]-3, top[0])
        if (bottom[0]+3) > self.bh:
            out_b =(self.bh,bottom[0])
        else: 
            out_b = (bottom[1]+3,bottom[0])
         
        arr_mean_out = np.array([(n[out_l]), (n[out_r]), (n[out_t]), (n[out_b])])
        arr_mean_out = arr_mean_out[~np.isnan(arr_mean_out)]
        arr_mean_out_tophat = np.array([(nt[out_l]), (nt[out_r]), (nt[out_t]), (nt[out_b])])
        arr_mean_out_tophat = arr_mean_out_tophat[~np.isnan(arr_mean_out_tophat)]
         
        if len(arr_mean) == 0:
            mean = None
            mean_tophat = None 
        if len(arr_mean) == 1:
            mean = arr_mean[0]
            mean_tophat = arr_mean_tophat[0]   
        else: 
            mean = arr_mean.mean()
            mean_tophat = arr_mean_tophat.mean()
          

        if len(arr_mean_out) == 0:
            mean_out = None
            mean_out_tophat = None
        if len(arr_mean_out) == 1:
            mean_out = arr_mean_out[0]
            mean_out_tophat = arr_mean_out_tophat[0]       
        else: 
            mean_out = arr_mean_out.mean()
            mean_out_tophat = arr_mean_out_tophat.mean()
            
        if mean == 0:
            mean = 0.25
        if mean_out ==0:
            mean_out = 0.25
        if mean_tophat == 0:
            mean_tophat = 0.25
        if mean_out_tophat == 0:
            mean_out_tophat = 0.25
            
        return mean, mean_out, mean_tophat, mean_out_tophat
     
    
    def find_mean_bright_px(self):
        img = np.ma.masked_where(self.mask_foci==255, self.orig_nuc, copy=True)
        img = img[self.by:self.by+self.bh, self.bx:self.bx+self.bw]
        img2 = np.ma.masked_where(self.mask_foci==255, self.orig_nuc_tophat, copy=True)
        img2 = img2[self.by:self.by+self.bh, self.bx:self.bx+self.bw]
        
        pixel_list = []
        for column in img:
            for px in column:
                pixel_list.append(px)
        pixel_list = np.array(pixel_list)
        pixel_list = pixel_list[~np.isnan(pixel_list)]
        pixel_list = np.sort(pixel_list)
        pixel_list = pixel_list[::-1]
        pixel_list2 = pixel_list[0:3]
        mean = pixel_list2.mean()
        
        pixel_list_tophat = [] 
        for column in img2:
            for px in column:
                pixel_list_tophat.append(px)
        pixel_list_tophat = np.array(pixel_list_tophat)
        pixel_list_tophat = pixel_list_tophat[~np.isnan(pixel_list_tophat)]
        pixel_list_tophat = np.sort(pixel_list_tophat)
        pixel_list_tophat = pixel_list_tophat[::-1]
        pixel_list_tophat = pixel_list_tophat[0:3]
        mean_tophat = pixel_list_tophat.mean()
        
        return img, mean, mean_tophat, pixel_list, pixel_list_tophat
    
    def find_mean_contour_points(self):
        pixel_coord_list = []
        
        for pixel in self.cnt:
           pixel_coord_list.append(pixel[0])
           
        pixel_list = []
        pixel_tophat_list =[]
        for px in pixel_coord_list:
            pixel_list.append(self.orig_nuc[px[1], px[0]])
            pixel_tophat_list.append(self.orig_nuc_tophat[px[1], px[0]])
        pixel_list = np.array(pixel_list)
        pixel_tophat_list = np.array(pixel_tophat_list)
        mean = pixel_list.mean()
        mean_tophat = pixel_tophat_list.mean()
        return mean, mean_tophat
        
    def laplacian_var(self):
        img_th = np.ma.masked_where(self.mask_foci==255, self.orig_nuc_tophat, copy=True)
        img = np.ma.masked_where(self.mask_foci==255, self.orig_nuc, copy=True)
        img_th = img_th[self.by:self.by+self.bh, self.bx:self.bx+self.bw]
        img = img[self.by:self.by+self.bh, self.bx:self.bx+self.bw]
        lv_th = cv.Laplacian(img_th, cv.CV_64F).var()
        lv = cv.Laplacian(img, cv.CV_64F).var()
        return lv, lv_th
    
    def second_derivative(self):
        img = np.ma.masked_where(self.mask_foci==255, self.orig_nuc, copy=True) 
        xc = self.bx+ round(self.bw/2)
        yc =  self.by+ round(self.bh/2)
        center = (xc, yc)
        lineup = profile_line(img, center, (xc, self.by))
        linedown = profile_line(img, center, (xc, self.by+self.bh))
        lineleft = profile_line(img, center, (self.bx, yc))
        lineright = profile_line(img, center, (self.bx+self.bw, yc))
        derivup = (np.diff(lineup**2, n=2)).var()
        derivdown = (np.diff(linedown**2, n=2)).var()
        derivleft= (np.diff(lineleft**2, n=2)).var() #tentar com 2 no line né troxa
        derivright = (np.diff(lineright**2, n=2)).var()
        sumder = derivup+derivdown+derivleft+derivright
        if sumder != 0:
            mean = sumder/4
        else:
            mean = 0.1
            
            
        img_th = np.ma.masked_where(self.mask_foci==255, self.orig_nuc_tophat, copy=True) 
        xc = self.bx+ round(self.bw/2)
        yc =  self.by+ round(self.bh/2)
        center = (xc, yc)
        lineup_th = profile_line(img_th, center, (xc, self.by))
        linedown_th = profile_line(img_th, center, (xc, self.by+self.bh))
        lineleft_th = profile_line(img_th, center, (self.bx, yc))
        lineright_th = profile_line(img_th, center, (self.bx+self.bw, yc))
        derivup_th = (np.diff(lineup_th**2, n=2)).var()
        derivdown_th = (np.diff(linedown_th**2, n=2)).var()
        derivleft_th= (np.diff(lineleft_th**2, n=2)).var() #tentar com 2 no line né troxa
        derivright_th = (np.diff(lineright_th**2, n=2)).var()
        sumder_th = derivup_th+derivdown_th+derivleft_th+derivright_th
        if sumder_th != 0:
            mean_th = sumder_th/4
        else:
            mean_th = 0.1
        return mean, mean_th
    
    def find_inertia_moment(self):
        huMoments = cv.HuMoments(self.moments)
        inertia = huMoments[0]
        return inertia

