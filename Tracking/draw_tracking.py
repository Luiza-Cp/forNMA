#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 00:02:51 2022

@author: luiza
"""
import cv2 as cv
import numpy as np
import os
import pandas as pd
import random
from skimage.exposure import rescale_intensity


def find_colors(df: pd.DataFrame) -> dict:
    """ 
    Generates a random color for each family. Returns a dictionary where 
    key = family, value = RGB color
    """
    family_color_dict = {}
    for family in list(set(df['family_id'])):
        color = (random.randint(0, 170), random.randint(0,170), random.randint(0,170))
        family_color_dict[family] =  color
        
    return family_color_dict


def read_image(path: str,
               rescale_int: bool = False
) -> np.ndarray:
    """ Given a image path, loads the image and rescales its intensity if needed """
    img = cv.imread(path, cv.IMREAD_COLOR) 
    if rescale_int == True:
        img = rescale_intensity(img, in_range='image', out_range='dtype')
    
    return img


def draw_tracking(path_to_tracked_df: str,
                  images_folder: str,
                  path_to_save: str,
                  rescale_int: bool = False
)-> None:

    df = pd.read_csv(path_to_tracked_df)
    image_names = sorted(os.listdir(images_folder)) 
    frames = sorted(list(set(df['Frame'].values)))
    frames = [int(f) for f in frames]
    
    if len(frames) != len(image_names):
        raise Exception('The number of frames at the tablemust be equal to the number of images')
        
    family_color_dict = find_colors(df)
    
    for i in range(len(frames)):  
        img = read_image(os.path.join(images_folder,image_names[i]))
        circle_radius = 5 if img.shape[0]*img.shape[1] < 4000000 else 10
        linewidth = 2 if img.shape[0]*img.shape[1] < 4000000 else 5
                  
        for family in list(set(df['family_id'])): # iterate over each family
            color = family_color_dict[family]
            df_frames = df[(df['family_id'] == family) & (df['Frame'] <= frames[i])] # nessa familia
            ids =  sorted(list(set(df_frames['Cell_id'])), key=len)
            
            for j in range(len(ids)): # iterate over cell_id 
                color2 = (color[0] + len(ids[j])*15, color[1] + len(ids[j])*15, color[2]+ len(ids[j])*15)
                df_id = df_frames.loc[df_frames['Cell_id'] == ids[j]]
                x = [int(f) for f in list(df_id['X'])]
                y = [int(f) for f in list(df_id['Y'])]   
                
                if j == 0:
                    cv.circle(img, (int(x[0]), int(y[0])), circle_radius, color2, cv.FILLED)
                else:
                    df_parent = df_frames.loc[df_frames['Cell_id'] == ids[j][:-2]]
                    max_parent_frame = df_parent['Frame'].max()
                    x0 = df_parent.loc[df_parent['Frame'] == max_parent_frame, 'X'].iloc[0]
                    x.insert(0, int(x0))
                    y0 = df_parent.loc[df_parent['Frame'] == max_parent_frame, 'Y'].iloc[0]
                    y.insert(0, int(y0))
                    
                    
                for n in range(len(x)-1): 
                    cv.line(img, (list(zip(x,y))[n]), (list(zip(x,y))[n+1]), color2, linewidth)

       
        cv.imwrite(os.path.join(path_to_save, image_names[i]), img)
    return None
       

draw_tracking('/media/luiza/DATA/Doutorado/53bp1 py some info/FAQ fornma/tracking test/Results md=250 t=7 ms=25 mg=100.csv',
              '/media/luiza/DATA/Doutorado/Teste tracking/2  arvores/imagens',
              '/media/luiza/DATA/Doutorado/53bp1 py some info/FAQ fornma/tracking test/Results md=250 t=7 ms=25 mg=100',
                  )
                 