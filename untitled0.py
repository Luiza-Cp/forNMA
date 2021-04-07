# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 07:53:10 2021

@author: Luiza
"""
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from scipy import signal

img = cv.imread('C:\\Users\\Luiza Cherobini\\Desktop\\video kaka\\r\\red\\VID429-karine-red-erk53bp1-30min_B5_19_2021y02m28d_15h05m')
dst = cv.fastNlMeansDenoisingColored(img,None,10,10,7,21)
dst1 = cv.fastNlMeansDenoisingColored(img,None,10,10,7,49) 
dst2 = cv.blur(img, (5,5))
dst3 = cv.medianBlur(img,5)
dst4 = cv.GaussianBlur(img,(5,5),0)
dst5 =cv.bilateralFilter(img,9,75,75)

dst_l = [img, dst, dst1, dst2, dst3, dst4, dst5]

kernlen = 181
std= kernlen/5
GaussianKernel1d = signal.gaussian(kernlen, std=std).reshape(kernlen, 1)
kernel = np.outer(GaussianKernel1d, GaussianKernel1d)

for i in range(len(dst_l)):
    th = cv.morphologyEx(dst_l[i], cv.MORPH_TOPHAT, kernel)   
    cv.imwrite('C:\\Users\\Luiza Cherobini\\Desktop\\kaka\\th' + str(i) + '.tif', th)


# top1 = dst1 + tophat com kernel 99 + std = kerneln/5