# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 10:13:31 2020

@author: 
    
this prints the nuclei with foci contours for further validation
"""


import cv2 as cv
from analyze_folder import generate_dfs
import copy
import os
from matplotlib import pyplot as plt

os.chdir('C:\\Users\\Luiza Cherobini\\Documents\\Doutorado\\53bp1\\Outras img\\20x')
fitems = [ 'a.tif']
#fitems = ['1 ou 2 pontos grandes.tif']

__,__,__, cells = generate_dfs(fitems, True, False, False, 20)

n = 4
for key, value in cells.items():   
    for cell_o in value:
        plt.figure()
        #plt.imshow((cell_o.lbp < 18), cmap='gray')
        #plt.title (str(cell_o.n))
        lbp = cell_o.lbp < 5
        lbp= lbp.astype('uint8') + 255
        dots = cell_o.mask_foci + 255
        cnt = cell_o.foci_cnt
        nuc = cell_o.nuc*3
        nuc2 = copy.deepcopy(cell_o.nuc*3)
        cv.drawContours(nuc2, cnt, -1, (255,255,0), 1)
        img1 = cv.hconcat([nuc, nuc2])
        img2 = cv.hconcat([lbp, dots])
        img3 = cv.vconcat([img1, img2])
        plt.imshow(img3, cmap='gray')
        plt.title(str(cell_o.n))
        file2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\nucleos\\20x\\foto_' + str(n) + ' nuc_' + str(cell_o.n) + '.tif'
        #cv.imwrite(file2, img)
    n = n + 1
    
    