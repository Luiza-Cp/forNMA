# -*- coding: utf-8 -*-
"""
Created on Sun Aug  1 20:46:57 2021

@author: Luiza
"""

import matplotlib.pyplot as plt
import matplotlib.lines as lines
from Draggable_line import draggable_lines
import pandas as pd
import seaborn as sns
import numpy as np


df = pd.read_csv("C:\\Users\\Luiza Cherobini\\Desktop\\teste nucleos forNMA\\Eduardo\\40x Results.csv", sep = ";")




def plot_and_clean(df: pd.DataFrame) -> pd.DataFrame:   
    
    h_down = df.Area.quantile(0.05)
    h_up= df.Area.quantile(0.95)
    v_left = df.Error.min()
    v_right = df.Error.quantile(0.95)
    fig= plt.figure()
    ax = fig.add_subplot(sns.scatterplot(data=df, x="Error", y="Area")) 
    horizontal_up = draggable_lines(ax, "h",h_up)
    horizontal_down = draggable_lines(ax, "h", h_down)
    vertical_left = draggable_lines(ax, "v", v_left)
    vertical_right = draggable_lines(ax, "v", v_right)
    plt.show(block=True)
   
    from Draggable_line import line_coord_list
    plt.close()
    
    coord_tuples = []
    for i in range (len(line_coord_list[:-1])):
        if isinstance(line_coord_list[i], str) and isinstance(line_coord_list[i+1], float):
            coord_tuples.append((line_coord_list[i], line_coord_list[i+1]))
    
    coord_tuples = list(reversed(coord_tuples))
    
        
    for item in coord_tuples:
        if item[0] == "_line0":
            h_up  = item[1]
            break 
        
    for item in coord_tuples:
        if item[0] == "_line1":
            h_down = item[1]
            break 
    
    for item in coord_tuples:
        if item[0] == "_line2":
            v_left = item[1]
            break 
        
    for item in coord_tuples:
        if item[0] == "_line3":
            v_right = item[1]
            break 
    
    return h_down, h_up, v_left, v_right
    

def erase_df (df, h_down, h_up, v_left, v_right):
    df = df[df["Area"] < h_up]
    df = df[df["Area"] > h_down]
    df = df[df["Error"] > v_left]
    df = df[df["Error"] < v_right]
    
    frames = list(set(df.Frame.values))
    origin_folders = list(set(df.origin_folder.values))
    
    df_adjusted_list = []
    for o in origin_folders:
        for f in frames:
            df2 = df[(df["origin_folder"]== o) & (df["Frame"]== f)]
            df2["Cell"] = list(range(1, df2.shape[0]+1))
            df_adjusted_list.append(df2)
    
    df = pd.concat(df_adjusted_list)   
            
    return df

    #fig = plt.figure()  
    #ax = fig.add_subplot(111)
    
    
    
    
    
