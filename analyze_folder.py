  # -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 11:09:34 2020

@author: Luiza Cherobini
"""

from matplotlib import pyplot as plt
import cv2 as cv
import numpy as np
import pandas as pd 
from untitled0 import generate_cell_list , read_image

def find_ktr_ring (cell_object, image):
    ring_bbox = cell_object.bbox2
    ring_mask = cell_object.ring
    ring_el = cell_object.ring_ellipse
    roi_image = image[ring_bbox[1] : ring_bbox[1] + ring_bbox[3],
                          ring_bbox[0] : ring_bbox[0] + ring_bbox[2]]
    mean_ring = cv.mean(roi_image,mask = ring_mask)
    mean_ring_el = cv.mean(roi_image,mask = ring_el) 
    nuc_mask = np.zeros(image.shape, np.uint8)
    cv.drawContours(nuc_mask, [cell_object.cnt], -1, (255,255,255),-1)
    nuc_mask = nuc_mask[ring_bbox[1] : ring_bbox[1] + ring_bbox[3],
                          ring_bbox[0] : ring_bbox[0] + ring_bbox[2]]
    
    mean_nuc =cv.mean(roi_image,mask = nuc_mask)   
    cytoplasm_nuc_ratio =  mean_ring[0]/mean_nuc[0]
    nuc_cytoplasm_ratio = mean_nuc[0]/ mean_ring[0]
    
    cn_el = mean_ring_el[0]/mean_nuc[0]
    nc_el = mean_nuc[0]/ mean_ring_el[0]
    return mean_ring[0], cytoplasm_nuc_ratio, nuc_cytoplasm_ratio, cn_el, nc_el, mean_ring_el[0]

def find_df_ktr (cell_list, image_name, image, wants_foci):
    df_with_ktr = pd.DataFrame(columns = ['Image','Nucleus', 'Nucleus Area', 'NII',
                                'Foci Count', 'Total Foci Area', 'Foci Mean Intensity',
                                ' Foci/Nucleus Area', 'Cytoplasm Ring Mean Intensity',
                                'Cytoplasm/Nucleus Mean Intensity',
                                'Nucleus/Cytoplasm Mean Intensity', 'N/C ellipse', 'C/N ellipse',
                                 'Cytoplasm Ellipse Ring Mean Intensity', 'centroid_x', 'centroid_y'])

  
    for cell_o in cell_list:
        mean_ring, cn_ratio, nc_ratio, cn_el, nc_el, mean_el = find_ktr_ring(cell_o, image)
        if wants_foci == True:
            fociNuc_area = cell_o.tot_foci_area/cell_o.area
        else: 
            fociNuc_area = None
        new_line = [image_name, cell_o.n, cell_o.area, cell_o.NII, cell_o.foci,
                    cell_o.tot_foci_area, cell_o.tot_foci_mean, fociNuc_area, mean_ring,
                    cn_ratio, nc_ratio, nc_el, cn_el, mean_el, cell_o.centroid_x, cell_o.centroid_y]
        df_with_ktr.loc[len(df_with_ktr)] = new_line
    
    return df_with_ktr


def find_df_no_ktr (cell_list, image_name, wants_foci):
    df_without_ktr = pd.DataFrame(columns = ['Image','Nucleus', 'Nucleus Area', 'NII',
                                'Foci Count', 'Total Foci Area', 'Foci Mean Intensity',
                                ' Foci/Nucleus Area'])
    for cell_o in cell_list:
        if wants_foci == True:
            fociNuc_area = cell_o.tot_foci_area/cell_o.area
        else: 
            fociNuc_area = None
        
        new_line = [image_name, cell_o.n, cell_o.area, cell_o.NII, cell_o.foci,
                    cell_o.tot_foci_area, cell_o.tot_foci_mean, fociNuc_area]
        df_without_ktr.loc[len(df_without_ktr)] = new_line
    
    return df_without_ktr

def find_df_foci (cell_list, image_name):
    df_foci = pd.DataFrame(columns = ['Image','Nucleus of origin', 'Foci', 'Area',
                                      'Mean Intensity'])
    for cell_o in cell_list:
        for foci_o in cell_o.foci_list:
            new_line = [image_name, cell_o.n, foci_o.n, foci_o.area, foci_o.mean_int]    
            df_foci.loc[len(df_foci)] = new_line
    
    return df_foci

def foci_in_categories(dataFrame):
    a = np.sum(dataFrame['Foci Count'] == 0)
    b = np.sum(dataFrame['Foci Count'] == 1)
    c = np.sum(dataFrame['Foci Count'] == 2)
    d = np.sum(dataFrame['Foci Count'] == 3)
    e = np.sum(dataFrame['Foci Count'] == 4)
    f = np.sum(dataFrame['Foci Count'] == 5)
    g = np.sum(dataFrame['Foci Count'] == 6)
    h = np.sum(dataFrame['Foci Count'] == 7)
    i = np.sum(dataFrame['Foci Count'] == 8)
    j = np.sum(dataFrame['Foci Count'] == 9)
    k = np.sum(dataFrame['Foci Count'] == 10)
    l =np.sum(dataFrame['Foci Count'] > 10)
    
   
    data = {'Category': ['0 Foci', '1 Foci', '2 Foci', '3 Foci', '4 Foci', 
                         '5 Foci', '6 Foci', '7 Foci', '8 Foci', '9 Foci',
                         '10 Foci', 'More than 10 foci'],
            'Nucleus Count' : [a,b,c,d,e,f,g,h,i,j,k,l]}
    foci_categories_df = pd.DataFrame(data)
    return foci_categories_df
    
    
    
# na função de draw cnt, tentar ver pra desenhar o número do núcleo na foto           
#pensar em magnificação 5x para coisas como NMAe maybe ktr
#aqui tem a main antes dessa


#folder_items = folder 
def generate_dfs(folder_items, wants_foci, wants_ktr, magnification, 
                  pixel_size = 0.5, folder2_items = None ):
   
    df_nuc_features = pd.DataFrame(columns = ['Image','Nucleus', 'Nucleus Area', 'NII',
                                'Foci Count', 'Total Foci Area', 'Foci Mean Intensity',
                                ' Foci/Nucleus Area', 'Cytoplasm Ring Mean Intensity',
                                'Cytoplasm/Nucleus Mean Intensity',
                                'Nucleus/Cytoplasm Mean Intensity', 'N/C ellipse', 'C/N ellipse',
                                'Cytoplasm Ellipse Ring Mean Intensity', 'centroid_x', 'centroid_y'])
    
    df_foci_features = pd.DataFrame(columns = ['Image','Nucleus of origin', 'Foci', 
                                               'Area','Mean Intensity'])
    
    
    cells_dict =  {} 
    

    for i in range(len(folder_items)):
        print (folder_items[i])
        cells = generate_cell_list(folder_items[i], magnification, wants_foci, pixel_size)
       
        image_name = folder_items[i]
        
        if wants_foci == True:
            df_foci_feat_image =find_df_foci(cells, image_name)
            df_foci_features = pd.concat([df_foci_features, df_foci_feat_image], sort=False)
            
            
        if wants_ktr == True:
           __, image_folder2, __ = read_image(folder2_items[i])
           df_nuc_features_image = find_df_ktr(cells, image_name, image_folder2, wants_foci)
           
        else:
            df_nuc_features_image = find_df_no_ktr(cells, image_name, wants_foci)
            
        df_nuc_features = pd.concat([df_nuc_features, df_nuc_features_image], sort=False)
        cells_dict[image_name] = cells
        
        df_foci_categories = foci_in_categories(df_nuc_features)
        
    return df_foci_features, df_nuc_features, df_foci_categories, cells_dict     


