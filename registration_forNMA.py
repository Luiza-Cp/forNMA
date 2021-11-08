#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 15:19:04 2021

@author: luiza
"""

import os
import pystackreg
from pystackreg import StackReg
from pystackreg.util import to_uint16
from typing import List, Tuple, Optional 
import numpy as np
import cv2 as cv
import shapely 
from shapely.geometry import Polygon, LineString, box


def open_images(path: str)-> Tuple[np.ndarray, List[str]]:
    """ Loads images and creates a stack """
    image_names = sorted(os.listdir(path)) # removi sorted aqui
    image_paths = [os.path.join(path, i) for i in image_names]
    images = [cv.imread(i,cv.IMREAD_ANYDEPTH) for i in image_paths]
    stack = np.stack(images) 
    
    return stack, image_names
    

def registrate_stack(stack: np.ndarray
) -> Tuple[np.ndarray, pystackreg.pystackreg.StackReg, np.ndarray]:
    """
    From a stack, performs image transformation of slices according to the 
    previous transformed slice.
    """
    sr = StackReg(StackReg.RIGID_BODY)
    transformed_stack = sr.register_transform_stack(stack, reference='previous')
    transformation_matrix = sr.register_stack(stack, reference='previous')
    
    return transformed_stack, sr, transformation_matrix


def find_new_coordinates(x: int,
                         y: int, 
                         tmats: np.ndarray
)-> List[shapely.geometry.polygon.Polygon]:
    """ Transforms image boundaries to its new coordinates (from registration). """
    
    polygon_list = []
    for mat in tmats:
        coordinate1 = np.array([mat[0,2], y - mat[1,2], 1])      #   x, y, z 
        coordinate2 = np.matmul(mat, [0, y, 1])
        coordinate2 = np.array([coordinate2[0],y-coordinate2[1], coordinate2[2]])
        coordinate3 = np.matmul(mat, [x, 0, 1])
        coordinate3 = np.array([coordinate3[0],y-coordinate3[1], coordinate3[2]])
        coordinate4 = np.matmul(mat, [x, y, 1])
        coordinate4 = np.array([coordinate4[0],y-coordinate4[1], coordinate4[2]])
        registered_rectangle = Polygon([(coordinate1[0], coordinate1[1]), 
                                        (coordinate2[0], coordinate2[1]),
                                        (coordinate4[0], coordinate4[1]), 
                                        (coordinate3[0],coordinate3[1])])
        polygon_list.append(registered_rectangle)
   
    return polygon_list


def find_bbox(polygon: shapely.geometry.polygon.Polygon) -> shapely.geometry.polygon.Polygon:
    """ Finds a polygon bounding box. """
    x_list, y_list = polygon.exterior.coords.xy
    x_list = sorted(x_list)
    y_list = sorted(y_list)
    bbox = box(x_list[0], y_list[0], x_list[-1], y_list[-1])
   
    return bbox


def reducing_box(bbox: shapely.geometry.polygon.Polygon,
                 bool_tuple: Tuple[bool]
)-> shapely.geometry.polygon.Polygon:
    """
        Reduces all sides of a box in two integers, if the value corresponding to 
    the specified side is set true in the given tuple. The bools in the tuple
    corespond to: (minimun x, maximun x, maximun y and minimun y).
    """
    x_list, y_list = bbox.exterior.coords.xy
    minx = round(min(x_list)) if bool_tuple[0] == False else round(min(x_list)+1)
    maxx = round(max(x_list)) if bool_tuple[1] == False else round(max(x_list)-1)
    maxy = round(max(y_list)) if bool_tuple[2] == False else round(max(y_list)-1)
    miny = round(min(y_list)) if bool_tuple[3] == False else round(min(y_list)+1)
    
    new_box_coord = Polygon([(maxx, miny),
                             (maxx, maxy),
                             (minx, maxy),
                             (minx, miny),
                             (maxx, miny)])
    
    return new_box_coord
 

def intersect_lines(bbox: shapely.geometry.polygon.Polygon,
                    polygon: shapely.geometry.polygon.Polygon
)-> Tuple[bool]:
    """ 
        Divides box sides in 4 lines (left, right, upper, bottom) and checks
    if those lines are within the polygon. If a line has no intersections with 
    the polygon, the tuple item that corresponds to that line will be returned
    as False.
    """
    
    x_list, y_list = bbox.exterior.coords.xy
    
    left_line = LineString([(min(x_list), min(y_list)), (min(x_list), max(y_list))]) 
    right_line = LineString([(max(x_list), min(y_list)), (max(x_list), max(y_list))]) 
    upper_line = LineString([(min(x_list), max(y_list)), (max(x_list), max(y_list))]) 
    bottom_line = LineString([(min(x_list), min(y_list)), (max(x_list), min(y_list))]) 
    
    intersec = (left_line.intersects(polygon.exterior),
                right_line.intersects(polygon.exterior),
                upper_line.intersects(polygon.exterior),
                bottom_line.intersects(polygon.exterior)) 
    
    return intersec


def adjust_box(bbox: shapely.geometry.polygon.Polygon,
               polygon: shapely.geometry.polygon.Polygon
)-> Tuple[int]:
    """ 
        Reduces box in a loop until all gox is inside the polygon. Returns new
    minimum y, new maximum y, new minimum x and new maximum x.
    """
    bool_tuple = intersect_lines(bbox, polygon)
    while any(bool_tuple) == True:
        bbox = reducing_box(bbox, bool_tuple)
        bool_tuple = intersect_lines(bbox, polygon)

    x_list, y_list = bbox.exterior.coords.xy        # bbox is a inner box now
   
   
    return int(min(y_list)), int(max(y_list)), int(min(x_list)), int(max(x_list))
    

def coord_to_crop(stack_shape: np.ndarray,
                  tmats: np.ndarray
)-> Tuple[int]:
    """ 
    Calculates the new image xy coordinates.
    Returns a tuple with minimun y, maximun y, minimum x and maximun x.
    """  
    polygons = find_new_coordinates(stack_shape[2], stack_shape[1], tmats)
    polygons_intersection = polygons[0].intersection(polygons[1])
    for i in polygons [2:]:
        polygons_intersection = polygons_intersection.intersection(i) 
    bbox = find_bbox(polygons_intersection)
    miny, maxy, minx, maxx = adjust_box(bbox, polygons_intersection)
    
    return miny, maxy, minx, maxx


def save(stack: np.ndarray,
         filenames: List[str],
         path_to_save: str ,
         original_path: str,
         crop: Optional[Tuple[int]]
) -> bool:
    """ Saves each stack slice in the specified folder."""
    stack = to_uint16(stack)
    path = os.path.join(path_to_save, os.path.basename(original_path))
    os.makedirs(path)
    if crop != None:
        stack = stack[0:stack.shape[0], crop[0]:crop[1], crop[2]:crop[3]]
    for i in range(len(filenames)):
        cv.imwrite(os.path.join(path, filenames[i]), stack[i])
    
    return True
         

# deve haver um loop na interface chamando essa pra cada grupo de pastas
def registration (folders_to_register: List[str],
                  path_to_save: str,
                  crop: bool = True
) -> bool:
    """
    Iterates over a list of paths performing registration of itens within 
    it. If list contains more than one item, uses the transformation matrix 
    from first item to register the other list items.
    If crop is True, crops images to keep just parts that remains in field 
    through all experiment.
    """
    stack, names = open_images(folders_to_register[0])
    new_stack, sr, tmat = registrate_stack(stack)   
    crop_coordinates = coord_to_crop(stack.shape, tmat) if crop == True else None
    save(new_stack, names, path_to_save, folders_to_register[0], crop_coordinates)
    if len(folders_to_register) > 1:
        for i in range(1, len(folders_to_register)):
            stack2, names2 = open_images(folders_to_register[i])
            stack2_from_stack = sr.transform_stack(stack2)
            save(stack2_from_stack, names2, path_to_save, folders_to_register[i], crop_coordinates)
            

registration([ '/home/luiza/Área de Trabalho/red' ,  '/home/luiza/Área de Trabalho/green'],
             '/home/luiza/Área de Trabalho/registradas')