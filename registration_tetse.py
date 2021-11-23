#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 09:28:49 2021

@author: luiza
"""


from pystackreg import StackReg
from pystackreg.util import to_uint16
from skimage import io
from pystackreg.util import to_uint16
import glob 
import tifffile
import os
import time 
from initializing_functions_multichannel import load_image
import numpy as np
import math
import cv2 as cv 


pathr = '/home/luiza/Área de Trabalho/red' 
pathg = '/home/luiza/Área de Trabalho/green' 




imagesr = [os.path.join(pathr, f) for f in os.listdir(pathr)]
imagesr = [ load_image(f, rescale_intensity=True) for f in imagesr]
stackr = np.stack(imagesr)


imagesg = [os.path.join(pathg, f) for f in os.listdir(pathg)]
imagesg = [ load_image(f, rescale_intensity=True) for f in imagesg]
stackg = np.stack(imagesg)


sr = StackReg(StackReg.RIGID_BODY)
red = sr.register_transform_stack(stackr, reference='previous')
tmats = sr.register_stack(stackr, reference='previous')    
red = to_uint16(red)

green = sr.transform_stack(stackg)



last_tmat= tmats[len(tmats)-1]
z_angle = math.atan2(last_tmat[1,0], last_tmat[0,0])
last_im = green[len(green)-1]

def rotatedRectWithMaxArea(w, h, angle):
  """
  Given a rectangle of size wxh that has been rotated by 'angle' (in
  radians), computes the width and height of the largest possible
  axis-aligned rectangle (maximal area) within the rotated rectangle.
  """
  if w <= 0 or h <= 0:
    return 0,0

  width_is_longer = w >= h
  side_long, side_short = (w,h) if width_is_longer else (h,w)

  # since the solutions for angle, -angle and 180-angle are all the same,
  # if suffices to look at the first quadrant and the absolute values of sin,cos:
  sin_a, cos_a = abs(math.sin(angle)), abs(math.cos(angle))
  if side_short <= 2.*sin_a*cos_a*side_long or abs(sin_a-cos_a) < 1e-10:
    # half constrained case: two crop corners touch the longer side,
    #   the other two corners are on the mid-line parallel to the longer line
    x = 0.5*side_short
    wr,hr = (x/sin_a,x/cos_a) if width_is_longer else (x/cos_a,x/sin_a)
   
  else:
    # fully constrained case: crop touches all 4 sides
    cos_2a = cos_a*cos_a - sin_a*sin_a
    wr,hr = (w*cos_a - h*sin_a)/cos_2a, (h*cos_a - w*sin_a)/cos_2a
  return round(wr),round(hr)




def new_coords(w, h, new_w, new_h, mov_x, mov_y):
    x_center = w/2
    y_center = h/2
    new_x_center = x_center + mov_x
    new_y_center = y_center + mov_y
    new_x =  new_x_center - new_w/2
    new_y =  new_y_center - new_h/2
    
    return round(new_x), round(new_y)



new_w, new_h = rotatedRectWithMaxArea(last_im.shape[1], last_im.shape[0], z_angle)
mov_x = last_tmat[0,2]
mov_y = last_tmat[1,2]
new_x, new_y = new_coords(last_im.shape[1], last_im.shape[0], new_w, new_h, mov_x, mov_y)


xf = 0 if mov_x <0 else round(mov_x)
yf = 0 if mov_y <0 else round(mov_y)




icrop2 = last_im[yf: yf+new_h, xf:xf+new_w]
icrop3 = last_im[0:new_h, 0:new_w]

#cv.imwrite('/home/luiza/Área de Trabalho/normal_teste_crop.tiff', last_im)
#cv.imwrite('/home/luiza/Área de Trabalho/cropped.tiff', icrop3)



def matmult(tmat, matrix):
    ax = matrix[0]*tmat[0,0] + matrix[1] * tmat[0,1] + matrix[2]*tmat[0,2]
    ay = matrix[0]*tmat[1,0] + matrix[1] * tmat[1,1] + matrix[2]*tmat[1,2]
    az = matrix[0]*tmat[2,0] + matrix[1] * tmat[2,1] + matrix[2]*tmat[2,2]

    return np.array([[ax, ay,az]])

point1 = np.array([[last_tmat[0,2], last_tmat[1,2], 1]])
point2 = matmult(last_tmat, [1408, 0, 1])
point3 = matmult(last_tmat, [0, 1040, 1])
point4 = matmult(last_tmat, [1408, 1040,1])
center_point =matmult(last_tmat, [704,520,1])
center_point = np.matmul(last_tmat, [704,520,1])



y_list = sorted([ point1[0][1], point2[0][1], point3[0][1], point4[0][1]])
x_list = sorted([ point1[0][0], point2[0][0], point3[0][0], point4[0][0]])
y_list= [1040 - f for f in y_list]


yf = round(y_list[1])
xf = round (x_list[1])
icrop = last_im[0:1040, xf:27]




end_y = round( center_point[1] -(new_h/2 ))
start_y =  round( center_point[1] +(new_h/2 ))
start_y = 1040-start_y
end_y = 1040-end_y

start_y = 0 if start_y < 0 else start_y
end_y = 0 if end_y < 0 else end_y



start_x = round( center_point[0] -(new_w/2 ))
end_x =  round( center_point[0] +(new_w/2 ))


start_x = 0 if start_x < 0 else start_x
end_x = 0 if end_x < 0 else end_x


icrop = last_im[start_y:end_y, start_x:end_x]

#DESISTO DESSA CARALHA
#1040-169 = 872 -> corte em y



#check the smallest area
area_list = []
for mat in tmats:
    z = math.atan2(mat[1,0], mat[0,0])
    w, h = rotatedRectWithMaxArea(last_im.shape[1], last_im.shape[0], z)
    area_list.append(w*h)
smallest = area_list.index( min(area_list))  


#tmat with smallest area
mat = tmats[smallest]

center_point2 = np.matmul(mat, [last_im.shape[1]/2,last_im.shape[0]/2,1])

z = math.atan2(mat[1,0], mat[0,0])
w,h = rotatedRectWithMaxArea(last_im.shape[1], last_im.shape[0], z)

end_y2 = last_im.shape[0] - round( center_point2[1] -(h/2 ))
start_y2 = last_im.shape[0]- round( center_point2[1] +(h/2 ))

start_y2 = 0 if start_y2 < 0 else start_y2
end_y2 = 0 if end_y2 < 0 else end_y2



start_x2 = round( center_point2[0] -(w/2 ))
end_x2 =  round( center_point2[0] +(w/2 ))


start_x2 = 0 if start_x2 < 0 else start_x2
end_x2 = 0 if end_x2 < 0 else end_x2


icrop2 = last_im[start_y2:end_y2, start_x2:end_x2]
plt.imshow(icrop2)

