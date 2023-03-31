
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 09:47:14 2022

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
import matplotlib.patches as mp
from matplotlib.widgets import Slider, Button, RadioButtons

class NMA:
    """ Class for NMA graph plotting"""
                                                              
    def __init__(self, df, sd):
        """                                     
        Atributes:
        
        self.df: pandas DataFrame with all value information
        self.sd: float representing the standard deviation from mean to use for NMA threshold
        self.mean_NII: mean NII value of control group
        self.mean_a: mean area value of control group
        self.std_NII: distance from mean NII of the max or min value (the smallest is chosen)
        self.std_a: distance from mean area of the max or min value (the smallest is chosen)
        self.circle: numpy linespace for ellipse 
        self.h_x: horizontal line x value
        self.h_y_up: horizontal upper line y coordinates
        self.h_y_down: horizontal lower line y coordinates
        self.v_upx: vertical upper line X coordinates
        self.v_upy: vertical upper line y coordinates
        self.v_midx: vertical middle line x coordinates
        self.v_midy: vertical middle line y coordinates
        self.v_downx: vertical bottom left line x coordinates
        self.v_downy: vertical bottom lines y coordinates
        self.v_downx2: vertical bottom right line x coordinates
        self.graph_limits: tuple with min and maximum area and NII values within 3 standard deviations
        self.percentages: dataframe with cell percentages at each NMA group
        """
        self.df = df
        self.sd = sd
        self.control_df = self.get_control_df()
        self.mean_NII, self.mean_a, self.std_NII, self.std_a, self.circle = self.calc_threshold_NMA()
        self.graph_limits = self.calc_area_NII_lims()
        self.ellipse = self.adjust_ellipse()
        self.h_x, self.h_y_up,self.h_y_down = self.calc_lines()
        self.graph_box = dict(boxstyle="round,pad=0.3", fc="#dedcdc", alpha=0.7,  ec="#bdbbbb", lw=1)
        self.v_upx, self.v_upy, self.v_midx, self.v_midy, self.v_downx, self.v_downy, self.v_downx2 = self.calc_vertical_lines()
        self.percentages = self.calc_all_percentages()
       
        
    def get_control_df(self):
        """ Checks if table has control gourps. If not, raise an error."""
        
        if 'is_control' not in self.df.columns: # is the column there?
            raise ValueError ('There is no column indicating controls.')
        elif 'y' not in list(self.df['is_control']): # are there any controls?
            raise ValueError ("There are no controls indicated in yor table.")
        else:
            return self.df.loc[self.df['is_control'] == 'y']
            
        
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
          Gets the control group from self.control_df and returns the values for 
        NMA threshold - area mean and standard deviation and NII mean and standard 
        deviation removig 2 z-score outliers - and the linespace for ellipse.
          If overtime, it will use all time frames for control gorup. 
        """
        
        df = self.control_df
        df = df.loc[(np.abs(stats.zscore(df["Area"])) < 2)] # removes 2 z-scores 
        df = df.loc[(np.abs(stats.zscore(df["NII"])) < 2)]
        mean_NII = df['NII'].mean()
        mean_a = df["Area"].mean()
        std_NII = df['NII'].std() 
        std_a = df["Area"].std() 

        circle = np.linspace(0, 2*pi, 100) 

        return mean_NII, mean_a, std_NII, std_a, circle
    
    
    def calc_lines(self):
         """ 
         Given mean and standard deviation values, it returns lines coordinates
         self.sd: number of standard deviations from mean that user has to provide 
         for thresholding.
         """
            
         rx= self.sd* self.std_NII # number of stantadard deviations * standard deviation
         ry = self.sd* self.std_a
         horizontal_x=[self.mean_NII -rx,  self.mean_NII + 3*rx]
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
    
    def adjust_ellipse(self): 
        """
        Plots a control sample of 500 units (or all control if smaller) with the
        calculated ellipse for user adjustments.
        """
        
        df = self.control_df
        df = df.loc[(np.abs(stats.zscore(df["Area"])) < 3)] # removes 3 z-scores 
        df = df.loc[(np.abs(stats.zscore(df["NII"])) < 3)]

                
        sns.set_theme()
        sns.set_palette('rainbow', 9)
        df_sample, boolean = self.get_sample(df, None, None)
        
        while boolean == False: # if any of variances is not preserved, repeat 
            df_sample, boolean = self.get_sample(df, None, None)
          
       
        fig, ax = plt.subplots()
        sns.scatterplot(data=df_sample, x="NII", y="Area", ax=ax)
      
        ellipse = mp.Ellipse((self.mean_NII,self.mean_a), 
                           2*self.sd*self.std_NII,
                           2*self.sd*self.std_a, 
                           ec = 'black', fc=None, fill = False)
        ax.add_patch(ellipse)
        ax.set_title('Adjust here the threshold ellipse')
        plt.subplots_adjust(left=0.25, bottom=0.25)
        
        axsd = plt.axes([0.1, 0.25, 0.0225, 0.63])
        axsd_slider = Slider(
            ax=axsd,
            label="SD",
            valmin=0,
            valmax=5,
            valinit = self.sd,
            orientation="vertical"
        )
        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        def update(val):
            self.sd = axsd_slider.val
            ellipse.set_height(2*self.sd*self.std_a) 
            ellipse.set_width(2*self.sd*self.std_NII)
            fig.canvas.draw_idle()
 
        axsd_slider.on_changed(update)
        plt.show(block = True)
   
        return None
        
    
    def calc_vertical_lines(self):
       """
       Plots the control df with ellipse and horizontal lines for user to adjust
       the NMA threshold. Returns the new values.
       """
       #%matplotlib qt
       upper_line_x = self.mean_NII + 1.5*self.sd*self.std_NII 
       upper_line_ys = [int(self.mean_a + self.sd * self.std_a), int(self.mean_a + (2+self.sd) * self.std_a)] 
       
       middle_line_x = upper_line_x 
       middle_line_ys = [int(self.mean_a - self.sd * self.std_a), upper_line_ys[0]]
       
       bottom_line_x = self.mean_NII
       bottom_line_ys =  [ int(self.mean_a -(1+ self.sd)* self.std_a) ,middle_line_ys[0]]
       
       bottom_line_x2 =  upper_line_x 
       
       sns.set_theme()
       sns.set_palette('rainbow', 9)
       fig= plt.figure()
       df_sample, boolean = self.get_sample(self.df , None, None)
       while boolean == False:
           df_sample, boolean = self.get_sample(self.df, None, None)
         
      
       ax = fig.add_subplot(sns.scatterplot(data=df_sample, x="NII", y="Area",)) 
      
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
       
       ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
       ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
       
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
                frames =group.groupby("Frame")
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
                   size: Optional[str],
                   n: int = 500
    )-> Tuple[pd.DataFrame, bool]:
        """ 
        Finds statistcally significant samples from a population based on Area,
        NII and other specified column values.
        """
        
        if df.shape[0] < n:
            return df, True
        
        df_sample = df.sample(n = n)
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
        p_values = [f for f in p_values if f != None]
        
        if np.any(np.array(p_values) < 0.05):
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
        sns.kdeplot(data = subset_of_df, x="Total_foci_Dapi", y="Area", cmap= 'rainbow',  
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
                     sample: bool = False
                     ):
        """ 
        Plots the NMA graph(scatterplot) with hue and size chosen by user. Same graph
        as the one defined by plot_NMA_200, but without performing sampling.
        When sample is enabled, it performs t test statistics to get representative
        means of the population and f test for variances, for each measure to be plotted.
        It also doe not plot the percentages in each graph group.
        """
       
  
        if sample == True:
            df_sample, boolean = self.get_sample(subset_of_df , hue, size)
            while boolean == False:
                df_sample, boolean = self.get_sample(subset_of_df, hue, size)
       
            subset_of_df = df_sample
        
       
        if all(item is None for item in condition_time_tuple):
            title = ' '
            percentages = None
        elif condition_time_tuple[0] is None:
            title = 'Frame ' + str(condition_time_tuple[1])
            percentages = self.percentages.loc[self.percentages['Frame'] == condition_time_tuple[1]]
        elif condition_time_tuple[1] is None:
            title =  str(condition_time_tuple[0])
            percentages = self.percentages.loc[self.percentages['Condition'] == condition_time_tuple[0]]
        else:
            title = condition_time_tuple[0] + ' Frame ' +  str(condition_time_tuple[1])
            percentages = self.percentages.loc[(self.percentages['Condition'] == condition_time_tuple[0])]
            percentages = percentages.loc[percentages['Frame'] == condition_time_tuple[1]]
            
        
        #make the values out of graph limits group at the limit (cytometry-like)
        subset_of_df.loc[subset_of_df['NII'] == self.graph_limits[3], 'NII'] = self.graph_limits[3] - 0.1
        subset_of_df.loc[subset_of_df['Area'] == self.graph_limits[1], 'Area'] = self.graph_limits[1] - 10
        plt.rcParams['axes.facecolor'] = 'white'
        
        fig,ax = plt.subplots(1)
        
        hue_norm = None
        size_norm = None
        if hue is not None:
            df_hue = self.df[(np.abs(stats.zscore(self.df[hue].fillna(self.df[hue].mean()))) < 3)]
            hue_norm = (df_hue[hue].min(), df_hue[hue].max())
        if size is not None:
            df_size = self.df[(np.abs(stats.zscore(self.df[size].fillna(self.df[size].mean()))) < 3)]
            size_norm = (df_size[size].min(), df_size[size].max())
        

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

    def calc_gates(self):
        """
        Plots the Control NMA graph and lets the user gate its data over it.
        Returns a dataframe with selected values
        """
        x0 = self.control_df['NII'].quantile(.05)
        xf = self.control_df['NII'].quantile(.95)
        y0 = self.control_df["Area"].quantile(.05)
        yf = self.control_df["Area"].quantile(.95)
        
        x_quantile = self.control_df['NII'].quantile(.2)
        y_quantile = self.control_df['Area'].quantile(.2)
        
        sns.set_theme()
        fig= plt.figure()
        ax = fig.add_subplot(sns.scatterplot(data=self.control_df, x="NII", y="Area", color = '#d8b8b8')) 
        ax.plot (self.h_x, self.h_y_up,self.h_x, self.h_y_down, color='black')
        ax.plot(self.mean_NII+(self.sd*self.std_NII)*np.cos(self.circle) , 
                self.mean_a+(self.sd*self.std_a)*np.sin(self.circle), color= 'black' )
       
        ax.plot (self.h_x, self.h_y_up,self.h_x, self.h_y_down, 
                 self.v_upx, self.v_upy, self.v_midx, self.v_midy,
                 self.v_downx, self.v_downy,
                 self.v_downx2, self.v_downy, color='black')
        
        ax.set_title('Click to move the blue lines. Click again to release.')
        
       
        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        
        df=self.control_df
        x = 'NII'
        y = 'Area'
        upper_line =  draggable_lines(ax, 'h', int(yf), [int(df[x].min()- x_quantile), int(df[x].max()+ x_quantile)])
        bottom_line = draggable_lines(ax, 'h',y0,  [int(df[x].min()-x_quantile), int(df[x].max()+ x_quantile)])
        left_line = draggable_lines(ax, 'v', x0, [int(df[y].min()-y_quantile), int(df[y].max()+ y_quantile)])
        right_line = draggable_lines(ax, 'v',xf, [int(df[y].min()-y_quantile), int(df[y].max()+y_quantile)])
        
        plt.show(block = True)
         
        upper = upper_line.x
        bottom = bottom_line.x
        left = left_line.x
        right =  right_line.x
        
        plt.close('all') 
        
        df2 = df.loc[(df[y] < upper) & (df[y] > bottom)]
        df2 = df2.loc[(df2[x] < right) & (df2[x] > left)]
        
        return df2

    def percentages_overtime(self, 
                             group: str,
                             frames: Optional[List[int]] = None):
        
        """ Given a group and an optional list of frames, plots the
        NMA groups percentage overtime"""
        
        df = self.percentages[self.percentages['Frame'].isin(frames)] if frames is not None else self.percentages
        df.drop(columns = ['Total Cells'], inplace = True)
        df = df.loc[df['Condition'] == group]
        df.set_index('Frame', inplace= True)
        sns.set_palette('rainbow',7)
        fig, ax = plt.subplots()
        df.plot(kind='bar', stacked=True, ax= ax)
        ax.set_title('NMA groups')
         
        return fig



# ===========Como chamar=======================================================
# 
df3 = pd.read_csv('/media/luiza/DATA/Triagem Denise/Triagem 2/results tables/Adjusted complete table.csv')
# 
df3=df3.loc[df3['time'] != '01d10h56m']
df3=df3.loc[df3['time'] != '00d10h56m']
df3['is_control'] = np.where(
    df3['Condition'] == 'C', 'y', 'n')
nma = NMA(df3, 2)
# =============================================================================
