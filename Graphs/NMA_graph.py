# -*- coding: utf-8 -*-
"""
Created on Fri Jun 25 10:05:41 2021

@author: Luiza

FUNCTIONS FOR NMA PLOTTING
"""

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


# função de calcular as porcentagens por quadrante e anotar
# NMA 3d

def thresh_NMA(df: pd.DataFrame):
    
    """ 
    Given a dataframe with the control goroup, returns the values for NMA 
    threshold- area mean and standard deviation and NII mean and standard 
    deviation - and the thcreshold ellipse.
    """
    df= df[(np.abs(stats.zscore(df["Area"])) < 2)]
    df= df[(np.abs(stats.zscore(df["NII"])) < 2)]
    mean_NII = df['NII'].mean()
    mean_a = df["Area"].mean()
    std_NII = df['NII'].std()
    std_a = df["Area"].std() 
    circle = np.linspace(0, 2*pi, 100) 
    return mean_NII, mean_a, std_NII, std_a, circle


def lines(mean_NII: str, 
          mean_a: str, 
          std_NII: str, 
          std_a: str):
    
    """ Given mean and standard deviation values, it returns lines coordinates"""
    
    rx= 2*std_NII
    ry = 2* std_a
    horizontal_x =  [mean_NII -rx,  mean_NII + 3*rx]
    horizontal_y_up = [mean_a +ry, mean_a +ry]
    horizontal_y_down= [mean_a-ry, mean_a-ry]
    vertical_x =  [mean_NII +rx,  mean_NII +rx]
    vertical_y=  [mean_a -ry,  mean_a + 3*ry]
    return horizontal_x, horizontal_y_up,horizontal_y_down, vertical_x, vertical_y


def find_area_NII_lims(df_dict: dict):
    
    """ Given a dictionary of dataFrames, establishes NMA graph limits"""
    
    max_a = []
    min_a = []
    max_NII = []
    min_NII = []
    for key, value in df_dict.items():
        df = value
        min_NII.append(df['NII'].min())
        min_a.append(df['Area'].min())
        df = df[(np.abs(stats.zscore(df["Area"])) < 3)]
        df = df[(np.abs(stats.zscore(df["NII"])) < 3)]
        max_a.append(df['Area'].max())
        max_NII.append(df['NII'].max())

    min_a = min(min_a) - ((sum(min_a)/len(min_a))*5) #ver se isso faz sentido 
    min_NII = min(min_NII) - 0.5

    return min_a,max(max_a), min_NII, max(max_NII)

def find_3d_lim(
        df_dict: dict,
        col: str 
)-> Tuple[float, float]:
    
    """ Given a dictionary of dataFrames, establishes Z coordinate limits"""
    
    if col == None:
        
        return None
    
    max_3d = []
    min_3d = []
    for key, value in df_dict.items():
        min_3d.append(value[col].min())
        df = value[(np.abs(stats.zscore(value[col])) < 3).all(axis=1)]
        max_3d.append(df[col].max())
    min_3d = min(min_3d) - (sum(min_3d)/len(min_3d))*0.3 #ver se isso faz sentido 
    
    
    return min_3d,max(max_3d) 
    


def find_norms(
        df_dict: dict,
        col: Optional[str]
)-> Tuple[int, int]:
    
    """ Given a dictionary of dataFrames, establishes hue, size and 3d plot limits"""
    print(col)
    if col != None:
       min_val = []
       max_val = []
       for key, value in df_dict.items():
           print (key)
           df= value
           df = df[(np.abs(stats.zscore(df[col])) < 3)]
           min_val.append(df[col].min())
           max_val.append(df[col].max())
       print(min_val, max_val)
       min_val = round(min(min_val), 0)
       max_val = round(max(max_val), 1)
       
     
       return (min_val, max_val)
   
    else: 
        
        return None
  

def plot_NMA_heatmap(
        name: str, 
        df: pd.DataFrame, 
        xh: float, 
        yh1: float, 
        yh2: float, 
        xv: float, 
        yv: float, 
        mean_NII: float, 
        mean_a: float, 
        std_NII: float, 
        std_a: float, 
        c: np.linspace, 
        lims: Tuple[float, float, float, float],
        hue: Optional[str] = None,
        size: Optional[str] = None,
        hue_norm: Optional[tuple] = None,
        size_norm: Optional[tuple] = None,
        col3:  Optional[str] = None,
        lim3d:  Optional[tuple] = None
        
  
):
    """  Plots a heatmap NMA with ignoring values passed as hue and size."""
    
    plt.rcParams['axes.facecolor'] = '#03051A'
    plt.figure()
    sns.displot(df, x="NII", y="Area", cmap= 'rocket', kind='kde', 
                    fill=True, thresh= None, levels = 60)
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='white', linewidth = 0.75)
    plt.ylim(lims[0], lims[1])
    plt.xlim(lims[2], lims[3])
    plt.title(name)
   # path_to_save = 'D:\\Triagem\\Results\\NEW\\Graphs\\NMA'
   # plt.savefig(os.path.join(path_to_save, 'Heatmap ' + name+ '.png'), dpi = 200)

 
    
def f_test(x: List[float],
           y: List[float]):
    """ Given two lists, performs f test statistic and returns the p value. """
    x = np.array(x)
    y = np.array(y)
    f = np.var(x, ddof=1)/np.var(y, ddof=1)     #calculate F test statistic 
    dfn = x.size-1  #define degrees of freedom numerator 
    dfd = y.size-1  #define degrees of freedom denominator 
    p = 1- stats.f.cdf(f, dfn, dfd)     #find p-value of F test statistic 
    
    return p     


def get_sample(df: pd.DataFrame,
               hue: Optional[str],
               size: Optional[str]
)-> Tuple[pd.DataFrame, bool]:
    """ 
    Finds statistcally significant samples from a population based on
    specific column values.
    """
    df_sample = df.sample(n = 200)
    p_NII_var = f_test(df['NII'].values, df_sample['NII'].values)
    p_a_var = f_test( df['Area'].values,df_sample['Area'].values)
    p_hue_var = None
    p_size_var = None
    p_NII_mean = stats.ttest_ind(df['NII'].values, df_sample['NII'].values)[1]
    p_a_mean = stats.ttest_ind( df['Area'].values,df_sample['Area'].values)[1]
    p_hue_mean = None
    p_size_mean = None
    
    if hue != None:
        p_hue_var = f_test(df[hue].values, df_sample[hue].values)
        p_hue_mean = stats.ttest_ind(df[hue].values, df_sample[hue].values)[1]
    if size != None:
        p_size_var = f_test(df[size].values, df_sample[size].values)
        p_size_mean = stats.ttest_ind(df[size].values, df_sample[size].values)[1]
    
    
    p_values = [p_NII_var, p_NII_mean, p_a_var, p_a_mean, p_hue_var, p_hue_mean, 
                p_size_var, p_size_mean]  
    
    for p in p_values:
        if p != None and p > 0.05:
            boolean = False
    else: 
        boolean = True
    
    return df_sample, boolean
    

def plot_NMA_200(
        name: str, 
        df: pd.DataFrame, 
        xh: float, 
        yh1: float, 
        yh2: float, 
        xv: float, 
        yv: float, 
        mean_NII: float, 
        mean_a: float, 
        std_NII: float, 
        std_a: float, 
        c: np.linspace, 
        lims: Tuple[float, float, float, float],
        hue: Optional[str] = None,
        size: Optional[str] = None,
        hue_norm: Optional[tuple] = None,
        size_norm: Optional[tuple] = None,
        col3:  Optional[str] = None,
        lim3d:  Optional[tuple] = None
):
   
    
    """ 
    Plots a sample NMA with hue and size given by user. To generate 
    samples, it calculates t test for means representative of the population
    and f test for variances, for each measure to be plotted.
    """
    
    df_sample, boolean = get_sample(df , hue, size)
    while boolean == False:
        df_sample, boolean = get_sample(df, hue, size)
    
    #make the values out of graph limits group at the limit (cytometry-like)
    df_sample.loc[df_sample['X'] == lims[3], 'X'] = lims[3]
    df_sample.loc[df_sample['Y'] == lims[1], 'Y'] = lims[1]
    
    plt.rcParams['axes.facecolor'] = 'white'
    fig,ax = plt.subplots(1)
    sns.scatterplot(data=df_sample, x="NII", y="Area", size =size,hue = hue,
                    hue_norm = hue_norm, size_norm = size_norm, ax=ax) 
    plt.plot( mean_NII+(2*std_NII)*np.cos(c) , mean_a+(2*std_a)*np.sin(c), color= 'black' )
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='black')
    plt.ylim(lims[0], lims[1])
    plt.xlim(lims[2], lims[3])
    plt.title(name)
   # path_to_save = 'D:\\Triagem\\Results\\NEW\\Graphs\\NMA'
   # plt.savefig(os.path.join(path_to_save, 'Sample ' +  name+ '.png'), dpi = 200)
 
def plot_NMA_dot(
        name: str, 
        df: pd.DataFrame, 
        xh: float, 
        yh1: float, 
        yh2: float, 
        xv: float, 
        yv: float, 
        mean_NII: float, 
        mean_a: float, 
        std_NII: float, 
        std_a: float, 
        c: np.linspace, 
        lims: Tuple[float, float, float, float],
        hue: Optional[str] = None,
        size: Optional[str] = None,
        hue_norm: Optional[tuple] = None,
        size_norm: Optional[tuple] = None,
        col3:  Optional[str] = None,
        lim3d:  Optional[tuple] = None,
        
              
):
    """ 
    Plots the NMA graph(scatterplot) with hue and size chosen by user. Same graph
    as the one define by plot_NMA_200, but without performing sampling.
    """
     #make the values out of graph limits group at the limit (cytometry-like)
    df.loc[df['X'] == lims[3], 'X'] = lims[3]
    df.loc[df['Y'] == lims[1], 'Y'] = lims[1]
    plt.rcParams['axes.facecolor'] = 'white'
    fig,ax = plt.subplots(1)
    sns.scatterplot(data=df, x="NII", y="Area", size = size, hue = hue,
                    hue_norm = hue_norm, size_norm = size_norm, ax=ax) 
    plt.plot(mean_NII+(2*std_NII)*np.cos(c) , mean_a+(2*std_a)*np.sin(c), color= 'black' )
    #el = Ellipse((mean_NII, mean_a), 4*std_NII, 4*std_a, angle=0, color="black", fill=False)
    #ax.add_patch(el)
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='black')
    plt.ylim(lims[0], lims[1])
    plt.xlim(lims[2], lims[3])
    plt.title(name)
    path_to_save = '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Aplicação poster/graphs'
    plt.savefig(os.path.join(path_to_save,'Scatter ' +  name+ '.svg'), dpi = 200)
    
    
    
       
NMA_plots_dict = {'heatmap': plot_NMA_heatmap, 
                  'sample': plot_NMA_200,
                  'dot': plot_NMA_dot,
                  '3d': 'func to plot a three dimensional NMA'}        
        

def NMA(df_dict: dict,
        ref: str, 
        type_of_plot: str,
        col1: Optional[str] = None,
        col2: Optional[str] = None,
        col3: Optional[str] = None,
        overtime: bool = False, 
        timelist: Optional[List[int]]= None,
):
    #esse df tem que ter o nome da pasta ou do csv como key e uma list [df, bool] como value
    # o bool é se é ou não controle
   """
   Given a dataframe dictionary, plots a NMA graph according to the chosen type.
   The avaluable types are: dot, sample and heatmap. If dot or sample are chosen,
   the user can assign two columns for hue and size of the dot.
   """
    
   # normalização das cols1 (hue_norm), 2 (size_norm) e 3 (limite do 3d)
   hue_norm = find_norms(df_dict, col1)
   size_norm = find_norms(df_dict, col2)
   lim3d = find_3d_lim(df_dict, col3)
   lims = find_area_NII_lims(df_dict)
   
   if overtime == True and ref == 't0':
       print('aa')
       for key, value in df_dict.items():
           t0 = value[value["Frame"] == 0]
           mean_NII, mean_a, std_NII, std_a, circle = thresh_NMA(t0)
           hx, hy1,hy2, vx, vy = lines(mean_NII, mean_a, std_NII, std_a)
           
           for time in timelist:
               df_plot = value[value["Frame"] == time]
               graph_name = str(key[:-8]) + ' Time '+ str(time)
               NMA_plots_dict[type_of_plot](graph_name, df_plot, hx, hy1, hy2, vx, vy, mean_NII, 
                                    mean_a, std_NII, std_a, circle, lims, col1, 
                                    col2, hue_norm,size_norm,col3, lim3d)
   
    
   for key, value in df_dict.items():
       if key == ref:
            mean_NII, mean_a, std_NII, std_a, circle = thresh_NMA(value)
            hx, hy1,hy2, vx, vy = lines(mean_NII, mean_a, std_NII, std_a)
           
  
   for key, value in df_dict.items():
       if overtime == True:
           for time in timelist:
               df_plot = value[value["Frame"] == time]
               graph_name = str(key[:-8]) + ' Time '+ str(time)
               NMA_plots_dict[type_of_plot](graph_name, df_plot, hx, hy1, hy2, vx, vy, mean_NII, 
                                    mean_a, std_NII, std_a, circle, lims, col1, 
                                    col2, hue_norm,size_norm,col3, lim3d)
           
       else:
           NMA_plots_dict[type_of_plot](key[:-8], value, hx, hy1, hy2, vx, vy, mean_NII, 
                                    mean_a, std_NII, std_a, circle, lims, col1, 
                                    col2, hue_norm,size_norm,col3, lim3d)
          
   return print("done")


## Não esquecer das duas funções que faltam!


# esse dicionário vem da interface também
# se for overtime, o controle é o primeiro tempo e o usuário escolhe
#qual ou quais tempos plotar. E nesse dic só entram os dfs a plotar

#se forem diferentes tto, o usuário seleciona qual é a condição controle
#e o dicionário vem com todos  


path = 'D:\\Triagem\\Results\\NEW'

df_dic= {}


for file in os.listdir(path):
    if file.endswith(".csv"):
        print(file)
        table = pd.read_csv(path+ '\\' + file) 
        for col in table.columns:
            if isinstance(table.iloc[0][col],str):
                 table = table.drop(columns =col)
        df_dic[file[:-4]] = table
       
#Types of plot: dot, sample, heatmap      
#Types of control: 
    # str representing the name of one specific group. If overtime will put all 
    # time values together to generate the control 
    # t0 -> initial time for each group

l = list(table["Frame"])
l= list(set(l))
l = [int(i) for i in l]
l.sort()
timelist = [int(l[0]), int(l[54]), int(l[101]), int(l[149]), int(l[176]), int(l[152]), int(l[188])]



t1= pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Aplicação poster/ct/c3_1_gResults.csv')
t2= pd.read_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Aplicação poster/ptx 1/d5_2_gResults.csv')

df_dict = {'Control': t1, 'Paclitaxel': t2}


NMA(df_dict, 'Control', 'dot', 'Total_foci_53bp1', 'Mean_Nucleus/Ellipse_erk', overtime = True, timelist = [0,21])

aa = list(df_dic.values())[0]
bb= aa[aa.Area > aa.Area.quantile(.75) ]
cc = aa[aa.Area < aa.Area.quantile(.25) ]
dd= aa[aa.NII > aa.NII.quantile(.75)]
ee = aa[aa.NII <aa.NII.quantile(.25)]

idx = []
idx.extend(bb.index.to_list())
idx.extend(cc.index.to_list())
idx.extend(dd.index.to_list())
idx.extend(ee.index.to_list())
to_drop = list(set(idx))
aa = aa.drop(aa.index[to_drop])
