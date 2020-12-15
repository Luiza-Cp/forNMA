# -*- coding: utf-8 -*-
"""
Created on Sat Dec  5 09:17:00 2020

@author: Luiza

Vai ser um substituto organizado do help.py
"""
import os

import numpy as np
import cv2 as cv
from initializing_functions2 import generate_cell_list
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


n = str(16)
#os.chdir('C:\\Users\\Luiza Cherobini\\Desktop\\teste')
os.chdir('C:\\Users\\Luiza Cherobini\\Desktop\\lu1')
folder_nuc = 'C:\\Users\\Luiza Cherobini\\Desktop\\lu1'
#folder_nuc ='C:\\Users\\Luiza Cherobini\\Desktop\\teste'
folder_cyto = 'C:\\Users\\Luiza Cherobini\\Desktop\\lu2'
#folder_cyto ='C:\\Users\\Luiza Cherobini\\Desktop\\teste'
magnification = 40
pixel_size = 0.2

folder_nuc_items = os.listdir(folder_nuc)
#folder_cyto_items = os.listdir(folder_cyto)
folder_cyto_items = [os.path.abspath(os.path.join(folder_cyto,i)) for i in os.listdir(folder_cyto)]
#Ktr de uma pasta só
df_foci, df_nuc, df_categories, cells_dict =  generate_dfs(folder_nuc_items, False,True, 20, folder2_items= folder_cyto_items)


for key, values in cells_dict.items():
    im = cv.imread(folder_nuc+'\\'+key, cv.IMREAD_ANYDEPTH)
    fs2 = cv.getFontScaleFromHeight(2,20,5)
    for c in values:
        cv.drawContours(im, c.cnt, -1, (255,255,0),1)
        cv.putText(im, str(c.n), (c.centroid_x, c.centroid_y), 2, fs2, (255,255,255), 1)
    plt.imshow(im, cmap='gray')
    path =  'D:\\Imagens incucyte lu\\c5_16_contoured\\cnt' + str(key) 
    cv.imwrite( path , im)
    


df_nuc.to_csv('D:\\Imagens incucyte lu\\dataframes\\c5_'+ n+ '.csv')





from matplotlib import pyplot as plt
from skimage import io, img_as_float, exposure,color
from skimage.filters import  threshold_triangle, threshold_yen
from skimage.segmentation import clear_border
import cv2 as cv
import numpy as np
import copy
from cell_class import cell 
import os
import math
img1 = cv.imread(folder_nuc_items[0], 0)
equalized_img1 = exposure.equalize_adapthist(img1) 
img2= cv.imread(folder_nuc_items[0], 0)

thresh = threshold_yen(img2)
binary = img2 <= thresh 
binary = binary.astype('uint8')
kernel=np.ones((3,3), np.uint8)
erode =  cv.erode (binary, kernel, iterations=1)
dilate =  cv.dilate (erode, kernel, iterations=round(0.65/0.5))

plt.imshow(equalized_img1,cmap='gray')

im = cv.imread('D:\\Imagens incucyte lu\\c4_1_RED\\VID20_C4_1_00d00h00m.tif', cv.IMREAD_ANYDEPTH )
cv.namedWindow('image', cv.WINDOW_NORMAL)
cv.imshow('image', im)
cv.waitKey(0)
cv.destroyAllWindows()
plt.imshow(im)

import skimage
from skimage import io
moon = io.imread('D:\\Imagens incucyte lu\\c4_1_RED\\VID20_C4_1_00d00h00m.tif')
plt.imshow(moon)


cv.namedWindow('image', cv.WINDOW_NORMAL)
cv.imshow('image',moon)
cv.waitKey(0)
cv.destroyAllWindows()

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


