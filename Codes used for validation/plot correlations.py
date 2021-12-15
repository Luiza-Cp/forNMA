#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 18:15:05 2021

@author: luiza
"""

import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import scipy
import os

def stats(col1: pd.DataFrame,
          col2: pd. DataFrame):
    """get correlation statistics form 2 data frames (single columns, but not a series).
    returns text to put at image and x position pfor text """
    pear_corr, p = scipy.stats.pearsonr(list([f[0] for f in list(col1.values)]),
                                       list([f[0] for f in list(col2.values)]))
    r_squared = scipy.stats.linregress(list([f[0] for f in list(col1.values)]),
                                       list([f[0] for f in list(col2.values)]))[2]
    pv = '= '+ str(p) if p > 0.001 else '> 0.001'
    text = 'R² = ' + str(round(r_squared, 3)) +'\n' + 'ρ = ' + str(round(pear_corr, 3)) +'\n' + 'p ' + pv
    x_text = max(col1.values)[0] - max(col1.values)[0]/5
    y_text =  max(col2.values)[0]/10
    
    return text, x_text, y_text

def lmplot_stats(df, hue):
    ''' separa os grupos de acordo com o hue para fazer estatísticas por subgrupo'''
    hue_items = list(set(df[hue].values))
    txt_list = []
    for item in hue_items:
        df_hue = df.loc[df[hue]== item]
        df_hue.drop(columns = [hue], inplace =True)
        text, _, _= stats(df_hue.iloc[:,0].to_frame(), df_hue.iloc[:,1].to_frame())
        txt_list.append(item +' ' + text)
    return txt_list


def plot_correlations(df1_path, df2_path, folder_save, hue):
    ''' Gets two paired dfs and align columns to be plotted against each other,
    then plots the correlations and calculates correlation statistics.'''
    
    
    
    df1 = pd.read_csv(df1_path)
    df2 = pd.read_csv(df2_path)
    
    #df1 = pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/forNMA (organized against IPP).csv')
    #df2 = pd.read_csv( '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/IPP (organized against forNMA).csv',         )
    
    df1.reset_index(inplace=True, drop=True)
    df2.reset_index(inplace=True, drop=True)
    
    cols = df1.columns.str.partition('_')
    cols = [f[0] for f in cols]
    remove =['Unnamed: 0', 'index', 'Image', 'Cell','X', 'Y', 'Mag', 'Condition']
    cols= [f for f in cols if f not in remove]
    #mag = df1.iloc[:,0]
    #mag.name = 'Magnification'
    hue_series = df1[hue]
    statistics = []
    for col in cols:
        c1 = df1[df1.columns[pd.Series(df1.columns).str.startswith(col)]]
        c2 = df2[df2.columns[pd.Series(df2.columns).str.startswith(col)]]
        
        to_plot = c1.join([c2, hue_series])
        
        
        plt.figure()
        sns.scatterplot(data=to_plot, x=to_plot.columns[0], y=to_plot.columns[1],
                        hue=hue, palette = 'Accent')
        
        sns.regplot(data=to_plot, x=to_plot.columns[0], y=to_plot.columns[1],
                       scatter = False, color ='gray')
        plt.title(col)
        
        text, x_text, y_text = stats(c1, c2)
        print (col +':\n',text)
         
        plt.text(x_text,y_text, text, fontsize = 'x-small')
          
        
        plt.savefig(os.path.join(folder_save, col + ' ' + c1.columns[0] + ' ' + c2.columns[0]) + '.svg')
        plt.savefig(os.path.join(folder_save, col + ' ' + c1.columns[0] + ' ' + c2.columns[0]) + '.png', dpi=300)
        
        aaa = lmplot_stats(to_plot, hue)
        
        statistics.append(aaa)
        statistics.append (col)
        g = sns.lmplot(x=to_plot.columns[0], y= to_plot.columns[1], col=hue,
                       hue=hue, data=to_plot, col_wrap=2, height=3)
    
    return statistics


aaa =plot_correlations(
    '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/forNMA (organized against IPP).csv',
    '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/IPP (organized against forNMA).csv',         
    '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/Gráficos2',
    'Condition_FORNMA')

