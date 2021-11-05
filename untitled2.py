#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 03:44:07 2021

@author: luiza
#tracking
"""
from LapTracker.LapTracker import *
import numpy as np
import pandas as pd
import os
import math
import random



def track(path_to_table: str,
          max_distance: int = 30,
          time_window: int = 5,
          max_split_distance: int = 20,
          max_gap_closing_distance: int = 10
)-> pd.DataFrame :
    """ Write here"""
    
    table = pd.read_csv(path_to_table)
    table.columns
    for i in table.columns:
        if 'Image_name' in i:
            name = i 
            break
             
    cols = ['X', "Y", 'Frame', name]
    df2 = table[cols]
    df2['X'] = pd.to_numeric(df2['X'], downcast='integer')
    df2['Y']  =pd.to_numeric(df2['Y'], downcast='integer')
    df2['Frame']  =pd.to_numeric(df2['Frame'], downcast='integer')
    tracker = LapTracker(max_distance=max_distance, time_window=time_window,
                         max_split_distance=max_split_distance,
                         max_gap_closing_distance=max_gap_closing_distance)
    tracker.track_df(df2, identifiers=cols)
    tracked_df = tracker.df
    return tracked_df
    

tracked_df = track('/home/luiza/Área de Trabalho/registradas/análise/greenResults.csv' )

unique = tracked_df['unique_id']
table = table.join(unique) 


import cv2 as cv
from skimage import  img_as_ubyte, exposure
im_names = table['Image_name_red'].to_list()
im_names = set(im_names)

def load(im):
    img = cv.imread(im, cv.IMREAD_ANYDEPTH)
    #img = exposure.rescale_intensity(img, in_range='image', out_range='dtype')
    #img = img_as_ubyte(img)
    img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
    return img

path = '/home/luiza/Área de Trabalho/registradas/análise/green/red'
images = [load(os.path.join(path,f)) for f in im_names]
im_df = pd.DataFrame()
im_df['images'] = images
im_df['Name'] = list(im_names)


distances = []
for track in tracker.tracks:
    x_list = []
    y_list = []
    image_list = []
    d = 0
    for u_id in track:
        x = table.loc[table['unique_id'] == u_id, 'X'].iloc[0]
        y = table.loc[table['unique_id'] == u_id, 'Y'].iloc[0]
        image = table.loc[table['unique_id'] == u_id, 'Image_name_red'].iloc[0]
        x_list.append(x)
        y_list.append(y)
        image_list.append(image)
     
         
    for i in range(len(x_list)-1):
        dis = math.sqrt(((x_list[i+1]-x_list[i])**2)+ ((y_list[i+1]-y_list[i])**2))
        d=d + dis
        
    
    r = random.randint(0,255)
    b = random.randint(0,255)
    g = random.randint(0,255)
    color = (b, g, r)   
    line_list = []
    for i in range(len(image_list)):
       img_draw = im_df.loc[im_df['Name'] == image_list[i], 'images'].iloc[0]
       cv.circle(img_draw, (x_list[i], y_list[i]), 3, color, -1) 
       if i > 0:
           line_list.append(((x_list[i-1], y_list[i-1]),(x_list[i], y_list[i])))
           for j in line_list:
               cv.line(img_draw, j[0], j[1] , color, 2) 
           
       
       im_df.loc[im_df['Name'] == image_list[i], 'images'].iloc[0] = img_draw
       
    
    distances.append(d)
from matplotlib import pyplot as plt
plt.imshow(im_df.loc[42][0])



fig, ax = plt.subplots()
sns.lineplot(data=ee, x= 'Frame', y='segment_id', ci=None, ax= ax)
sns.lineplot(data=bb, x= 'Frame', y='segment_id', ci=None, ax= ax)
