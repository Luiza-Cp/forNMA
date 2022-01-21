#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 15:40:07 2022

@author: luiza
"""
#as infos disso estção anotadas no caderno, conferir ali 
from scipy import stats
import math 
import os
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import ticker
import seaborn as sns
import numpy as np  
from math import pi
from typing import Optional, List, Tuple
from matplotlib.patches import Ellipse

# devo fazer NMA 3d???
# porcentagens de pixels que colocalizma faz sentido pro edu???




class NMA:
    """ Class for NMA graph plotting"""
    
    def __init__(self, df, controls): # control: Tuple[group_name, frame] - um deles pode ser None
        """ 
        Atributes:
        
        self.df: pandas DataFrame with all value information
        self.coontrols: tuple containing gorup name and frmae. One of them can be none
        self.control_df: dataframe only with control group rows
        self.mean_NII: mean NII value of control gorup
        self.mean_a: mean area value of control gorup
        self.std_NII: distance from mean NII of the max or min value (the smallest is chosen)
        self.std_a: distance from mean area of the max or min value (the smallest is chosen)
        self.circle: numpy linespace for ellipse 
        self.h_x: horizontal line x value
        self.h_y_up: horixontal upper line y value
        self.h_y_down: horixontal lower line y value
        self.v_x: vertical line x value
        self.v_y: vertical line y value
        self.graph_limits: tuple with min and maximum area and NII values within 3 standard deviations
        """
        self.df = df
        self.controls = controls
        self.control_df = self.subset_df(self.controls)
        self.mean_NII, self.mean_a, self.std_NII, self.std_a, self.circle = self.calc_threshold_NMA()
        self.h_x, self.h_y_up,self.h_y_down, self.v_x, self.v_y = self.calc_lines()
        self.graph_limits = self.calc_area_NII_lims()
        #self.df_percentages = self.calc_percentages()
        #self.dot_plots = []
        #self.heatmap_plots: {}
        #self.sample_plost: []
       
        
    def subset_df(self, condition_time_tuple):
        
       """ Subsets the self dataframe based in a condition or time frame or both.""" 
       
       if condition_time_tuple[1] is None:
            df = self.df.loc[self.df['Condition'] == condition_time_tuple[0]]
       elif condition_time_tuple[0] is None:
            df = self.df.loc[self.df['Frame'] == condition_time_tuple[1]]
       else:
            df = self.df.loc[self.df['Condition'] == condition_time_tuple[0]]
            df = df.loc[df['Frame'] == condition_time_tuple[1]]
         
       return df
       
        
       
    def calc_threshold_NMA(self):
        
        """ 
        Gets the control group from self.dataframe and returns the values for NMA 
        threshold- area mean and standard deviation and NII mean and standard 
        deviation removig 2 z-score outliers- and the thcreshold ellipse.
        """
        df = self.control_df
        df = df.loc[(np.abs(stats.zscore(df["Area"])) < 1.5)]
        df = df.loc[(np.abs(stats.zscore(df["NII"])) < 1.5)]
        mean_NII = df['NII'].mean()
        mean_a = df["Area"].mean()
        std_NII = df['NII'].std() 
        std_a = df["Area"].std() 

        print( std_NII, mean_NII, std_a, mean_a)
        
        circle = np.linspace(0, 2*pi, 100) 
        
        return mean_NII, mean_a, std_NII, std_a, circle
    
    def calc_lines(self):
         """ Given mean and standard deviation values, it returns lines coordinates"""
            
         rx= 2* self.std_NII
         ry = 2* self.std_a
         horizontal_x =  [self.mean_NII -rx,  self.mean_NII + 3*rx]
         horizontal_y_up = [self.mean_a +ry, self.mean_a +ry]
         horizontal_y_down= [self.mean_a-ry, self.mean_a-ry]
         vertical_x =  [self.mean_NII +rx,  self.mean_NII +rx]
         vertical_y=  [self.mean_a -ry,  self.mean_a + 3*ry]
         return horizontal_x, horizontal_y_up,horizontal_y_down, vertical_x, vertical_y
        
        
    def calc_area_NII_lims(self):
        
        """ Given a dataframe, establishes NMA graph limits"""
        
        df = self.df[(np.abs(stats.zscore(self.df["Area"])) < 3)]
        df = df[(np.abs(stats.zscore(df["NII"])) < 3)]
        max_a = df['Area'].max()
        min_a = df['Area'].min() - df['Area'].min()/3
        max_NII = df['NII'].max()
        min_NII = df['NII'].min() - df['NII'].min()/3
        
        return min_a,max_a, min_NII, max_NII
    
    
    
   # def calc_percentages(self):
        
    
    
    
    
    
    ##BAH EU N SEI SE ISSO TA CERTO

    def plot_NMA_heatmap(self, 
                         subset_of_df: pd.DataFrame, 
                         title: str): 
        # plota pra uma condição sṕ. Cada condição adicional 
    # tem que chamar separado de novo. Isso é para UM plot
     
        """  Plots a heatmap NMA with ignoring values passed as hue and size."""
        
       
        plt.rcParams['axes.facecolor'] = '#7e03ff'#'#03051A'
        fig, ax = plt.subplots()
        sns.kdeplot(data = subset_of_df, x="NII", y="Area", cmap= 'rainbow',  
                        fill=True, thresh= None, levels = 60, ax= ax)
        ax.plot (self.h_x, self.h_y_up,self.h_x, self.h_y_down, self.v_x, self.v_y, color='white', linewidth = 0.75)
        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        ax.set_title(title)
       
        return ax 
    
       
    # na interface tem que aparecer as olções de grupos e/ou tempos pro user plotar
    # aí chama essa função com um de cada vez (um tempo e condição) - acho que iss?
    
    
    def plot_NMA_dot(self, 
                     subset_of_df: pd.DataFrame, 
                     title: str,
                     hue: Optional[str] = None,
                     size: Optional[str] = None,
                     hue_norm: Optional[tuple] = None,
                     size_norm: Optional[tuple] = None,
                     ):
        """ 
        Plots the NMA graph(scatterplot) with hue and size chosen by user. Same graph
        as the one define by plot_NMA_200, but without performing sampling.
        """
        #make the values out of graph limits group at the limit (cytometry-like)
        
        subset_of_df.loc[subset_of_df['NII'] == self.graph_limits[3], 'NII'] = self.graph_limits[3] - 0.1
        subset_of_df.loc[subset_of_df['Area'] == self.graph_limits[1], 'Area'] = self.graph_limits[1] - 10
        plt.rcParams['axes.facecolor'] = 'white'
        
        fig,ax = plt.subplots(1)
        
        sns.scatterplot(data=subset_of_df, x="NII", y="Area", size = size, hue = hue,
                        hue_norm = hue_norm, size_norm = size_norm, ax=ax, palette = 'rainbow') 
        ax.plot(self.mean_NII+(2*self.std_NII)*np.cos(self.circle) , 
                self.mean_a+(2*self.std_a)*np.sin(self.circle), color= 'black' )
        #el = Ellipse((mean_NII, mean_a), 4*std_NII, 4*std_a, angle=0, color="black", fill=False)
        #ax.add_patch(el)
        ax.plot (self.h_x, self.h_y_up,self.h_x, self.h_y_down, self.v_x, self.v_y, color='black')
        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        ax.set_title(title)
        
        
        return ax                  
        
        
  # adicionar as porcentagems (escritas no gráfico)
# pensar se retorno elas na tabea tbm
     
       
       
nma_df_ignacio = pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/NMA_organizado.csv')
nma_df_fornma = pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/Fornma_results.csv') 

ig= NMA(nma_df_ignacio, ('Control', None))
fornma= NMA(nma_df_fornma, ('Control', None))

c_ig = ig.plot_NMA_dot(ig.subset_df(('Control', None)), 'Control', hue = 'Aspect')
c_ig_htm = ig.plot_NMA_heatmap(ig.subset_df(('Control', None)), 'Control')
t_ig = ig.plot_NMA_dot(ig.subset_df(('Taxol', None)), 'Taxol', hue = 'Aspect')
t_ig_htm =  ig.plot_NMA_heatmap(ig.subset_df(('Taxol', None)), 'Taxol')

c_for = fornma.plot_NMA_dot(fornma.subset_df(('Control', None)), 'Control fornma', hue = 'Aspect')
c_for_htm =  fornma.plot_NMA_heatmap(fornma.subset_df(('Control', None)), 'Control fornma')
t_for = fornma.plot_NMA_dot(fornma.subset_df(('Taxol', None)), 'Taxol fornma', hue = 'Aspect')
t_fpr_htm = fornma.plot_NMA_heatmap(fornma.subset_df(('Taxol', None)), 'Taxolfornma')

