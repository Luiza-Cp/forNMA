# -*- coding: utf-8 -*-
"""
Created on Sat Mar 13 21:12:53 2021

@author: Luiza

This class performs watershed segmentation and/or forces a division of a cell in 
two according to user input
"""
import cv2 as cv
import numpy as np
from skimage import color, img_as_ubyte
import math

def select_right_contour(contour_list, hierarchy):
     """ It uses hierarchy from cv.findContours to get the most external contour. """
     cnt_adjusted = [] 
     for i in range(len(contour_list)):
         if hierarchy[0,i,2] == -1:
             cnt_adjusted.append(np.array(contour_list[i]))
     return cnt_adjusted

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


class Segmenting:
       

    
    def __init__(self, contour, image, resolution_factor, pixel_size,
                 extent, x, y, w, h, cut_edges): 
        
        self.raw_contour = contour
        self.img = image
        self.rf = resolution_factor
        self.ps = pixel_size
        self.adjusted_contours = [] 
        self.extent = extent
        self.x = x
        self.y = y
        self.w = w
        self.h =h
        self.cut_edges = cut_edges
        self.x2, self.y2, self.w2, self.h2 = self.find_bigger_bbox()
        self.roi_img, self.roi_binary = self.find_roi_bigger_bbox()
        self.bg, self.fg, self.unknown = self. find_bg_fg_unk()
        self.markers = self.find_markers()
        self.ws_contour = self.watershed() # aqui tem a lista dos contornos 
        self.cut_contour = self.force_cut()
        self.true_contour = self.select_contour()
        
  
    def find_bigger_bbox(self):
        x2 = self.x - round(60 *self.rf)
        y2 = self.y - round(60 * self.rf)
        w2 = self.w + round(120 * self.rf)
        h2 = self.h + round(120 * self.rf)
        if x2 < 0:
            x2 = 0
        if y2 < 0:
            y2=0
        if w2 > self.img.shape[1]:
            w2 = self.img.shape[1]
        if h2 > self.img.shape[0]:
           h2 = self.img.shape[0]   
        return x2,y2,w2,h2
    
    def find_roi_bigger_bbox(self):
        roi_image = self.img[self.y2:self.y2+self.h2, self.x2:self.x2+self.w2]
        roi_image = img_as_ubyte(roi_image)
        blank_image= np.zeros((self.img.shape), dtype = "uint8")
        cv.drawContours(blank_image, [self.raw_contour], -1, (255,255,255), -1)
        roi_binary_image = blank_image[self.y2:self.y2+self.h2, self.x2:self.x2+self.w2]
        return roi_image, roi_binary_image
    
    def find_bg_fg_unk(self):
        kernel = np.ones((3,3), np.uint8) 
        sure_bg = cv.dilate(self.roi_binary, kernel, iterations=round(17*self.rf))
        dist_transform = cv.distanceTransform(self.roi_binary,cv.DIST_L2,3)
        if self.extent > 0.88:
            n = 0.75
        else: 
            n=0.5
        ret, sure_fg = cv.threshold(dist_transform,n*dist_transform.max(),255, 0) #usuário??
        sure_fg= np.uint8(sure_fg) 
        unknown= cv.subtract(sure_bg, sure_fg)
        return sure_bg, sure_fg, unknown

    def find_markers(self):
      ret_a, markers = cv.connectedComponents(self.fg)
      markers = markers+1 
      markers[self.unknown==255] = 0 
      img =cv.cvtColor(self.roi_img,cv.COLOR_GRAY2BGR)
      markers =cv.watershed(img, markers)
      img[markers == -1] = [255, 0, 0]
      img = color.label2rgb(markers, bg_label=0)
      markers = markers.astype(np.uint8)
      return markers    
 
    def smooth_edges(self, contours):   
        new_contours= []
        kernel = np.ones((3,3), np.uint8)
        ks= round(33*self.rf)
        if ks % 2 == 0:
            ks = ks+1
        for cnt in contours:
           blank_image= np.zeros((self.roi_img.shape), dtype = "uint8")
           cv.drawContours(blank_image, [cnt], -1, (255,255,255), -1)
           for i in range(round(self.rf*30)):
                blured_img = cv.GaussianBlur(blank_image, (ks, ks), 2)
           blured_img = cv.medianBlur(blank_image,round(ks/2)+1)
           blured_img =  cv.dilate (blured_img, kernel, iterations=round(3*self.rf))
           contour, hierarchy = cv.findContours(blured_img, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
           if len(contour) == 0:
               continue
           else:    
               contour = select_right_contour(contour, hierarchy)
               new_contours.append(contour)
        return new_contours   
 
    def watershed(self):
        ret, image2 = cv.threshold(self.markers, 0, 255, cv.THRESH_BINARY|cv.THRESH_OTSU)
        contours, hierarchy = cv.findContours(image2, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        right_contours = select_right_contour(contours, hierarchy)
        smoothed_contours = self.smooth_edges(right_contours)
        new_contour = []
        for cnt in smoothed_contours:
            if isinstance(cnt, np.ndarray):
                new_contour.append(cnt)
            else:
                new_contour.append(cnt[0])
        return new_contour

    def section_nuc(self, coordinate_list, radius, binary_image,x , y):
        if len(coordinate_list) == 2:
            dist = math.sqrt((coordinate_list[0][0]-coordinate_list[1][0])**2 + 
                         (coordinate_list[0][1]-coordinate_list[1][1])**2)
            if radius[0]*self.cut_edges > dist:
                a = (coordinate_list[0][0]- x, coordinate_list[0][1]-y)
                b = (coordinate_list[1][0]- x, coordinate_list[1][1]-y)
                cv.line(binary_image,a, b,[0,0,0], 2)   #round(2 * self.rf))    
        if len(coordinate_list)>2:
           new_line, dist2 = find_smallest_distance(coordinate_list)
           if radius[0]*self.cut_edges > dist2:
               a = (new_line[0][0]- x, new_line[0][1]-y)
               b =  (new_line[1][0]- x, new_line[1][1]-y)
               cv.line(binary_image, a,b ,[0,0,0],2)     
        return binary_image    

    
    def hull_defects(self, contour, binary, x, y):
        hull = cv.convexHull(contour,returnPoints=False)
        hull[::-1].sort(axis=0)
        defects = cv.convexityDefects(contour, hull)
        if np.all(defects) != None:
            coordinate_far_list = main_defects(defects, contour) 
            if len(coordinate_far_list) == 0:
                return [contour]
            else:
                pos, radius, degree = cv.fitEllipse(contour)
                binary_image = self.section_nuc(coordinate_far_list,radius, binary,x, y) 
                new_contours, hierarchy =  cv.findContours(binary_image, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
                return new_contours
        else:
              return [contour]
    
    def force_cut(self):
        cnt_hull = []
        if len(self.ws_contour) ==1:
            contour_hull = self.hull_defects(self.raw_contour, self.roi_binary, self.x2, self.y2)
            cnt_hull = contour_hull
        else:
            for contour in self.ws_contour:
                blank_image = np.zeros((self.roi_img.shape), dtype = "uint8")
                binary = cv.drawContours(blank_image, [contour], -1, (255,255,255), -1)
                contour_hull = self.hull_defects(contour, binary,0 ,0)
                for cnt in contour_hull:
                    cnt_hull.append(cnt)
        return cnt_hull

    def adjust_contour_for_image(self, contour_list):
        adjusted_contour =[]
        for contour in contour_list:
            for pix in contour:
                pix[0][0] = pix[0][0] + self.x2
                pix[0][1] = pix[0][1] + self.y2
            adjusted_contour.append(contour)  
        return adjusted_contour
   
    def select_contour(self):
        if len(self.cut_contour) > len(self.ws_contour):
            true = self.adjust_contour_for_image(self.cut_contour)
        elif len(self.ws_contour) > 1:
            true = self.adjust_contour_for_image(self.ws_contour)
        else:
            true = [self.raw_contour]
        return true