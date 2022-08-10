#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 09:38:50 2022

@author: luiza

Prepairs dataframes for graph plotting
"""

import os
import pandas as pd
from typing import List, Optional


def check_column_names(df:pd.DataFrame, 
                       name: str):
    """
    Checks if DataFrame columns rare the ones expected by forNMA. If not,
    raises an error.
    """
    
    columns = ['Frame', 'Cell', 'X', 'Y', 'Area', 'Perimeter', 'Aspect',
               'Extent', 'Roundness', 'Radius_ratio', 'NII', 'FitEllipse_X',
               'FitEllipse_Y', 'FitEllipse_a', 'FitEllipse_b', 'FitEllipse_angle',
               'Condition', 'Overtime']
    
    if not all(item in df.columns for item in columns):
        raise ValueError ('The table '+ name+ ' does not have forNMA output column names. Rename your columns according to forNMA standard outputs and try again.')
    
    return None


def rename_conditions(
        conditions: List[str],
        csv_list: List[str],
        nan_l: List,
        df_list: List[pd.DataFrame]
)-> List[pd.DataFrame]:
    """ 
    Checks if conditions column has none or repeated values and ask the user
    for correction.
    """
    
    if len(set(conditions)) != len(conditions):
        # isso deve ser uma caixinha de msg na interface
        rename = input("There are repeated condition names. Do you want to rename?(y/n) If you chose to follow, forNMA will group the repeated conditions.")
    
    elif True in nan_l:
        rename = input("One ore more conditions do not have names. Do you want to rename? (y/n)")
       
    else: 
        rename = 'n'
        
    
    if rename.lower()  == 'y':
        conditions = []
        for csv in csv_list:
            new_name = input('Type the condition for ' + csv + ' :' )
            conditions.append(new_name)
        
        for i in range(len(df_list)):
            df_list[i]["Condition"] = conditions[i]
    
    elif True in nan_l:
        for i in range(len(df_list)):
            df_list[i]["Condition"] = i
    
    return df_list
   

    
def graph_init(
        csv_list: List[str],
        control: Optional[List[int]], # list index of all tabels that are controls (usually just one)
        
)-> pd.DataFrame:
    
    """
        Gets a list of DataFrames and the information about the control group,
    position at the list, if present, and then prepairs the DataFrame for graph 
    plotting.
    """
    df_list = [pd.read_csv(f) for f in csv_list]
    names = [os.basename(f) for f in csv_list]
    check = [check_column_names(f, g) for f, g in zip(df_list, names)]
        
    conditions =[]
    nan_l = [] 
    for df in df_list:
        conditions.append(df['Condition'].iloc[0])
        nan = True if df['Condition'].iloc[0] == False else False 
        nan_l.append(nan)
 
    df_list = rename_conditions(conditions, csv_list, nan_l, df_list)
    
    for i in range(len(df_list)):
        df_list[i]["is_control"] = 'y' if i in control else 'n'
        
    final_df = pd.concat(df_list)
    if len(set(list(final_df['Overtime']))) >1:
        final_df['Overtime'] == False
        
    return final_df

