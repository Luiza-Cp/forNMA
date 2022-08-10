# -*- coding: utf-8 -*-
"""
Created on Sun May 16 20:11:52 2021

@author: Luiza
"""
import numpy as np
import os
import pandas as pd
from typing import List, Optional
from measure.Morphology import Morphology 
from measure.Cell import Cell
from segmentation.find_contours import fornma_contour_finding, load_image
from segmentation.cellpose_integration import run_cellpose
   
pd.options.mode.chained_assignment = None  # default='warn'

def measure_image(
        path_image: str, 
        dict_param: dict,
        ref: np.ndarray, 
        contour_list: List[np.ndarray],
        mag: int,
        ps: float,
        channel_name: str
)-> pd.DataFrame:
    
    """
    Loads an image - given by its path - using parameters present in dict_param.
    Uses the ref as reference for matching histograms during load.
    Creates Cell objects  based on parameters present at dict_param and returns 
    a dataframe with its measurements.
    """
    
    dp = dict_param 
    name = os.path.basename(path_image)
    img_to_measure = load_image(path_image, rescale_intensity = dp['rescale_intensity'],
                       remove_bg = dp['remove_bg'], radius_bg = dp['radius_bg'],
                       ref = ref)
    cell_df_list = []
    for i in range(len(contour_list)):
        cell_obj = Cell(i+1, contour_list[i], mag, ps, img_to_measure, name, 
                        channel_name, dp['wants_ktr'], dp['ring_size'], 
                        dp['wants_foci'], dp['foci_min_size'], 
                        dp['foci_max_size'], dp['foci_min_int'], 
                        dp['foci_max_int'], dp['foci_proeminence'], 
                        dp['use_ellipse'])
        cell_df_list.append(cell_obj.df)
       
    return cell_df_list, img_to_measure, name
    

def perform_measure(contours: np.ndarray,
                    img_n: int,
                    subfolder_dict: dict,
                    ref_dict: dict,
                    segment_dict: dict
                    ):
    """ 
        Applies functions needed for cell morphometry and intesity measures
    Returns a dataframe with all image information.
    """
    df_morpho_list  = []
    for n in range(len(contours)):
        morpho = Morphology(n+1, contours[n], segment_dict['use_cellpose'])
        df_morpho_list.append(morpho.df)
    image_df = pd.concat(df_morpho_list)
      
    
    for key, value in subfolder_dict.items():
        df_ch_list, im, im_name= measure_image(value[0][img_n], value[1], 
                            ref_dict[key], contours, segment_dict['magnification'], 
                            segment_dict['pixel_size'], key)
            
        df_ch = pd.concat(df_ch_list)
        image_df = pd.merge(image_df, df_ch, on = 'Cell')
        image_df["Frame"] = img_n
    
    return image_df


def drop_cols(
        complete_df: pd.DataFrame,
        subfolder_dict: dict
)-> pd.DataFrame:
    """ Drops columns that store values not required by user."""
    
    for key, value in subfolder_dict.items():
        if value[1]['wants_foci'] == False:
            drop_foci = ["Total_foci_" + key,"Total_foci_area_" + key,
                         "Total_foci_mean_" + key, "Foci_area_fraction_" + key,
                         "Foci_cnt_" + key]
            complete_df.drop(columns = (drop_foci), inplace=True)
       
        if value[1]['wants_ktr'] == False:
             drop_ktr = [ "Mean_ring_" + key,"Median_ring_" + key, "Mean_ellipse_" + key,
                     "Median_ellipse_" + key,"Mean_Ring/Nucleus_" + key, "Median_Ring/Nucleus_" + key,
                     "Mean_Nucleus/Ring_" + key, "Median_Nucleus/Ring_" + key,
                     "Mean_Ellipse/Nucleus_" + key,"Median_Ellipse/Nucleus_" + key,
                     "Mean_Nucleus/Ellipse_" + key,  "Median_Nucleus/Ellipse_" + key,
                     "Cyto_ring_cnt_" + key]
                    
             complete_df.drop(columns = (drop_ktr), inplace=True)

    return complete_df


def analyze_dict(
        subfolder_dict: dict,      # dict of every channel 
        segment_dict: dict,        # dict of global parameters
        is_overtime: bool,
        condition: Optional[str],
        preview: bool,
        
)-> pd.DataFrame:
    
    """
    Given a dictionary containing information about each image channel analysis
    and the parameters used to perform cell segmentation, returns a dataframe
    containing the measurements and contours of each cell in every channel.
    This function is resposible for organizing all measuring funtions.
    """
    ref_dict = {}   # reference images for matching histograms
    for key, value in subfolder_dict.items():
        if value[2] == True:
            ch_segment = key
        ref_dict[key] = load_image(value[0][0]) if value[1]['match_hist'] else None

    all_df_list = []    #all dataframes to be concatenated   
    total_images = len((list(subfolder_dict.values())[0][0])) # number of imagens in the forlder
    # if running on preview mode, analyzes just the first 5 images of each folder
    total_images = 5 if preview == True and total_images>10 else total_images
    print(total_images, 'total_images') # esse print ta aqui pra conferencia só, depois apagar
    
    for img_n in range(total_images):      
        img_to_segment = subfolder_dict[ch_segment][0][img_n]
        
        cellpose =  segment_dict['use_cellpose']
        if cellpose == True:    #    calls cellpose
            contours = run_cellpose(img_to_segment, segment_dict['use_gpu'], 
                            segment_dict['diameter'], segment_dict['magnification'],
                            segment_dict['pixel_size'], segment_dict['shape'], 
                            segment_dict['eccentricity'],segment_dict['min_size'], 
                            segment_dict['max_size'],segment_dict['min_radius'], 
                            segment_dict['max_radius'], segment_dict['invert'], 
                            segment_dict['normalize'], segment_dict['net_avg'],
                            segment_dict['resample'], segment_dict['flow_threshold'],
                            segment_dict['mask_threshold'])
           
    
        else:   #   calls forNMA pipeline
            contours = fornma_contour_finding(img_to_segment, 
               magnification = segment_dict['magnification'],
               pixel_size = segment_dict['pixel_size'], rescale_intensity = segment_dict['rescale_intensity'],
               remove_bg = segment_dict['remove_bg'],radius_bg = segment_dict['radius_bg'],
               threshold = segment_dict['threshold'], offset = segment_dict['offset'], 
               blur= segment_dict['blur'], adjust_size= segment_dict['adjust_size'], 
               cut_edges = segment_dict['cut_edges'], shape= segment_dict['shape'], 
               eccentricity = segment_dict['eccentricity'],min_size= segment_dict['min_size'], 
               max_size= segment_dict['max_size'],min_radius= segment_dict['min_radius'], 
               max_radius= segment_dict['max_radius'],fast_detection = segment_dict['fast_detection'],
               weakly_labeled = segment_dict['weakly_labeled'])
        
        
        contours = [f for f in contours if len(f)>5] # remove contours with less than 5 points
        if len(contours) == 0:  # skips execution if there are no contours
            continue
        
        image_df = perform_measure(contours, img_n, subfolder_dict, ref_dict, segment_dict)
        all_df_list.append(image_df)
    
    if len(all_df_list) == 0:
       return False
    
    all_df = pd.concat(all_df_list) if len(all_df_list) >1 else all_df_list[0]# all images dataframe
    all_df["Condition"] = condition
    all_df["Overtime"] =  is_overtime
    all_df = all_df.reset_index(drop= True)
    all_df = drop_cols(all_df, subfolder_dict)  # drop columns 
    
    return all_df   
          
