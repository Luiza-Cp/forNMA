# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 14:25:56 2021

@author: Luiza

File that puts all functions together 
"""


import os
from typing import List
from analyze_multichannel import analyze_dict, saving_images,split_dfs, save_dfs
import tempfile
import pandas as pd 
pd.options.mode.chained_assignment = None  # default='warn'
from clean_dataframe import plot_and_clean, erase_df
   



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
                     headless: bool,
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

def run(path_to_save: str,
        ch_name_list: List[str],
        ch_path_list: List[str],
        ch_with_nuc: str,
        overtime: bool,
        parameter_list: List[str],
        conditions: List[str],
        segment_dict: dict,
        wants_to_save: bool,
        headless: bool  = False
)-> None:
    """
    Gets all user inputs and applies them to analyze allfolders and subfolders.
    Then filters results, draws images (if requested) and saves all results.
    """
    
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
    
    complete_df = filter_dataframe(temp_dir)
    
    # now the complete df is splitted in smaller ones and saved
    df_results, df_draw = split_dfs(complete_df, ch_name_list) 
    save_dfs(df_results, path_to_save)
    if wants_to_save == True: # save images
        saving_images(df_draw, path_to_save, ch_name_list, segment_dict['use_cellpose']) # aqui dentro eu crio os pkl dos foci
    
    temp_dir.cleanup()
    
    return None