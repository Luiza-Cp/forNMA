#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 09:04:52 2022

@author: luiza
"""
import seaborn as sns
from matplotlib import pyplot as plt
import pandas as pd
from typing import Optional, List, Dict
import math
import numpy as np
import similaritymeasures
import os
import itertools

class Graphs:
    """ Class containing graph plotting funcrions. """
    
    def __init__(self, df, static_or_overtime, groups, times):
        """
        Atributes:
        
        self.df = dataframe containig all population information
        self.s_o = string correrpondig to graph type chosen by user, it is static or overtime. Will be s or o
        self.conditions: conditions to be plotted
        self.times: frames to be plotted
        """
        
        self.df= df
        self.s_o = static_or_overtime # interface devolve "s" ou "o"
        self.conditions = groups
        self.times = times
        self.fig_width=  self.calc_fig_width()
        self.subset =self.subset_df()
        
    def subset_df(self): 
        
       """ Subsets the self dataframe based on given groups and/or frames"""
       
       if self.s_o == 's':
           df = self.df[self.df['Condition'].isin(self.conditions)]
           if len(self.times) > 1:
               df = df[df['Frame'].isin(self.times)]
      
       else:
           df = self.df[self.df['Frame'].isin(self.times)]
           if len(self.conditions) > 1:
               df = df[df['Condition'].isin(self.conditions)]
      
         
       return df
   
    
    def calc_fig_width(self):
        """ based on s_o and in the amount of data to be plotted, finds the best figure width"""
        
        if self.s_o == 's':
            if len(self.conditions) <= 5:
                size = 2* len(self.conditions)
            elif len(self.conditions) <= 10:
                size = 10       # checar se 10 é um número ok ou se tem que ser mais
            else: 
                size = 1/3 * len(self.conditions) # checar se não fica ridículo 1/3
        else:
            if len(self.times) <= 5:
                size = 2* len(self.times)
            elif len(self.times) <= 10:
                size = 10       # checar se 10 é um número ok ou se tem que ser mais
            else: 
                size = 1/3 * len(self.times) # checar se não f
                   
        return size
    
    
    def violinplot(self, 
                   y: str, 
                   hue: Optional[str] = None):
         """  Plots a violin plot with all groups in a frame or all frames in a group"""
         
        
         x= "Condition" if self.s_o =='s' else 'Frame'
         fig= plt.figure(figsize=(self.fig_width, 6)) 
         sns.set_theme()
         ax = sns.violinplot(x=x, hue=hue, y=y, data=self.subset, inner=None, palette = "rainbow")
        
         return fig
     
        
    def boxplot(self, 
                y: str, 
                hue: Optional[str] = None): 
         
         x= "Condition" if self.s_o =='s' else 'Frame'
         fig= plt.figure(figsize=(self.fig_width, 6) ) 
         sns.set_theme()
         ax = sns.boxplot(x=x, y=y, hue=hue, data=self.subset, palette= "rainbow")
         
         return fig


    def stripplot(self, 
                  y: str, 
                  hue: Optional[str]= None): 
        
         x= "Condition" if self.s_o =='s' else 'Frame'
         fig= plt.figure(figsize=(self.fig_width, 6) ) 
         sns.set_theme()
         ax = sns.stripplot(x=x, y=y, hue=hue, data=self.subset, palette="rainbow")
         
         return fig    

    def barplot(self, 
                 y: str, 
                 hue: Optional[str] = None ): 
        
         x= "Condition" if self.s_o =='s' else 'Frame'
         fig= plt.figure(figsize=(self.fig_width, 6) ) 
         sns.set_theme()
         ax = sns.barplot(x=x, y=y, hue=hue, data=self.subset, palette="rainbow")
         
         return fig      


    def box_dot(self, 
                y: str, 
                hue: Optional[str] = None):
         
        x= "Condition" if self.s_o =='s' else 'Frame'
        fig= plt.figure(figsize=(self.fig_width, 6) ) 
        sns.set_theme()
        ax = sns.boxplot(x=x, y=y, hue=hue, data=self.subset, palette= "rainbow")   
        ax = sns.swarmplot(x=x, y=y, data=self.subset, color="gray", edgecolor="gray", size = 3)

        return fig


    def violin_dot(self, 
                   y: str, 
                   hue: Optional[str] = None):                   
         
        x= "Condition" if self.s_o =='s' else 'Frame'
        fig= plt.figure(figsize=(self.fig_width, 6) ) 
        sns.set_theme()
        ax = sns.violinplot(x=x, y=y, data=self.subset, inner=None, palette = "rainbow")
        ax = sns.swarmplot(x=x, y=y, data=self.subset, color="gray", edgecolor="gray", size = 3)
        
        return fig 


    def scatterplot(self,
                   x: str,        #add hue_norm and size_norm? e xy limits?
                   y: str,
                   hue: Optional[str] = None,
                   size: Optional[str] = None):
        

        """ 
        Groups the subset dataframe in conditions or frames or both and sends 
        each group to scatterplot functon. Rteturns a list of figures from all 
        scatterplots generated.
        """
        fig_list = []
        if len(self.conditions) >1 and len(self.times)>1:
            df_cond = self.subset.groupby('Condition')
            for cond_name, cond_group in df_cond:
                df_time = cond_group.groupby('Frame')
                for frame_name, frame_group in df_time:
                    txt = 'Scatterplot ' + str(cond_name) + ' frame ' + str(frame_name)
                    fig = self.plot_scatterplot(txt, frame_name, x, y, hue, size)
                    fig_list.append(fig)
        
        elif len(self.conditions) >1:
            df_cond = self.subset.groupby('Condition')
            for cond_name, cond_group in df_cond:
                txt = 'Scatterplot ' + str(cond_name)
                fig = self.plot_scatterplot(txt, cond_group, x, y, hue, size)
                fig_list.append(fig)
                
        elif len(self.times)>1:
            df_time = self.subset.groupby('Frame')
            for frame_name, frame_group in df_time:
                txt = 'Scatterplot Frame ' + str(frame_name)
                fig = self.plot_scatterplot(txt, df_time, x, y, hue, size)
                fig_list.append(fig)
       
        else:
            fig = self.plot_scatterplot("Scatterplot", x, y, hue, size)
            fig_list.append(fig)
        
        return fig_list
        
    # esse gráfico deve ser chaamdo n vezes de acordo com condições ou grupo ou ambos.
    # posso fazer uma função que já faz isso pra esse que tem que chamar vários, e armazenar eles em self.something
    def plot_scatterplot(self,
                    name: str,
                    group: pd.DataFrame,
                    x: str,      
                    y: str,
                    hue: Optional[str],
                    size: Optional[str]):
    
        """ Plots scatterlots and returns a figure containing the plot """
        fig= plt.figure(figsize=(self.fig_width, 6)) 
        sns.set_theme()
        group= group.apply(lambda x: x) 
               
        ax = sns.scatterplot(data=group, x=x, y=y, size = size, hue = hue, palette= 'rainbow') 
        sns.regplot(data=group, x=x, y=y,scatter = False, color ='gray')
        ax.set_title(name)
        plt.xticks(rotation=70)
        
        return fig
       

   # lineplot só parace pro overime 
    def lineplot(self, 
                 y: str, 
                 size: Optional[str] = None,
                 ci: Optional[int] = None,       # confidence interval
                 style: Optional[str] = None,    # tipo da linha de acordo comn o plot -> indica feature
                 hue: Optional[str] = None,
                 individual: bool = False):   # plotar cada item (se tem tracking) como uma linha -> Usar segment_ID

         
         x= 'Frame'
         units = "segment_ID" if individual ==True else None
         fig= plt.figure(figsize=(self.fig_width, 6) ) 
         sns.set_theme()
         ax = sns.lineplot(data=self.subset, x=x, y=y, hue= hue, style =style, 
                           size=size, ci=ci, legend="full", units=units, 
                           palette=  'rainbow') 
         plt.xticks(rotation=70)
           
         return fig
     
                   
    def rolling_average(self,
                        y: str,
                        n: str):          # number to group for moving average
      
         fig= plt.figure(figsize=(self.fig_width, 6) ) 
         conditions = list(set(list(self.subset["Condition"])))
         sns.set_theme()
     
         for c in conditions:
              df_plot = self.subset.loc[self.subset["Condition"] == c]  
              mean = df_plot.groupby("Frame")[y].mean()
              moving_df = mean.to_frame()
              moving_df["Frame"]=moving_df.index
              moving_df["Condition"]= [c]*moving_df.shape[0]
              moving_avg = moving_df[y].rolling(n).mean()
              moving_df[y] = moving_avg
              ax = sns.lineplot(data=moving_df, y=y, x = "Frame")
             
         plt.title("Rolling average "+ str(n) + " frames")
         plt.legend(conditions) 
         
         return fig
     
        
    def cpd(self,
             frames: List[int]):
         
    
        """ Measures the Cumulative Population Doubling of a cell population, given
        a dataframe and a list of timepoints"""
        
 
        dict_of_pd_lists = {}
        conditions = set(list(self.subset["Condition"])) 
        df = self.subset[self.subset["Frame"].isin(frames)]
        
        for c in conditions:
            df_plot = df[df["Condition"]== c]                # subsets each condition
            num_cell = df_plot["Frame"].value_counts()       # counts number at each time
            num_cell = list(num_cell.sort_index())      
            n_cell = [num_cell[n]  for n in frames]        # list with cell number
        
            pd_list = [0,]
       
            for n in range(len(n_cell)-1):
                fim = math.log(n_cell[n+1])
                ini = math.log(n_cell[n])
                doubling = (fim-ini)/math.log(2)
                if n >0:
                    doubling = doubling+ pd_list[n-1]
                pd_list.append(doubling)
        
            dict_of_pd_lists[c] = pd_list 
        
        fig= plt.figure(figsize=(self.fig_width, 6) ) 
        sns.set_theme()
        abc_list = []
        x= frames
        x.sort()
        x = [int(x[i]) for i in frames]
        for key, value in dict_of_pd_lists.items():
            ax = sns.lineplot(y =value, x = x, marker='s', sort= False)
        plt.legend(dict_of_pd_lists.keys())
        ax.set_title("Cumulative Population Doubling")  
        
        return fig
    

# como chamar!!!    
# devo testar também com tabelas maiores    
df = pd.read_csv('/home/luiza/Área de Trabalho/teste.csv')
g= Graphs(df, 'o', ['A', 'B'], [0, 1, 2, 3])

df2 = pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/Fornma_results.csv')
g= Graphs(df2, 's', ['Control', 'Gemcitabine', 'Etoposide', 'Taxol+carbo', 'Taxol'], [])
