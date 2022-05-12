#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 11 19:45:36 2022

@author: luiza

Code with auxiliary dataframe managing functions
"""

import os
from typing import List, Tuple, Optional
import pandas as pd 
pd.options.mode.chained_assignment = None  # default='warn'
from df_managing.clean_dataframe import plot_and_clean, erase_df

    
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


def split_dfs(
        complete_df: pd.DataFrame,
        ch_name_list: List[str]
)-> Tuple[pd.DataFrame, pd.DataFrame]:
    """ 
    Gets a complete DataFrame and separates it in the user output and the 
    dataframe with information to draw images.
    """
    col_list_cnt =['Frame', 'Cell', 'X', 'origin_folder']
    col_to_remove = []
    for key in ch_name_list:
        cols = ['Image_'+ key,'Image_name_'+ key, "Nuc_cnt_" + key, "Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key]
        col_list_cnt.extend(cols)
        cols_remove = ["Nuc_cnt_" + key,"Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key, "Unnamed: 0", "Image_" + key ]
        col_to_remove.extend(cols_remove)
    
    all_col = list(complete_df)
    col_results = [i for i in all_col if i not in col_to_remove]
    df_results = complete_df[col_results]
    col_draw = [i for i in col_list_cnt if i in all_col]
    df_draw = complete_df[col_draw]
    
    return df_results, df_draw


def organize_df_foci(frames: List[int],
                      overtime: List[bool],
                      condition: List[str],
                      image_names: List[str],
                      foci_dfs: List[Optional[pd.DataFrame]]
)-> List[pd.DataFrame]:
    
    """ 
    Gets a dataframe list and other information lists and create new 
    dataframe columns. Stores all dataframes in a list trat is returned.
    """
    
    assert len(frames) == len(overtime) == len(condition) == len(image_names) == len(foci_dfs)
    foci_df_list = []
    for i in range(len(foci_dfs)):
        if isinstance(foci_dfs[i], pd.DataFrame): 
            foci_dfs[i]['Frame'] = frames[i]
            foci_dfs[i]['Is_overtime'] = overtime[i]
            foci_dfs[i]['Condition'] = condition[i]
            foci_dfs[i]['Image_name'] = image_names[i]
            foci_df_list.append(foci_dfs[i])
    
    return foci_df_list



def get_foci_df(df_results: pd.DataFrame): 
     """ Generates foci df from dataframes stored inside df_results. """
   
     df_results_cols = list(df_results.columns)
     cols_channel = [f for f in df_results_cols if "Total_foci" in f]
   
     channels_with_foci = [f.replace('Total_foci_', '') for f in cols_channel]
     channels_with_foci = [f for f in channels_with_foci if "area" not in f]
     channels_with_foci = [f for f in channels_with_foci if "mean" not in f]
         
     frames = list(df_results['Frame'])
     overtime = list(df_results['Overtime'])
     condition = list(df_results['Condition'])
     
     dfs_foci_to_append = []
     for ch in channels_with_foci:
         image_names = list(df_results['Image_name_' + ch])
         foci_dfs = list(df_results['foci_df_' + ch])
         df_foci_list = organize_df_foci(frames, overtime, condition,
                                         image_names, foci_dfs)
         dfs_foci_to_append.extend(df_foci_list)
         #df_results.drop(columns= (["foci_df_"+ ch]), inplace=True)
     if len (dfs_foci_to_append) > 0:
         df_foci = pd.concat(dfs_foci_to_append)
         df_foci = df_foci[['Channel', 'Image_name', 'Frame', "Origin_nucleus", 
                            'Focus_number', 'Focus_mean_intensity',	'Focus_Area', 
                            'Focus_perimeter', 'Focus_centroid_x', 'Focus_centroid_y', 
                            'Condition', 'Is_overtime']] 
     else:
         df_foci= None
         
     return df_foci, df_results
    