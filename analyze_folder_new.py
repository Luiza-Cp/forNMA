# -*- coding: utf-8 -*-
"""
Created on Sun Jan 10 23:11:06 2021

@author: Luiza

analyze folder para o Cell novo 
"""


import numpy as np
import pandas as pd 
from initializing_functions_new import generate_cell_list 
import cv2 as cv
import os

def find_df_nuc_features_image (cell_list, image_name, wants_foci, pixel_size, image2_name):
    df_total = pd.DataFrame(columns = ['Image','Nucleus','Centroid x', 'Centroid y',
                'Nucleus Area',  "Nucleus mean intensity",'NII', 'Radius Ratio', 'Aspect',
                'Rotation Angle','Foci Count', 'Total Foci Area',  'Foci Mean Intensity',
                ' Foci/Nucleus Area', 'Image 2','Image 2 Minimum Intensity',
                "Image 2 Maximun Intensity", "Nucleus (N) mean intensity at image 2", 
                'Cytoplasmatic Ring (CR) Mean Intensity',"Cytoplasmatic Ellipse (CE) Mean Intensity", 
                'CR/N Mean', 'CR/N Mean Normalized', 'N/CR Mean', 'N/CR Mean Normalized',
                'CE/N Mean', 'CE/N Mean Normalized', 'N/CE Mean', 'N/CE Mean Normalized', 
                'ring mean image 1'])
    if image2_name is not None:
        image2_name =  str(os.path.basename(image2_name))
    
    for cell_o in cell_list:
        if wants_foci == True:
            fociNuc_area = cell_o.tot_foci_area/cell_o.area
        else: 
            fociNuc_area = None
        
        new_line = [image_name, cell_o.n, cell_o.centroid_x, cell_o.centroid_y, cell_o.area, 
                    cell_o.mean_intensity, cell_o.NII, cell_o.radius_ratio, cell_o.aspect,
                    cell_o.fellipse[2], cell_o.foci, cell_o.tot_foci_area, 
                    cell_o.tot_foci_mean, fociNuc_area, image2_name, cell_o.image2_min, 
                    cell_o.image2_max, cell_o.mean_intensity2, cell_o.ring_mean, cell_o.ellipse_mean,
                    cell_o.cn_ring, cell_o.cn_ring_norm, cell_o.nc_ring, cell_o.nc_ring_norm,
                    cell_o.cn_ellipse, cell_o.cn_el_norm, cell_o.nc_ellipse, cell_o.nc_el_norm,
                    cell_o.ring_mean_img1]
        
        
        df_total.loc[len(df_total)] = new_line
    
    return df_total

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
def generate_dfs(folder_items, wants_foci, wants_ktr,foci_other_channel, magnification, 
                 path_to_save, save_image, folder_save_1, folder_save_2, pixel_size = 0.5, 
                 folder2_items = None ):
   
    df_nuc_features = pd.DataFrame(columns = ['Image','Nucleus','Centroid x', 'Centroid y',
                'Nucleus Area',  "Nucleus mean intensity",'NII', 'Radius Ratio', 'Aspect',
                'Rotation Angle','Foci Count', 'Total Foci Area',  'Foci Mean Intensity',
                ' Foci/Nucleus Area', 'Image 2','Image 2 Minimum Intensity',
                "Image 2 Maximun Intensity", "Nucleus (N) mean intensity at image 2", 
                'Cytoplasmatic Ring (CR) Mean Intensity',"Cytoplasmatic Ellipse (CE) Mean Intensity", 
                'CR/N Mean', 'CR/N Mean Normalized', 'N/CR Mean', 'N/CR Mean Normalized',
                'CE/N Mean', 'CE/N Mean Normalized', 'N/CE Mean', 'N/CE Mean Normalized',
                 'ring mean image 1'])
    
    df_foci_features = pd.DataFrame(columns = ['Image','Nucleus of origin', 'Foci', 
                                               'Area','Mean Intensity'])
    
    df_foci_categories = None
    cells_dict =  {} 
    
    for i in range(len(folder_items)):
       
        image_name = str(os.path.basename(folder_items[i]))
        if folder2_items is None:
            cells = generate_cell_list(folder_items[i], magnification, wants_foci, wants_ktr, 
                                       foci_other_channel, pixel_size)  
            image_folder2 = None
            image2_to_draw = None
            
        else:
            image2_name = str(os.path.basename(folder2_items[i]))
            image2_to_draw =cv.imread(folder2_items[i],cv.IMREAD_ANYDEPTH)
            image_folder2= folder2_items[i]
            cells = generate_cell_list(folder_items[i], magnification, wants_foci, wants_ktr, 
                                       foci_other_channel, pixel_size, image_folder2)
            
        df_nuc_features_image= find_df_nuc_features_image (cells, image_name, wants_foci, 
                                                           pixel_size, image_folder2)
        df_nuc_features = pd.concat([df_nuc_features, df_nuc_features_image], sort=False)
        
        if wants_foci == True:
            df_foci_feat_image =find_df_foci(cells, image_name)
            df_foci_features = pd.concat([df_foci_features, df_foci_feat_image], sort=False)
            df_foci_categories = foci_in_categories(df_nuc_features)
        else:
            df_foci_features = None
            df_foci_categories = None
            
            
        #cells_dict[image_name] = cells
        
        if save_image == True:
            fs = cv.getFontScaleFromHeight(2,15,3)
            image =  cv.imread(folder_items[i],cv.IMREAD_ANYDEPTH)
            #image_draw =cv.cvtColor(image,cv.COLOR_GRAY2RGB)
            image_draw = image
            for Cell_o in cells:
                cv.drawContours(image_draw, Cell_o.cnt, -1, (122,97,246),1)
                cv.putText(image_draw, str(Cell_o.n), (Cell_o.centroid_x, Cell_o.bbox_y), 
                           2, fs, (152,204,239), 2)
                if wants_foci == True and foci_other_channel == False:
                    cv.drawContours(image_draw, Cell_o.foci_cnt_im, -1, (122,97,246),1)
            #cv.imwrite(folder_save_1 + image_name + '.jpeg', image_draw)
            cv.imwrite(folder_save_1 + image_name, image_draw)
            
        if image2_to_draw is not None:
            fs = cv.getFontScaleFromHeight(2,15,3)
            image2 =  cv.imread(folder2_items[i],cv.IMREAD_ANYDEPTH)
            image2_draw = image2#cv.cvtColor(image2,cv.COLOR_GRAY2RGB)

           
            
            for Cell_o in cells:
                cv.drawContours(image2_draw, Cell_o.cnt, -1, (122,97,246),1)
                cv.putText(image2_draw, str(Cell_o.n), (Cell_o.centroid_x, Cell_o.bbox_y), 
                           2, fs, (152,204,239), 2)
                if wants_ktr == True:
                    cv.drawContours(image2_draw, Cell_o.cnt_ring_ellipse, -1, (122,97,246),1)
                if wants_foci == True and foci_other_channel == True:
                    cv.drawContours(image2_draw, Cell_o.foci_cnt_im, -1, (122,97,246),1)
            
           
            cv.imwrite(folder_save_2 + image2_name , image2_draw)
            
                        
    return df_foci_features, df_nuc_features, df_foci_categories, cells_dict     


#cells dict é muito pesado, melhor retornar contornos, números ... maybe