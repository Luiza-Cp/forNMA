# -*- coding: utf-8 -*-
"""
Created on Mon May 17 10:18:45 2021

@author: Luiza
Classe que calcula o NMA devolvendo um dict igual ao das imagens mas sem medidas
de intensidade. Só morfoógicas
"""

import cv2 as cv
import math 
import pandas as pd


class Morphology:
    """
    Stores and measures morphological properties of a object contour.
    """
    def __init__(self, n, cnt):
        """
        Atributes
        
        self.n = number of the cell at a given image
        self.cnt = contour of the object(the nucleus) at image
        self.bbox_x1 = bounding rectangle x coordinate
        self.bbox_y1 = bounding rectangle y coordinate
        self.bbox_w1 = bounding rectangle width
        self.bbox_h1 = bounding rectangle height
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
        self.df = DataFrame with all information
        """
        
        self.n = n
        self.cnt = cnt
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
        self.NII = 0.9*self.aspect- 0.87*self.extent + 0.96*self.radius_ratio + 0.92*self.roundness
        self.df = self.create_df()
        
    def calc_aspect (self) -> float: 
        """Given a fit ellipse, measures the ratio between the major and mino axis."""
        if self.fellipse[1][0] == 0 or  self.fellipse[1][1]==0 :
            print ('zero, usei 1 no lugar ')
            asp =1
   
        elif self.fellipse[1][0] > self.fellipse[1][1]:
            asp = (self.fellipse[1][0])/(self.fellipse[1][1])
        
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
    
    def create_df(self)-> pd.DataFrame:
        """ Generates a DataFrame wth all class information."""
       
        morpho_info = {"Cell": [self.n],
                     "X" : [self.centroid_x],
                     "Y" : [self.centroid_y],
                     "Area": [self.area],
                     "Perimeter": [self.perimeter],
                     "Aspect": [self.aspect],
                     "Extent": [self.extent],
                     "Roundness": [self.roundness],
                     "Radius_ratio": [self.radius_ratio],
                     "NII" : [self.NII],
                       }
        df_morpho = pd.DataFrame(morpho_info) 
        
        return df_morpho