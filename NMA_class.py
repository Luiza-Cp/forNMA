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
from NMA_draggable_line import draggable_lines




# na interface: usar um código que fornece uma caixinha pra digitar o sd ouu opções de linhagens celulares
# em ordem alfabética. Essa lista de linhagens pode ser atualizada pelo user
# os valores devem ser puxados de um csv (que abre em forma de dataFrame). c
#ALÉM DE CADA USUÁRIO PODER ADD SUAS LINHAGENS, A GENTE PODE DISPONIBILIZAR TABELAS ATUALIZADAS NO SITE






# Na funcçao graph init eu já tenho a infp de quem é controle. E é lá que a pesoa passa uma tabela de controle,
#logo, não preciso essa other_control e o controle eu tenho que fazer o subset de acordo com o is_control 
# se nenhuma do is control for true, ele avisa que é necessário ter uma condição controle (caixa de erro mesmo)


class NMA:
    """ Class for NMA graph plotting"""
                                                                # other_control: user-input dataframe with control group from another experiment
    def __init__(self, df, controls, sd, other_control = None): # control: Tuple[group_name, frame] - um deles pode ser None
        """                                     
        Atributes:
        
        self.df: pandas DataFrame with all value information
        self.coontrols: tuple containing gorup name and frmae. One of them can be none
        self.sd: float representing the standard deviation from mean to use for NMA threshold
        self.control_df: dataframe only with control group rows
        self.mean_NII: mean NII value of control gorup
        self.mean_a: mean area value of control gorup
        self.std_NII: distance from mean NII of the max or min value (the smallest is chosen)
        self.std_a: distance from mean area of the max or min value (the smallest is chosen)
        self.circle: numpy linespace for ellipse 
        self.h_x: horizontal line x value
        self.h_y_up: horixontal upper line y coordinates
        self.h_y_down: horixontal lower line y coordinates
        self.v_upx: vertical upper line X coordinates
        self.v_upy: vertical upper line y coordinates
        self.v_midx: vertical middle line x coordinates
        self.v_midy: vertical middle line y coordinates
        self.v_downx: vertical bottom left line x coordinates
        self.v_downy: vertical bottom lines y coordinates
        self.v_downx2: vertical bottom right line x coordinates
        self.graph_limits: tuple with min and maximum area and NII values within 3 standard deviations
        self.percentages: 
        """
        self.df = df
        self.controls = controls
        self.sd = sd
        self.control_df = self.subset_df(self.controls) #if other_control != None else other_control
        self.mean_NII, self.mean_a, self.std_NII, self.std_a, self.circle = self.calc_threshold_NMA()
        self.h_x, self.h_y_up,self.h_y_down = self.calc_lines()
        self.graph_box = dict(boxstyle="round,pad=0.3", fc="#dedcdc", alpha=0.7,  ec="#bdbbbb", lw=1)
        self.v_upx, self.v_upy, self.v_midx, self.v_midy, self.v_downx, self.v_downy, self.v_downx2 = self.calc_vertical_lines()
        self.graph_limits = self.calc_area_NII_lims()
        self.percentages = self.calc_all_percentages()

        
    def subset_df(self, condition_time_tuple):
        
       """ Subsets the self dataframe based in a condition or time frame or both.""" 
       if all(item is None for item in condition_time_tuple):
           df= self.df
       elif condition_time_tuple[1] is None:
            df = self.df.loc[self.df['Condition'] == condition_time_tuple[0]]
       elif condition_time_tuple[0] is None:
            df = self.df.loc[self.df['Frame'] == condition_time_tuple[1]]
       else:
            df = self.df.loc[self.df['Condition'] == condition_time_tuple[0]]
            df = df.loc[df['Frame'] == condition_time_tuple[1]]
         
       return df
       
        
    def calc_threshold_NMA(self):
       
        """ 
        sd: number of standard deviations from mean tht user has to provide for thresholding.
        Gets the control group from self.dataframe and returns the values for NMA 
        threshold- area mean and standard deviation and NII mean and standard 
        deviation removig 2 z-score outliers- and the thcreshold ellipse.
        """
        df = self.control_df
        df = df.loc[(np.abs(stats.zscore(df["Area"])) < self.sd)] # user mexe -> fazer algum esquema de dict com parametros para linhnagens 
        df = df.loc[(np.abs(stats.zscore(df["NII"])) < self.sd)]
        mean_NII = df['NII'].mean()
        mean_a = df["Area"].mean()
        std_NII = df['NII'].std() 
        std_a = df["Area"].std() 

        circle = np.linspace(0, 2*pi, 100) 
        
        return mean_NII, mean_a, std_NII, std_a, circle
    
    
    def calc_lines(self):
         """ Given mean and standard deviation values, it returns lines coordinates"""
            
         rx= self.sd* self.std_NII
         ry = self.sd* self.std_a
         horizontal_x =  [self.mean_NII -rx,  self.mean_NII + 3*rx]
         horizontal_y_up = [self.mean_a +ry, self.mean_a +ry]
         horizontal_y_down= [self.mean_a-ry, self.mean_a-ry]
        
         return horizontal_x, horizontal_y_up,horizontal_y_down
     
        
    def calc_area_NII_lims(self):
        
        """ Given a dataframe, establishes NMA graph limits"""
        
        df = self.df[(np.abs(stats.zscore(self.df["Area"])) < 3)]
        df = df[(np.abs(stats.zscore(df["NII"])) < 3)]
        max_a = df['Area'].max()
        min_a = df['Area'].min() - df['Area'].min()/3
        max_NII = df['NII'].max()
        min_NII = df['NII'].min() - df['NII'].min()/3
        
        return min_a,max_a, min_NII, max_NII
    
    
    def calc_vertical_lines(self):
       """
       Plots the control df with ellipse and horizontal lines for user to adjust
       the NMA threshold. Returns the new values.
       """
       %matplotlib qt
       upper_line_x = self.mean_NII + self.sd*self.std_NII
       upper_line_ys = [int(self.mean_a + self.sd * self.std_a), int(self.mean_a + (2+self.sd) * self.std_a)] 
       
       middle_line_x = upper_line_x +0.3 
       middle_line_ys = [int(self.mean_a - self.sd * self.std_a), upper_line_ys[0]]
       
       bottom_line_x = self.mean_NII
       bottom_line_ys =  [ int(self.mean_a -(1+ self.sd)* self.std_a) ,middle_line_ys[0]]
       
       bottom_line_x2 = self.mean_NII + 2.5*self.std_NII
       
       fig= plt.figure()
       ax = fig.add_subplot(sns.scatterplot(data=self.control_df, x="NII", y="Area", color = '#d8b8b8')) 
       ax.plot (self.h_x, self.h_y_up,self.h_x, self.h_y_down, color='black')
       ax.plot(self.mean_NII+(self.sd*self.std_NII)*np.cos(self.circle) , 
               self.mean_a+(self.sd*self.std_a)*np.sin(self.circle), color= 'black' )
       ax.set_title('Click to move the blue lines. Click again to release.')
       

       # ax.text(x, y, text, size, bbox)
       ax.text(upper_line_x-1, self.h_y_up[0]+0.3*self.sd*self.mean_a, 'LR', 
               size=10, bbox=self.graph_box)
       ax.text(upper_line_x+1, self.h_y_up[0]+0.3*self.sd*self.mean_a, 'LI', 
               size=10, bbox=self.graph_box)
       ax.text(self.mean_NII, self.mean_a, 'N', size=10, bbox=self.graph_box)
       ax.text(middle_line_x+1, self.mean_a, 'I', size=10, bbox=self.graph_box)
       ax.text(bottom_line_x-0.5, self.h_y_down[0]-0.1*self.sd*self.mean_a,
               'SR', size=10, bbox=self.graph_box)
       ax.text(bottom_line_x+0.5, self.h_y_down[0]-0.1*self.sd*self.mean_a, 'S', 
               size=10, bbox=self.graph_box)
       ax.text(bottom_line_x2+0.5, self.h_y_down[0]-0.1*self.sd*self.mean_a, 
               'SI', size=10, bbox=self.graph_box)
       
       upper_line =  draggable_lines(ax, 'v', upper_line_x, upper_line_ys)
       middle_line =  draggable_lines(ax, 'v', middle_line_x, middle_line_ys)
       bottom_line =  draggable_lines(ax, 'v', bottom_line_x, bottom_line_ys)
       bottom_line2 = draggable_lines(ax, 'v', bottom_line_x2, bottom_line_ys)
        
       plt.show(block=True)
       
       upper = upper_line.x
       middle = middle_line.x
       bottom = bottom_line.x
       bottom2 = bottom_line2.x
      
       plt.close('all')
  
       return [upper, upper], upper_line_ys, [middle, middle],middle_line_ys, [bottom, bottom], bottom_line_ys, [bottom2, bottom2]
  
    
    def get_NMA_classification_from_df(self, df):
        """Gets a dataframe and measures the percentage of nuclei in each NMA category."""
        
        total = df.shape[0]
        t= 100/total
        lr = df.loc[(df['Area'] >= self.h_y_up[0])& (df['NII'] < self.v_upx[0])].shape[0]
        li = df[(df['Area'] > self.h_y_up[0]) & (df['NII'] >= self.v_upx[0])].shape[0]
        n = df[(df['Area'] < self.h_y_up[0]) & (df['Area'] >= self.h_y_down[0]) & 
                   (df['NII'] < self.v_midx[0])].shape[0]
        i = df[(df['Area'] < self.h_y_up[0]) & (df['Area'] >= self.h_y_down[0]) & 
                   (df['NII'] > self.v_midx[0])].shape[0]
        sr = df[(df['Area'] < self.h_y_down[0]) & (df['NII'] < self.v_downx[0])].shape[0]
        s = df[(df['Area'] < self.h_y_down[0]) & (df['NII'] >= self.v_downx[0])
                  & (df['NII'] < self.v_downx2[0])].shape[0]
        si = df[(df['Area'] < self.h_y_down[0]) & (df['NII'] >= self.v_downx2[0])].shape[0]
        
        return  lr*t, li*t, n*t, i*t, sr*t, s*t, si*t
  
  
    def calc_all_percentages(self):
        """ Generates a dataframe containig the percentage relation of all NMA gorups. """
        
        has_controls = self.df['Condition'].iloc[0] != False and len(set(list(self.df['Condition']))) != 1 
        #não é falso (logo, tem valores ali) e tiver mais d 1 condição have_controls ==True
        
        df_percent_rows = []
        
        if has_controls ==True and self.df['Overtime'].loc[0] == True:
            # tem controles E tempo
            conditions = self.df.groupby('Condition')
            for name, group in conditions:
                frames = self.df.groupby("Frame")
                for frame_name, frame in frames:
                    lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(frame)
                    new_row = [name, frame_name, frame.shape[0], lr, li, n, i, sr, s, si ]
                    df_percent_rows.append(new_row)
       
        elif has_controls == True:
            #tem só controles?
            conditions = self.df.groupby('Condition')
            for name, group in conditions:
                lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(group)
                new_row = [name, False,group.shape[0], lr, li, n, i, sr, s, si ]
                df_percent_rows.append(new_row)
       
        elif self.df['Overtime'].loc[0] == True:
            # tem sṕ tempos?
            frames = self.df.groupby('Frame')
            for name, group in frames:
                lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(group)
                new_row = [False, name,group.shape[0], lr, li, n, i, sr, s, si ]
                df_percent_rows.append(new_row)
        
        else:
            #nada destacado
            lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(self.df)
            new_row = [False, False, self.df.shape[0], lr, li, n, i, sr, s, si ]
            df_percent_rows.append(new_row)
            
      
        percent_df = pd.DataFrame(df_percent_rows,
                    columns = ["Condition", "Frame", 'Total Cells', 'LR', 'LI', 'N', 'I', 'SR', 'S', 'SI'])
        
        return percent_df
          
        
    def f_test(self,
               x: List[float],
               y: List[float]):
        """ Given two lists, performs the f statistic teste and returns the p value. """
        x = np.array(x)
        y = np.array(y)
        f = np.var(x, ddof=1)/np.var(y, ddof=1)     # calculate F test statistic 
        dfn = x.size-1                              # define degrees of freedom numerator 
        dfd = y.size-1                              # define degrees of freedom denominator 
        p = 1- stats.f.cdf(f, dfn, dfd)             # find p-value of F test statistic 
        
        return p     
    
    def get_sample(self,
                   df: pd.DataFrame,
                   hue: Optional[str],
                   size: Optional[str]
    )-> Tuple[pd.DataFrame, bool]:
        """ 
        Finds statistcally significant samples from a population based on Area,
        NII and other specified column values.
        """
        df_sample = df.sample(n = 200)
        p_NII_var = self.f_test(df['NII'].values, df_sample['NII'].values)
        p_a_var = self.f_test( df['Area'].values,df_sample['Area'].values)
        
        p_NII_mean = stats.ttest_ind(df['NII'].values, df_sample['NII'].values)[1]
        p_a_mean = stats.ttest_ind( df['Area'].values,df_sample['Area'].values)[1]
        
        
        if hue != None:
            p_hue_var = self.f_test(df[hue].values, df_sample[hue].values)
            p_hue_mean = stats.ttest_ind(df[hue].values, df_sample[hue].values)[1]
        if size != None:
            p_size_var = self.f_test(df[size].values, df_sample[size].values)
            p_size_mean = stats.ttest_ind(df[size].values, df_sample[size].values)[1]
        if hue == None and size==None:
            p_hue_var = None
            p_hue_mean = None
            p_size_var = None
            p_size_mean = None
        
        p_values = [p_NII_var, p_NII_mean, p_a_var, p_a_mean, p_hue_var, p_hue_mean, 
                    p_size_var, p_size_mean]  
        
        for p in p_values:
            if p != None and p > 0.05:
                boolean = False
        else: 
            boolean = True
        
        return df_sample, boolean
     
        
    
    def plot_NMA_heatmap(self, 
                         subset_of_df: pd.DataFrame, 
                         title: str): 
        # plota pra uma condição sṕ. Cada condição adicional 
    # tem que chamar separado de novo. Isso é para UM plot
     
        """  Plots a heatmap NMA with ignoring values passed as hue and size."""
        
        #%matplotlib inline
        plt.rcParams['axes.facecolor'] = '#7e03ff'#'#03051A'
        fig, ax = plt.subplots()
        sns.kdeplot(data = subset_of_df, x="NII", y="Area", cmap= 'rainbow',  
                        fill=True, thresh= None, levels = 60, ax= ax)
        ax.plot (self.h_x, self.h_y_up,self.h_x, self.h_y_down, 
                 self.v_upx, self.v_upy, self.v_midx, self.v_midy,
                 self.v_downx, self.v_downy, self.v_downx2, self.v_downy,
                 color='white', linewidth = 0.75)
        
        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        ax.set_title(title)
        
       
        return fig 
    
       
    # na interface tem que aparecer as olções de grupos e/ou tempos pro user plotar
    # aí chama essa função com um de cada vez (um tempo e condição) 
    
    
    def plot_NMA_dot(self, 
                     condition_time_tuple: Tuple[Optional[str], Optional[int]],
                     subset_of_df: pd.DataFrame, 
                     hue: Optional[str] = None,
                     size: Optional[str] = None,
                     hue_norm: Optional[tuple] = None,
                     size_norm: Optional[tuple] = None,
                     sample: bool = False
                     ):
        """ 
        Plots the NMA graph(scatterplot) with hue and size chosen by user. Same graph
        as the one defined by plot_NMA_200, but without performing sampling.
        When sample is enabled, it performs t test statistics to get representative
        means of the population and f test for variances, for each measure to be plotted.
        It also doe not plot the percentages in each graph group.
        """
       
    #checar se ta tudo certo com esse iníco dos samples         
        if sample == True:
            df_sample, boolean = self.get_sample(subset_of_df , hue, size)
            while boolean == False:
                df_sample, boolean = self.get_sample(subset_of_df, hue, size)
       
            subset_of_df = df_sample
        
       #CONFERIR ESSAS COISAS DOS PERCENTS 
        if all(item is None for item in condition_time_tuple):
            print ('q')
            title = ' '
            percentages = None
        elif condition_time_tuple[0] == None:
            title = 'Frame ' + str(condition_time_tuple[1])
            percentages = self.percentages.loc[self.percentages['Frame'] == condition_time_tuple[1]]
        elif condition_time_tuple[1] == None:
            title =  str(condition_time_tuple[0])
            percentages = self.percentages.loc[self.percentages['Condition'] == condition_time_tuple[0]]
        else:
            title = condition_time_tuple[0] + ' Frame ' +  str(condition_time_tuple[0])
            percentages = self.percentages.loc[(self.percentages['Condition'] == condition_time_tuple[0])
                        & self.percentages['Frame'] == condition_time_tuple[1]]
            
        
        #make the values out of graph limits group at the limit (cytometry-like)
        subset_of_df.loc[subset_of_df['NII'] == self.graph_limits[3], 'NII'] = self.graph_limits[3] - 0.1
        subset_of_df.loc[subset_of_df['Area'] == self.graph_limits[1], 'Area'] = self.graph_limits[1] - 10
        plt.rcParams['axes.facecolor'] = 'white'
        
        fig,ax = plt.subplots(1)
        
        sns.scatterplot(data=subset_of_df, x="NII", y="Area", size = size, hue = hue,
                        hue_norm = hue_norm, size_norm = size_norm, ax=ax, palette = 'rainbow') 
        ax.plot(self.mean_NII+(self.sd*self.std_NII)*np.cos(self.circle) , 
                self.mean_a+(self.sd*self.std_a)*np.sin(self.circle), color= 'black' )
        
        ax.plot (self.h_x, self.h_y_up,self.h_x, self.h_y_down, 
                 self.v_upx, self.v_upy, self.v_midx, self.v_midy,
                 self.v_downx, self.v_downy,
                 self.v_downx2, self.v_downy, color='black')
        
        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        #ax.set_title(title)
        
        if isinstance(percentages, pd.DataFrame) or isinstance(percentages, pd.DataFrame) and sample== True:
            if percentages.shape[0]>1:
                percentages = percentages.drop(columns = ['Condition', 'Frame', 'Total Cells'])
                n = percentages.shape[0]
                percentages = (percentages.sum()/n).to_frame()
                percentages = percentages.transpose()
            print (percentages)
           
            ax.text(self.v_upx[0]-1, self.h_y_up[0]+0.3*self.sd*self.mean_a, 
                    str(round(percentages['LR'].iloc[0],2)),size=10, bbox=self.graph_box)
            ax.text(self.v_upx[0]+1, self.h_y_up[0]+0.3*self.sd*self.mean_a, 
                    str(round(percentages['LI'].iloc[0],2)), size=10, bbox=self.graph_box)
            ax.text(self.mean_NII, self.mean_a, str(round(percentages['N'].iloc[0],2)), 
                    size=10, bbox=self.graph_box)
            ax.text(self.v_midx[0]+1, self.mean_a, str(round(percentages['I'].iloc[0],2)),
                    size=10, bbox=self.graph_box)
            ax.text(self.v_downx[0]-0.7, self.h_y_down[0]-0.1*self.sd*self.mean_a,
                    str(round(percentages['SR'].iloc[0],2)), size=10, bbox=self.graph_box)
            ax.text(self.v_downx[0]+0.5, self.h_y_down[0]-0.1*self.sd*self.mean_a,
                    str(round(percentages['S'].iloc[0],2)), size=10, bbox=self.graph_box)
            ax.text(self.v_downx2[0]+0.5, self.h_y_down[0]-0.1*self.sd*self.mean_a, 
                    str(round(percentages['SI'].iloc[0],2)), size=10, bbox=self.graph_box)
        ax.set_title(title)   
                
        return fig                 
    
        

## COMO CHAMAR
       
nma_df_ignacio = pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/NMA_organizado.csv')
nma_df_fornma = pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/Fornma_results.csv') 




#ig= NMA(nma_df_ignacio, ('Control', None), 1.8)
fornma= NMA(nma_df_fornma, ('Control', None),1.8,)

t_for = fornma.plot_NMA_dot(('Taxol', None),fornma.subset_df(('Taxol', None)), hue = 'Total_foci_Dapi')
# =============================================================================
#c_ig = ig.plot_NMA_dot(ig.subset_df(('Control', None)), 'Control', hue = 'Aspect')
# c_ig_htm = ig.plot_NMA_heatmap(ig.subset_df(('Control', None)), 'Control')
# t_ig = ig.plot_NMA_dot(ig.subset_df(('Taxol', None)), 'Taxol', hue = 'Aspect')
# t_ig_htm =  ig.plot_NMA_heatmap(ig.subset_df(('Taxol', None)), 'Taxol')
# 
# c_for = fornma.plot_NMA_dot(fornma.subset_df(('Control', None)), 'Control fornma', hue = 'Aspect')
# c_for_htm =  fornma.plot_NMA_heatmap(fornma.subset_df(('Control', None)), 'Control fornma')
# t_for = fornma.plot_NMA_dot(fornma.subset_df(('Taxol', None)), 'Taxol fornma', hue = 'Aspect')
# t_fpr_htm = fornma.plot_NMA_heatmap(fornma.subset_df(('Taxol', None)), 'Taxolfornma')
# 
# =============================================================================

