# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 09:29:09 2021



@author: Luiza
"""

#match histograms defeituoso!!!!!!!

from typing import Optional, List
import numpy as np
import cv2 as cv
from initializing_functions_advanced2 import run_image
from skimage import  img_as_ubyte, exposure, restoration
from skimage.exposure import match_histograms
import logging
import os
import pandas as pd

logging.basicConfig(format='%(asctime)s %(message)s')

not_processed = []
#remover Nones dessa lista no fim -> [x for x in L if x is not None]
#tentar um @ jit aqui
def load_image(
        filename: str, 
        rescale_intensity: bool = False,
        remove_bg: bool = False,
        radius: int = 30,
        ref: Optional[np.ndarray] = None
) -> Optional[np.array]:
    """ 
    It opens the image, performs intensity adjustments, if required, and
    converts image to ubyte. If file can not be opened, adds the file
    to not_procesed list.
    """
    print (filename)
    img = cv.imread(filename,cv.IMREAD_ANYDEPTH)
    if  img is None or img.size == 0:
        not_processed.append(filename)
        return None
    
    if ref is not None:
        img = match_histograms(img, ref)
        img =img.astype('ubyte')

    if rescale_intensity == True:
        img = exposure.rescale_intensity(img, in_range='image', out_range='dtype')
    elif img.dtype.kind == 'f' and (np.any(img>1) or np.any(img<-1)):
        img = exposure.rescale_intensity(img, in_range='image', out_range='dtype')
        
    img = img_as_ubyte(img) 
   
   ####
    
    if remove_bg == True:
        background = restoration.rolling_ball(img, radius = radius )
        img = img-background
     
    return img


#listas ja devem, chegar aqui com mesmo tamanho (se tiver 2) e com sort aplicado
def preview_contours(
        files_ch1: List[str], 
        magnification: int, 
        files_ch2: Optional[List[str]] = None,
        pixel_size: Optional[float] = 0.5, 
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
        rescale_intensity: bool = False, 
        fast_detection: bool = False,
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
        foci_proeminence: Optional[int] = None
) -> np.ndarray:
    
    for i in range(len(files_ch1)):
        img1 = load_image(files_ch1[i], rescale_intensity)
        __, img1_name =  os.path.split(files_ch1[i])
        if files_ch2 != None:
            img2 = load_image(files_ch2[i], rescale_intensity)
            __, img2_name =  os.path.split(files_ch2[i])
            logging.info('analyzing pair number ' + str(i)+ ' (channel 1 = ' + 
                         img1_name + 'channel 2 = ' + img2_name + ')')
        else:
            logging.info('analyzing image number ' +str(i)+ ' (channel 1 = ' + 
                         img1_name + ')')
            
        if img1 is None:
            continue
        
        else:
            cell_list = run_image(img1,img1_name, magnification, img2, img2_name, 
                                  pixel_size, threshold,
                       offset, blur, adjust_size, cut_edges, shape, eccentricity, 
                       min_size, max_size, min_radius, max_radius,fast_detection, 
                       error, wants_ktr, ring_size, use_ellipse, wants_foci,
                       foci_channel2, foci_min_size, foci_max_size, foci_min_int,
                       foci_max_int, foci_proeminence)
    
        img1_draw = img1.copy()
        img2_draw = img2.copy()
          
        fs = cv.getFontScaleFromHeight(2,15,2)  #de repente mudar o height de acordo com qtd de pixels  
        for cell_o in cell_list:
             cv.drawContours(img1_draw,cell_o.cnt, -1, (255,255,255), 1)
             cv.putText(img1_draw, str(cell_o.n), (cell_o.centroid_x, cell_o.bbox_y1),
                                   2, fs, (255,255,255))
            
             if wants_foci == True:
                cv.drawContours(img1_draw,cell_o.foci_cnt_im, -1, (255,255,255), 1) 
                
            
             if wants_ktr == True:
                cv.drawContours(img2_draw,cell_o.cnt, -1, (255,255,255), 1) 
                cv.putText(img2_draw, str(cell_o.n), (cell_o.centroid_x, cell_o.bbox_y1),
                                   2, fs, (255,255,255))
                
                if use_ellipse == True:
                    cv.drawContours(img2_draw,cell_o.ellipse_cnt, -1, (255,255,255), 1) 
                else: 
                    cv.drawContours(img2_draw,cell_o.ring_cnt, -1, (255,255,255), 1) 
                         
        cv.imwrite('C:\\Users\\Luiza Cherobini\\Desktop\\aaa.tiff', img1_draw)
        yield img1_draw, img2_draw









#devolver contorno com cor? transformar em RGB
#deolver o contorno independente da imagem pra facilitar ajuste de intensidade?
#comentar o Divide e encontrar o erro 
#tudo bw por enquanto. Depois penso se meto canais no tiff, sepa sim





'''

path1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\video kaka\\r\\red\\'
path2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\video kaka\\g\\green\\'

files1 = [path1 + 'VID429-karine-red-erk53bp1-30min_B5_19_2021y02m28d_15h05m.tif', 
          path1 + 'VID429-karine-red-erk53bp1-30min_B5_19_2021y02m28d_15h35m.tif']

files2 = [path2 +'VID429-videokarine-erk53bp1-30min_B5_19_2021y02m28d_15h05m.tif', 
          path2 + 'VID429-videokarine-erk53bp1-30min_B5_19_2021y02m28d_15h35m.tif'] 
a = preview_contours(files1, 20, pixel_size = 0.6, files_ch2 = files2, wants_ktr = True, 
                     rescale_intensity = True, use_ellipse = True, wants_foci = True,
                     foci_proeminence=350, foci_min_size=6)

for foto in a:
   cv.namedWindow('resultado', cv.WINDOW_NORMAL)
   cv.imshow('resultado', foto[0])
   cv.waitKey(0)
   cv.imshow('resultado', foto[1])
   cv.waitKey(0)

c = analyze (files1, 20, pixel_size = 0.6, files_ch2 = files2, wants_ktr = True, 
             rescale_intensity = True, use_ellipse = True, wants_foci = True,
             foci_proeminence=350, foci_min_size=6)


df_salva, df_contornos = split_dfs(c, True, False, True)


#fazer contornos em uma imagem np.zeros e fazer overlay
#criar a função de ajustar brilho, aí quando a pessoa muda na barrinha em loop 
# o ju chama essa função em loop
#a função pega a imagem original e soma ou subtrai o valor desejado e aplica o 
#overlay de novo, retonando a imagem ajustada sem mudar o overlay. Acho q isso.
# tenho que er se não pode ser demmebrando a imgem final de repente. n sei 

  

#Checar ws pq alguns contornos ficam dentro uns dos outros
'''