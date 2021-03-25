# -*- coding: utf-8 -*-
"""
Created on Sat Dec  5 09:17:00 2020

@author: Luiza

Vai ser um substituto organizado do help.py
"""
import os

import numpy as np
import cv2 as cv
from untitled0 import generate_cell_list
import re 
import pandas as pd        
from matplotlib import pyplot as plt 
import scipy
from scipy import stats
from analyze_folder import generate_dfs
from cell_class import cell
from foci_class import foci
import math
import seaborn as sns   
from matplotlib.patches import Ellipse


n = '7-8-9'
os.chdir('D:\\imagens incucyte kaka\\clonogenico 2 kaka\\Pre TMZ\\Red')
folder_nuc = 'D:\\imagens incucyte kaka\\clonogenico 2 kaka\\Pre TMZ\\Red'
folder_cyto = 'D:\\imagens incucyte kaka\\clonogenico 2 kaka\\Pre TMZ\\Green'
magnification = 20
pixel_size = 0.3

folder_nuc_items = os.listdir(folder_nuc)
#folder_cyto_items = os.listdir(folder_cyto)
folder_cyto_items = [os.path.abspath(os.path.join(folder_cyto,i)) for i in os.listdir(folder_cyto)]
#Ktr de uma pasta só
df_foci, df_nuc, df_categories, cells_dict =  generate_dfs(folder_nuc_items, False,True, 20, folder2_items= folder_cyto_items)


for key, values in cells_dict.items():
    im = cv.imread(folder_nuc+'\\'+key, cv.IMREAD_ANYDEPTH)
    fs2 = cv.getFontScaleFromHeight(2,20,5)
    for c in values:
        cv.drawContours(im, c.cnt, -1, (255,255,255),1)
        cv.putText(im, str(c.n), (c.centroid_x, c.centroid_y), 2, fs2, (255,255,255), 1)
    plt.imshow(im, cmap='gray')
    path = 'D:\\imagens incucyte kaka\\clonogenico 2 kaka\\Pre TMZ\\Contornadas vermelho' + str(key) 
    cv.imwrite( path , im)
    


df_nuc.to_csv('D:\\imagens incucyte kaka\\clonogenico 2 kaka\\Pre TMZ\\results.csv')





'''
#cídigo tosco de rodar ktr

n = str(26)

folderb = 'C:\\Users\\Luiza Cherobini\\Desktop\\kaka\\green\\G'+ n+'.tif'
foldera = 'C:\\Users\\Luiza Cherobini\\Desktop\\kaka\\red\\R'+ n+'.tif'
save_csv = 'C:\\Users\\Luiza Cherobini\\Desktop\\kaka\\'+n+'.csv'
save1 ='C:\\Users\\Luiza Cherobini\\Desktop\\kaka\Results G ellipse\\'+n+'.tif'
save2 ='C:\\Users\\Luiza Cherobini\\Desktop\\kaka\Results R ellipse\\'+n+'.tif'

dffoc, dfnuc, dfcat,cells =  generate_dfs([foldera], False,True, 40,
                                          pixel_size = 0.1083, folder2_items = [folderb])
fs2 = cv.getFontScaleFromHeight(2,20,5)
from matplotlib import pyplot as plt
for key, value in cells.items():
    im = cv.imread(folderb)
    im2 = cv.imread(foldera)
    for c in value:
        cv.drawContours(im, c.cnt, -1, (255,255,0),1)
        cv.drawContours(im, c.cnt_ring_ellipse, -1, (255,25,200),1)
        cv.drawContours(im2, c.cnt, -1, (255,255,0),1)
        cv.drawContours(im2, c.cnt_ring_ellipse, -1, (255,25,200),1)
        #cv.drawContours(im, c.cnt, -1, (255,255,0),1)
        #cv.drawContours(im, c.ring_contour, -1, (255,255,0), 1)
        #cv.drawContours(im2, c.cnt, -1, (255,255,0),1)
        #cv.drawContours(im2, c.ring_contour, -1, (255,255,0), 1)
        cv.putText(im, str(c.n), (c.bbox_x, c.bbox_y), 2, fs2, (255,255,255), 1)
        cv.putText(im2, str(c.n), (c.bbox_x, c.bbox_y), 2, fs2, (255,255,255), 1)
        #plt.imshow(c.nuc)

dfnuc.to_csv(save_csv)        
cv.imwrite(save1,im)
cv.imwrite(save2,im2)


'''


