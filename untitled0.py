#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 18:57:10 2021

@author: luiza
"""


from pystackreg import StackReg
from pystackreg.util import to_uint16
from pystackreg.util import to_uint16
import os
from initializing_functions_multichannel import load_image
import numpy as np
import math
from matplotlib import pyplot as plt 
from shapely.geometry import Polygon

pathr = '/home/luiza/Área de Trabalho/red' 
pathg = '/home/luiza/Área de Trabalho/green' 




imagesr = [os.path.join(pathr, f) for f in os.listdir(pathr)]
imagesr=sorted(imagesr)
imagesr = [ load_image(f, rescale_intensity=True) for f in imagesr]
stackr = np.stack(imagesr)


imagesg = [os.path.join(pathg, f) for f in os.listdir(pathg)]
imagesg = sorted(imagesg)
imagesg = [ load_image(f, rescale_intensity=True) for f in imagesg]
stackg = np.stack(imagesg)


sr = StackReg(StackReg.RIGID_BODY)
red = sr.register_transform_stack(stackr, reference='previous')
tmats = sr.register_stack(stackr, reference='previous')    
red = to_uint16(red)

green = sr.transform_stack(stackg)


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





#check the smallest area
area_list = []
for mat in tmats:
    z = math.atan2(mat[1,0], mat[0,0])
    w, h = rotatedRectWithMaxArea(green.shape[2], green.shape[1], z)
    area_list.append(w*h)
smallest = area_list.index( min(area_list))  


#tmat with smallest area
mat = tmats[smallest]
mat =tmats[44]
center_point = np.matmul(mat, [green.shape[2]/2,green.shape[1]/2,1])

z = math.atan2(mat[1,0], mat[0,0])
w,h = rotatedRectWithMaxArea(green.shape[2], green.shape[1], z)

end_y = green.shape[1] - round( center_point[1] -(h/2 ))
start_y = green.shape[1]- round( center_point[1] +(h/2 ))

start_y = 0 if start_y < 0 else start_y
end_y = 0 if end_y < 0 else end_y



start_x = round(center_point[0] -(w/2 ))
end_x =  round(center_point[0] +(w/2 ))


start_x = 0 if start_x < 0 else start_x
end_x = 0 if end_x < 0 else end_x


icrop = green[7][start_y:end_y, start_x:end_x]
plt.imshow(icrop)



#find image that leaves the field the most
intersection_area_list = []
other_polygon_list = []
for mat in tmats:
    #new borders of image
    gsy = green.shape[1]
    coordinate1 = np.array([mat[0,2], gsy - mat[1,2], 1])
    coordinate2 = np.matmul(mat, [0, green.shape[1], 1])
    coordinate2 = np.array([coordinate2[0],gsy-coordinate2[1], coordinate2[2]])
    coordinate3 = np.matmul(mat, [green.shape[2],0, 1])
    coordinate3 = np.array([coordinate3[0],gsy-coordinate3[1], coordinate3[2]])
    coordinate4 = np.matmul(mat, [green.shape[2], green.shape[1], 1])
    coordinate4 = np.array([coordinate4[0],gsy-coordinate4[1], coordinate4[2]])
    
    
    
    polygon = Polygon([(0, 0), (0, green.shape[2]), (green.shape[1], green.shape[2]), (green.shape[1], 0)])
    other_polygon = Polygon([(coordinate1[0], coordinate1[1]), (coordinate2[0], coordinate2[1]),
                             (coordinate4[0], coordinate4[1]), (coordinate3[0],coordinate3[1])])
    intersection = polygon.intersection(other_polygon)
    intersection_area_list.append(intersection.area)
    other_polygon_list.append(other_polygon)

smallest2 = intersection_area_list.index( min(intersection_area_list))  







import matplotlib.pyplot as plt



# essa é a lista de todos os 4 potos externos das imagens depois da rotação e translação 
circles = other_polygon_list
# o inter é a intersecção de todos. me dá a maior area comum
inter = circles[0].intersection(circles[1])
for i in circles [2:]:
    inter = inter.intersection(i)


from shapely.geometry import LineString


#coords x e y do poligono inter
x, y = inter.exterior.coords.xy
x= sorted(x)
y = sorted(y)

from shapely.geometry import box
# box(minx, miny, maxx, maxy, ccw=True)
b = box(x[0], y[0], x[-1], y[-1])
b.wkt  # POLYGON ((5 30, 5 33, 2 33, 2 30, 5 30))
b.area  # 9.0



#unção que encolhe o quadrado todo

#função 2 que encolhe 3 lados, 2 ou 1 lado

def reducing_box(box_coord, bool_tuple):
    '''Retorna nova coordenada'''
    x, y = box_coord.exterior.coords.xy
    minx = round(min(x)) if bool_tuple[0] == False else round(min(x)+1)
    maxx = round(max(x)) if bool_tuple[1] == False else round(max(x)-1)
    maxy = round(max(y)) if bool_tuple[2] == False else round(max(y)-1)
    miny = round(min(y)) if bool_tuple[3] == False else round(min(y)+1)
    
    new_box_coord = Polygon([(maxx, miny),
                             (maxx, maxy),
                             (minx, maxy),
                             (minx, miny),
                             (maxx, miny)])
    
    return new_box_coord
 

def intersect(box_coord, polygon):
    ''' confere se alguma das linhas está completamente dentro do polígono,
    retorna tupla de bool, onde caada um corresponde a uma linha'''
    
    x, y = box_coord.exterior.coords.xy
    print(int(min(y)), max(y) , min(x), int(max(x)))
    
    left_line = LineString([(min(x), min(y)), (min(x), max(y))]) 
    right_line = LineString([(max(x), min(y)), (max(x), max(y))]) 
    upper_line = LineString([(min(x), max(y)), (max(x), max(y))]) 
    bottom_line = LineString([(min(x), min(y)), (max(x), min(y))]) 
    
    intersec = (left_line.intersects(polygon.exterior),
                right_line.intersects(polygon.exterior),
                upper_line.intersects(polygon.exterior),
                bottom_line.intersects(polygon.exterior)
                ) 
    return intersec

poly = inter
box = b
n = intersect(box, poly)
while any(n) == True:
    box = reducing_box(box, n)
    n = intersect(box, poly)

x,y = box.exterior.coords.xy
ycrop = round(max(y) - min(y))

crop = green[44][round(min(y)):int(max(y)), int(min(x)):int(max(x))]

for i in red:
    crop = i[round(min(y)):ycrop, int(min(x)):int(max(x))]
    plt.figure()
    plt.imshow(crop)
