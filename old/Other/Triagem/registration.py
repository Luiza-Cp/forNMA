# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 23:14:04 2021

@author: Luiza
"""

from pystackreg import StackReg
from pystackreg.util import to_uint16
from skimage import io
from pystackreg.util import to_uint16

import tifffile
#img0 = io.imread('C:\\Users\Luiza Cherobini\\Desktop\\bbb.tif') # 3 dimensions : frames x width x height
#img1 = io.imread('C:\\Users\Luiza Cherobini\\Desktop\\aaa.tif') # same shape as img0
#assert img0.shape == img1.shape
import glob 
pa = 'C:\\Users\\Luiza Cherobini\\Desktop\\campo res'
path ='C:\\Users\\Luiza Cherobini\\Desktop\\campo R'
path2 ='C:\\Users\\Luiza Cherobini\\Desktop\\campo g'

with tifffile.TiffWriter('C:\\Users\Luiza Cherobini\\Desktop\\r.tif') as stack:
    for filename in glob.glob(path+ '\\*'):
        stack.save(tifffile.imread(filename))
        
with tifffile.TiffWriter('C:\\Users\Luiza Cherobini\\Desktop\\g.tif') as stack:
    for filename in glob.glob(path2+ '\\*'):
        stack.save(tifffile.imread(filename))

img0 = io.imread('C:\\Users\Luiza Cherobini\\Desktop\\r.tif', plugin='pil')
img1 = io.imread('C:\\Users\Luiza Cherobini\\Desktop\\g.tif', plugin='pil')

assert img0.shape == img1.shape

sr = StackReg(StackReg.RIGID_BODY)

# register each frame to the previous (already registered) one
# this is what the original StackReg ImageJ plugin uses
out_previous = sr.register_transform_stack(img0, reference='previous')



# register to first image
#out_first = sr.register_transform_stack(img0, reference='first')

# register to mean image
#out_mean = sr.register_transform_stack(img0, reference='mean')

# register to mean of first 10 images
#out_first10 = sr.register_transform_stack(img0, reference='first', n_frames=10)

# calculate a moving average of 10 images, then register the moving average to the mean of
# the first 10 images and transform the original image (not the moving average)
#out_moving10 = sr.register_transform_stack(img0, reference='first', n_frames=11, moving_average = 11)



tmats = sr.register_stack(img0, reference='previous')
out = sr.transform_stack(img1)
sr.transform_stack(img1, tmats=tmats)
out_previous = to_uint16(out_previous)
out = to_uint16(out)
#tifffile.imsave('C:\\Users\\Luiza Cherobini\\Desktop\\g.tiff', out)
#tifffile.imsave('C:\\Users\\Luiza Cherobini\\Desktop\\r.tiff',out_previous)

import os
name = os.listdir(path)
name2 = os.listdir(path2)
os.mkdir(pa+ '\\registered')
pat = pa+ '\\registered'
os.mkdir(pat +'\\Green' )
os.mkdir(pat +'\\Red' )

save = pat + '\\Red\\'
save2 =pat + '\\Green\\'

import cv2 as cv
n = 0
for a in out_previous:
     print (a.shape, a.dtype )
     io.imsave(save + name[n] + '.tiff', a)
     n= n+1
n=0
for a in out:
     io.imsave(save2 +  name2[n] +  '.tiff', a)
     n= n+1    
     
     
for item in img0:
    print (item.shape, item.dtype )
# descobrir como salvar essas fotos em formato ok ou se o fornma abre elas 
#nesse tiff random aqui