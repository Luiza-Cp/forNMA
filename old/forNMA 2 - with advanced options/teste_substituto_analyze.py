# -*- coding: utf-8 -*-
"""
Created on Sun Apr 25 02:37:39 2021

@author: Luiza
"""

import numpy as np
import pandas as pd 
from initializing_functions_advanced2 import run_image 
import cv2 as cv
import os
from typing import List, Optional
from preview import load_image

def get_file_list (folder1: str,
                    path_save: str,
                    save_images: bool = True,
                    folder2: Optional[str] = None,                   
) -> List[str]: 
    
    
    ch1_files =  sorted([os.path.join(folder1, f) for f in os.listdir(folder1)
                         if not f.startswith('.')])
    foldername1 = str(os.path.basename(folder1))
    ch1_save = os.path.join(path_save, foldername1 + " Contours")
    if save_images == True:
        os.mkdir(ch1_save)
    
    if folder2 != None:
        ch2_files =  sorted([os.path.join(folder2, f) for f in os.listdir(folder2) 
                             if not f.startswith('.')])
        foldername2 = str(os.path.basename(folder2))
        ch2_save = os.path.join(path_save, foldername2 + " Contours")
        if save_images == True:
             os.mkdir(ch2_save)
    else:
        ch2_files = None
        
    return ch1_files, ch2_files, foldername1, foldername2, ch1_save, ch2_save




# arrumar cunção pra quando a pessoa quiser só medir média do nuc na imagem 2, sem 
#ktr ou foci. Ela tem que ver se tem canal 2 e se sim medir ele
def split_dfs(
        df: pd.DataFrame,
        wants_foci: bool = False,
        foci_ch2: bool = False,
        wants_ktr: bool = False
) -> pd.DataFrame:
    
    df_cnt = df.groupby('Frame')[['Cell_n','X','Y_draw','Path_ch1','Path_ch2','Nuc_cnt',
                        "Ellipse_cnt","Ring_cnt", "Foci_cnt"]].agg(list).reset_index()
    
    if wants_foci and wants_ktr == True:
        col_list = ["Cell_n", "Frame", "Image_ch1", "Ch1_min", "Ch1_max", "X", "Y", "Area",
                    "Perimeter", "Aspect", "Extente", "Roundness", "Radius_ratio",
                     "NII", "Mean_ch1", "Median_ch1", "Image_ch2", "Ch2_min",
                     "Ch2_max",  "Mean_ch2", "Median_ch2", "Mean_ring", "Median_ring",
                     "Mean_ellipse", "Median_ellipse", "Mean_Ring/Nucleus",
                     "Median_Ring/Nucleus", "Mean_Nucleus/Ring", "Median_Nucleus/Ring",
                     "Mean_Ellipse/Nucleus", "Median_Ellipse/Nucleus", "Mean_Nucleus/Ellipse",
                     "Median_Nucleus/Ellipse", "Total_foci",  "Total_foci_area",
                     "Total_foci_mean", "Foci_area_fraction"]
       
    elif wants_foci == True and wants_ktr == False:
        if foci_ch2 == True:
            col_list = ["Cell_n", "Frame", "Image_ch1", "Ch1_min", "Ch1_max", "X", "Y", "Area",
                    "Perimeter", "Aspect", "Extente", "Roundness", "Radius_ratio",
                     "NII", "Mean_ch1", "Median_ch1", "Image_ch2", "Ch2_min",
                     "Ch2_max",  "Mean_ch2", "Median_ch2", "Total_foci",  
                     "Total_foci_area", "Total_foci_mean", "Foci_area_fraction"]
        else:
            col_list = ["Cell_n", "Frame", "Image_ch1", "Ch1_min", "Ch1_max", "X", "Y", "Area",
                    "Perimeter", "Aspect", "Extente", "Roundness", "Radius_ratio",
                     "NII", "Mean_ch1", "Median_ch1", "Total_foci",  
                     "Total_foci_area", "Total_foci_mean", "Foci_area_fraction"]
    
    elif wants_foci == False and wants_ktr == True:
        col_list = ["Cell_n", "Frame", "Image_ch1", "Ch1_min", "Ch1_max", "X", "Y", "Area",
                    "Perimeter", "Aspect", "Extente", "Roundness", "Radius_ratio",
                     "NII", "Mean_ch1", "Median_ch1", "Image_ch2", "Ch2_min",
                     "Ch2_max",  "Mean_ch2", "Median_ch2", "Mean_ring", "Median_ring",
                     "Mean_ellipse", "Median_ellipse", "Mean_Ring/Nucleus",
                     "Median_Ring/Nucleus", "Mean_Nucleus/Ring", "Median_Nucleus/Ring",
                     "Mean_Ellipse/Nucleus", "Median_Ellipse/Nucleus", "Mean_Nucleus/Ellipse",
                     "Median_Nucleus/Ellipse"]

    
    df_save = df[col_list] 
    
    return df_save, df_cnt


#ref ch1 não deve ser ocional, mudar isso   
def analyze(
        files_ch1: List[str],
        magnification: int, 
        pixel_size: Optional[float] = 0.5, 
        ref_ch1: Optional[np.array] = None,
        ref_ch2: Optional[np.array] = None,
        threshold: Optional[str] = 'triangle', 
        offset: Optional[int] = 0, 
        blur: Optional[int] = 12, 
        adjust_size: Optional[int] = 0, 
        cut_edges: Optional[float] = 0.7, 
        shape: Optional[float] = 0.88, 
        eccentricity: Optional[float] = None, 
        min_size: Optional[int] = None, 
        max_size: Optional[int] = None, 
        min_radius: Optional[int] = None, 
        max_radius: Optional[int] = None, 
        fast_detection: bool = False,
        rescale_intensity: bool = False, 
        remove_bg: bool = False,
        radius: int = 30,
        error: Optional[int] = None, 
        wants_ktr: bool = False, 
        ring_size: Optional[float] = 1.75, #talvez pedir valor em pixel
        use_ellipse: bool = False, 
        wants_foci: bool = False, 
        foci_channel2: bool = False, 
        foci_min_size: Optional[int] = None, 
        foci_max_size: Optional[int] = None, 
        foci_min_int: Optional[int] = None, 
        foci_max_int: Optional[int] = None,
        foci_proeminence: Optional[int] = None,
        files_ch2: Optional[List[str]] = None
) -> pd.DataFrame:
    
   
    
   df_total =  pd.DataFrame() 
   for i in range(len(files_ch1)):
       image1_name = str(os.path.basename(files_ch1[i]))
       image1 = load_image(files_ch1[i], rescale_intensity, remove_bg, 
                           radius, ref_ch1)
       if  files_ch2 != None:
           image2_name = str(os.path.basename(files_ch2[i]))
           image2 = load_image(files_ch2[i], rescale_intensity,remove_bg, 
                               radius, ref_ch2)
       else:
           image2_name = None
        
       cell_list = run_image(image1, image1_name, magnification, image2, 
                             image2_name, pixel_size, 
                             threshold, offset, blur, adjust_size, cut_edges,
                             shape, eccentricity, min_size, max_size,min_radius,
                             max_radius,fast_detection, error, wants_ktr, 
                             ring_size, use_ellipse, wants_foci, foci_channel2, 
                             foci_min_size,  foci_max_size, foci_min_int, 
                             foci_max_int, foci_proeminence)
        
       df_image = pd.DataFrame() 
       for cell_o in cell_list:
          cell_o.df_nucleus.insert(1, "Frame", [i], True)
          print ('inserted')
          cell_o.df_nucleus.insert(37, "Path_ch1", files_ch1[i], True)
          cell_o.df_nucleus.insert(37, "Path_ch2", files_ch2[i], True)
          df_image = pd.concat([cell_o.df_nucleus, df_image], ignore_index=True)
       
       df_total = pd.concat([df_image, df_total], ignore_index=True)
       
        
    
   df_total = df_total.reset_index(drop=True)
  
   return df_total 



def draw_and_save(
        df_contours: pd.DataFrame,
        path_save1: str,
        ch2: bool = False,  #tem coisa no canal dois?
        path_save2: Optional[str] = None,   #pasta criada na função antes do analyze
        wants_ktr: bool = False,
        use_ellipse: bool = False,
        wants_foci: bool = False,
        foci_ch2: bool = False,
        rescale_intensity: bool = False,
        remove_bg: bool = False,
        radius: int = 30,
        ref_ch1: Optional[np.array] = None,
        ref_ch2: Optional[np.array] = None,
)-> None:
    
    fs = cv.getFontScaleFromHeight(2,15,2)
    
    for i in range (df_contours.shape[0]):
        row = df_contours.loc[i]
        path1 = row['Path_ch1'][0]
        path2 = row['Path_ch2'][0]
        nuc_cnt = row['Nuc_cnt']
        ellipse_cnt = row['Ellipse_cnt']
        ring_cnt = row['Ring_cnt']
        foci_cnt = row['Foci_cnt']
        n = row['Cell_n']
        x = row['X']
        y = row['Y_draw']
          
        image1 = load_image(path1, rescale_intensity,remove_bg, radius, ref_ch1)
        image1_name = str(os.path.basename(path1))
        
        if ch2 ==True:
            image2 = load_image(path2, rescale_intensity, remove_bg, radius, ref_ch2)
            image2_name = str(os.path.basename(path2))
            
        
        for j in range(len(n)):
            cv.drawContours(image1, nuc_cnt[j], -1, (255,255,255), 1)
            cv.putText(image1, str(n[j]), (x[j],y[j]), 2, fs, (255,255,255))
            if ch2 == True:
                cv.putText(image2, str(n[j]), (x[j],y[j]), 2, fs, (255,255,255))
                cv.drawContours(image2, nuc_cnt[j], -1, (255,255,255), 1)
        
            if use_ellipse and wants_ktr == True:
                cv.drawContours(image2, ellipse_cnt[j], -1, (255,255,255), 1)
            elif wants_ktr == True:
                cv.drawContours(image2, ring_cnt[j], -1, (255,255,255), 1)
            if wants_foci and foci_ch2 == True:
                cv.drawContours(image2, foci_cnt[j], -1, (255,255,255), 1)
            elif wants_foci ==True:
                cv.drawContours(image1, foci_cnt[j], -1, (255,255,255), 1)
        
            
        cv.imwrite(os.path.join(path_save1, image1_name) , image1)
        if ch2 ==True:
             cv.imwrite(os.path.join(path_save2, image2_name) , image2)

    return None

  
    
    
