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


def plot_and_clean(df: pd.DataFrame,
                   is_cyto: bool,
) -> pd.DataFrame:   
    
    n_or_c = "Nuc_" if is_cyto==False else "Cyto_"
    title = 'Nuclei' if is_cyto==False else "Cells"
    
    h_down = df[n_or_c + 'Area'].quantile(0.05)
    h_up= df[n_or_c + 'Area'].quantile(0.95)
    v_left = df[n_or_c + 'Roundness'].min()
    v_right = df[n_or_c + 'Roundness'].quantile(0.95)
    fig= plt.figure()
    ax = fig.add_subplot(sns.scatterplot(data=df, x=n_or_c + 'Roundness', y=n_or_c + 'Area')) 
    horizontal_up = draggable_lines(ax, "h",h_up)
    horizontal_down = draggable_lines(ax, "h", h_down)
    vertical_left = draggable_lines(ax, "v", v_left)
    vertical_right = draggable_lines(ax, "v", v_right)
    
    plt.title(title +" outlier removal. Click and move to adjust the gate. Cliick again to relaese")
    
    plt.show(block=True)
   
    
    plt.close('all')
   
    
    h_up =horizontal_up.XorY
    h_down =horizontal_down.XorY
    v_left = vertical_left.XorY
    v_right = vertical_right.XorY
    
    
    return h_down, h_up, v_left, v_right
    

def erase_df (df, h_down, h_up, v_left, v_right, is_cyto):
    n_or_c = "Nuc_" if is_cyto==False else "Cyto_"
    df = df[df[n_or_c + 'Area'] < h_up]
    df = df[df[n_or_c + 'Area'] > h_down]
    df = df[df[n_or_c + 'Roundness'] > v_left]
    df = df[df[n_or_c + 'Roundness'] < v_right]
    
    frames = list(set(df.Frame.values))
    origin_folders = list(set(df.origin_folder.values))
    
    df_adjusted_list = []
    for o in origin_folders:
        for f in frames:
            df2 = df[(df["origin_folder"]== o) & (df["Frame"]== f)]
            df2["Cell"] = list(range(1, df2.shape[0]+1))
            df_adjusted_list.append(df2)
    if len(df_adjusted_list)>1:
        df = pd.concat(df_adjusted_list)   
    else:
        df = None
    return df

    
    
    
    
