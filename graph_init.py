#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 09:38:50 2022

@author: luiza

Prepairs dataframes for graph plotting
"""
import pandas as pd
from typing import List, Optional
import numpy as np
import math


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
        csv_list: List[pd.DataFrame],
        control: Optional[int],
)-> pd.DataFrame:
    
    """
        Gets a list of DataFrames and the information about the control group,
    position at the list, if present, and then prepairs the DataFrame for graph 
    plotting.
    """
    df_list = [pd.read_csv(f) for f in csv_list]
    conditions =[]
    nan_l = [] 
    for df in df_list:
        conditions.append(df['Condition'].iloc[0])
        nan = True if math.isnan(df['Condition'].iloc[0]) else False
        nan_l.append(nan)
 
    df_list = rename_conditions(conditions, csv_list, nan_l, df_list)
    
    for i in range(len(df_list)):
        df_list[i]["is_control"] = 'y' if i == control else 'n'
        
    final_df = pd.concat(df_list)
    if len(set(list(final_df['Overtime']))) >1:
        final_df['Overtime'] == False
        
    return final_df


# como chamar
df = graph_init(['/media/luiza/DATA/Doutorado/Imagens incucyte/img 4x/teste 12.csv' ,'/media/luiza/DATA/Doutorado/Imagens incucyte/img 4x/teste 11.csv'], 1)
