# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 14:25:56 2021

@author: Luiza

File that puts all functions together 
"""


import os
from typing import List, Tuple
from analyze_multichannel import analyze_dict, saving_images,split_dfs, save_dfs
import tempfile
import pandas as pd 
pd.options.mode.chained_assignment = None  # default='warn'
from clean_dataframe import plot_and_clean, erase_df
   

def rename_channel_parameters(channel_parameters: dict) -> dict:
    """ Renames parameter dictionary keys"""
    
    min_size = channel_parameters['foci_min_size'] if channel_parameters['foci_min_size'] != False else None
    max_size = channel_parameters['foci_max_size'] if channel_parameters['foci_max_size'] != False else None
    min_int = channel_parameters['foci_min_int'] if channel_parameters['foci_min_int'] != False else None
    max_int = channel_parameters['foci_max_int'] if channel_parameters['foci_max_int'] != False else None
    prominence = channel_parameters['foci_prominence'] if channel_parameters['foci_prominence'] != False else None
    
    new_dict = {'rescale_intensity': channel_parameters['rescale_intensity'],
                'remove_bg': channel_parameters["remove_background"], 
                'radius_bg': channel_parameters['rolling_ball_radius'],
                'match_hist': channel_parameters['match_hisograms'],
                'wants_ktr':channel_parameters['measure_translocation'],
                'ring_size': channel_parameters['ring_size'],
                'use_ellipse': channel_parameters['use_ellipse'], 
                'wants_foci': channel_parameters['measure_foci'],
                'foci_min_size': min_size,
                'foci_max_size': max_size,
                'foci_min_int': min_int,
                'foci_max_int': max_int,
                'foci_proeminence': prominence
                }
    
    return new_dict

def adjust_parameters(parameters_dict)-> Tuple[bool, str, List[str], List[str], str, dict ]:
    """
    Adjusts dictionary from interface or parameters.toml to establish new variable names.
    """
    path_to_save = parameters_dict['path_to_save']
    ch_name_list = parameters_dict['names']
    ch_path_list = parameters_dict['channel_path_list']
    ch_with_nuc = parameters_dict['channel_with_nuclei']
    overtime = parameters_dict['overtime']
    parameter_list = [f for f in parameters_dict['channel_parameters'].values()][0:len(ch_path_list)]
    parameter_list =[ rename_channel_parameters(f) for f in parameter_list]
    conditions = parameters_dict['subfolder_names']
    save_images = parameters_dict['save_images']
    
    shape = parameters_dict['segmentation']['shape'] if parameters_dict['segmentation']['shape'] != False else None
    eccentricity = parameters_dict['segmentation']['eccentricity'] if parameters_dict['segmentation']['eccentricity'] != False else None
    min_size = parameters_dict['segmentation']['minimum_size'] if parameters_dict['segmentation']['minimum_size'] != False else None
    max_size = parameters_dict['segmentation']['maximum_size'] if parameters_dict['segmentation']['maximum_size'] != False else None
    min_radius = parameters_dict['segmentation']['minimum_radius'] if parameters_dict['segmentation']['minimum_radius'] != False else None
    max_radius = parameters_dict['segmentation']['maximum_radius'] if parameters_dict['segmentation']['maximum_radius'] != False else None



    segment_dict = {'magnification': parameters_dict['segmentation']['magnification'],
                    'pixel_size':parameters_dict['segmentation']['pixel_size'] ,
                    'rescale_intensity': parameters_dict['segmentation']['rescale_intensity'],     
                    'remove_bg': parameters_dict['segmentation']['remove_background'],      
                    'radius_bg': parameters_dict['segmentation']['rolling_ball_radius'],              
                    'threshold': parameters_dict['segmentation']['forNMA']['threshold'],
                    'offset': parameters_dict['segmentation']['forNMA']['offset'],                    
                    'blur': parameters_dict['segmentation']['forNMA']['smooth'],               
                    'adjust_size': parameters_dict['segmentation']['forNMA']['adjust_size'],      
                    'cut_edges': parameters_dict['segmentation']['forNMA']['cut_edges'], 
                    'shape':  shape,
                    'eccentricity': eccentricity,       
                    'min_size': min_size, 
                    'max_size': max_size,
                    'min_radius': min_radius,
                    'max_radius': max_radius,
                    'fast_detection': parameters_dict['segmentation']['forNMA']['find_low_intensity_nucleus'],
                    'weakly_labeled': parameters_dict['segmentation']['forNMA']['weakly_labeled'],
                    'use_cellpose':parameters_dict['segmentation']['cellpose']['use_cellpose'], 
                    'invert': False,               
                    'normalize': True,
                    'diameter': parameters_dict['segmentation']['cellpose']['diameter'], 
                    'net_avg': True,                
                    'resample': True,              
                    'flow_threshold':parameters_dict['segmentation']['cellpose']['flow_threshold'], 
                    'mask_threshold': parameters_dict['segmentation']['cellpose']['mask_threshold'],
                    'use_gpu': parameters_dict['segmentation']['cellpose']['use_gpu'],
        }

    return save_images, path_to_save, ch_name_list, ch_path_list, ch_with_nuc, overtime, parameter_list, conditions, segment_dict
    
    


def create_folder_dict( 
        ch_name_list: List[str],
        ch_path_list: List[str],
        ch_with_nuc: str,
        parameter_list: List[str]
)-> dict:
    """
    Returns the subfolders and a dictionary for a folder where:
        key = channel name 
        values = [ list, dict, bool] 
            values[0]: a list with all folders in a given channel (each folder can be a field or a treatment condition, for example)
            values[1]: the param_dict for this channel
            values[2]: boolean indicating if user wants to perform segmentation in this chanel
    """
    folder_dict = {}
    for i in range(len(ch_name_list)):
        seg = ch_with_nuc == ch_path_list[i]
        subfolders = sorted((os.listdir(ch_path_list[i])))
        folder_dict[ch_name_list[i]] = [[os.path.join(ch_path_list[i], f) for f in subfolders],
                                           parameter_list[i],seg]
    
    return subfolders, folder_dict


def create_subfolder_dict(folder_dict: dict,
                          iterator: int
)-> dict:
    """
    Returns a dictionary for each subfolder where:
        key =  channel name
        values = [list, dictionary, bool]
            values[0]: list of every item inside folder (list of images)
            values[1]: dictionary os parameters (param_dict)
            values[2]: boolean indicating if user wants to perform segmentation in this chanel
    """
    subfolder_dict ={}   
    for key, value in folder_dict.items():
        files = sorted(os.listdir(value[0][iterator]))
        files = [os.path.join(value[0][iterator], f) for f in files ]
        subfolder_dict[key] = [files, value[1], value[2]]
   
    return subfolder_dict  


def check_size(ch_dict: dict)-> bool:
    """ Sorts files and checks if all file_lists have the same size. """
    
    len_files = len (list(ch_dict.values())[0][0])      #first file list
    for key, value in ch_dict.items():
        value[0] = sorted(value[0])
        if len(value[0]) != len_files:
            
            return False
        
    return True
 
    
def filter_dataframe(temp_dir: str,
                     headless: bool = False,
)-> pd.DataFrame:
    """ 
    From all folders in a temporary directory, opens all dataframes stored as
    pickle objects, appends all dataframes and applies user manual filtering. 
    If headless, does not open graph to be adjusted and filtering is not applied.
    """
    complete_df = pd.DataFrame()
    for file in os.listdir(temp_dir.name):
        path_to_temp_csv = os.path.join(temp_dir.name, file) 
        df = pd.read_pickle(path_to_temp_csv)
        df["origin_folder"]= file
        complete_df = complete_df.append(df)
    
    if headless == False:    
        h_down, h_up, v_left, v_right = plot_and_clean(complete_df) 
        complete_df = erase_df(complete_df, h_down, h_up, v_left, v_right)   

    return complete_df


def run(parameters_dict: dict,
        headless: bool  = False
)-> None:
    """
    Gets all user inputs and applies them to analyze allfolders and subfolders.
    Then filters results, draws images (if requested) and saves all results.
    """
    
    wants_to_save, path_to_save, ch_name_list, ch_path_list, ch_with_nuc, overtime, parameter_list, conditions, segment_dict = adjust_parameters(parameters_dict)
    subfolders, folder_dict = create_folder_dict(ch_name_list, ch_path_list,
                                                  ch_with_nuc, parameter_list)
    
    # tests whether number of conditions match the number os subfolders
    if len(conditions) != len(subfolders):
        conditions = [False] * len(subfolders)
        
    temp_dir = tempfile.TemporaryDirectory()
       
    for i in range(len(subfolders)):
        subfolder_dict = create_subfolder_dict(folder_dict, i)
        if not check_size(subfolder_dict):
            raise("The folders contain different image number")
        total_df = analyze_dict(subfolder_dict, segment_dict, overtime, conditions[i]) # ju usa esse pra remover outliers
        filename = os.path.basename(subfolders[i]) + '.zip'
        # adds files to temporary directory
        total_df.to_pickle(os.path.join(temp_dir.name, filename))
    
    
    complete_df = filter_dataframe(temp_dir, headless)
    
    # now the complete df is splitted in smaller ones and saved
    df_results, df_draw = split_dfs(complete_df, ch_name_list) 
    save_dfs(df_results, path_to_save)
    if wants_to_save == True: # save images
        saving_images(df_draw, path_to_save, ch_name_list, segment_dict['use_cellpose']) # aqui dentro eu crio os pkl dos foci
    
    temp_dir.cleanup()
    
    return None