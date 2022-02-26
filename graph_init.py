#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 09:38:50 2022

@author: luiza

Prepairs dataframes for graph plotting
"""
import pandas as pd
from typing import List, Optional
from matplotlib import pyplot as plt
import seaborn as sns
from NMA_draggable_line import draggable_lines
# o df que sai do graph init que vai para o graph class



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
        nan = True if df['Condition'].iloc[0] == False else False # aqui n
        nan_l.append(nan)
 
    df_list = rename_conditions(conditions, csv_list, nan_l, df_list)
    
    for i in range(len(df_list)):
        df_list[i]["is_control"] = 'y' if i == control else 'n'
        
    final_df = pd.concat(df_list)
    if len(set(list(final_df['Overtime']))) >1:
        final_df['Overtime'] == False
        
    return final_df

def gating(df: pd.DataFrame,
           conditions: List[str],
           x: int,
           y: int,
           frames: Optional[List[int]] = None
)-> pd.DataFrame:
   
    """
    Gets a dataframe with all conditions and frames (if present) and plots
    a scatterplot for region selection by user.
    Returns a dataframe with user-defined subset.
    """
    
    if len(conditions) > 0:
        df = df[df['Condition'].isin(conditions)]
    if len(frames) > 0:
        df = df[df['Frame'].isin(frames)]
    
    fig= plt.figure() 
    sns.set_theme()

    ax = sns.scatterplot(data=df, x=x, y=y, palette= 'rainbow') 
    ax.set_title('Click once to move the lines. Click again to release')
    plt.xticks(rotation=70)
    
    
    upper_line =  draggable_lines(ax, 'v', upper_line_x, upper_line_ys)
    middle_line =  draggable_lines(ax, 'v', middle_line_x, middle_line_ys)
    bottom_line =  draggable_lines(ax, 'v', bottom_line_x, bottom_line_ys)
    bottom_line2 = draggable_lines(ax, 'v', bottom_line_x2, bottom_line_ys)
    
    
    
# como chamar
df = graph_init(['/media/luiza/DATA/Doutorado/Imagens incucyte/img 4x/teste 12.csv' ,'/media/luiza/DATA/Doutorado/Imagens incucyte/img 4x/teste 11.csv'], 1)
