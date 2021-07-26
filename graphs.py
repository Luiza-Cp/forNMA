# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 09:24:41 2021

@author: Luiza
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
from statannot import add_stat_annotation

def violinplot(x: str, 
               y: str, 
               df: pd.DataFrame,
               hue: Optional[str],
               dodge: Optional[bool], 
               overtime: bool
):
    
        
     ax = sns.violinplot(x=x, y=y, data=df, inner=None, palette = "rocket_r")
     return ax
    
def boxplot(x: str, 
            y: str, 
            df: pd.DataFrame, 
            hue: Optional[str],
            dodge: Optional[bool],
            overtime: bool
): # não aceitae hue no overtime
     if overtime == True:
         hue= None
     ax = sns.boxplot(x=x, y=y, hue=hue, data=df, palette="rocket_r")
     return ax

def stripplot(x: str, 
               y: str, 
               df: pd.DataFrame, 
               hue: Optional[str],
               dodge: Optional[bool],
               overtime: bool
): 
     if overtime == True:
         hue = None
         dodge = False
     ax = sns.stripplot(x=x, y=y, hue=hue, data=df, palette="rocket_r", dodge=dodge)
     return ax    

def barplot(x: str, 
             y: str, 
             df: pd.DataFrame, 
             hue: Optional[str],
             dodge: Optional[bool],
             overtime: bool
): 
     if overtime == True:
         hue = None
     ax = sns.barplot(x=x, y=y, hue=hue, data=df, pallete = 'rocket_r')
     
     return ax    


def box_dot(x: str, 
            y: str, 
            df: pd.DataFrame,
            hue: Optional[str],
            dodge: Optional[bool],
            overtime: bool
):
     
    ax = boxplot(x, y, df, overtime)      
    ax = sns.swarmplot(x=x, y=y, data=df, color="gray", edgecolor="gray", size = 3)

    return ax


def violin_dot(x: str, 
               y: str, 
               df: pd.DataFrame, 
               hue: Optional[str],
               dodge: Optional[bool],
               overtime: bool
):
     
    ax = violinplot(x, y, df, overtime)      
    ax = sns.swarmplot(x=x, y=y, data=df, color="gray", edgecolor="gray", size = 3)

    return ax 

categorical_dict = {'violin': violinplot, 'box': boxplot, 'strip': stripplot,
                   'bar': barplot, 'box_dot': box_dot, 'violin_dot': violin_dot}



def categorical_plots(plot_type: str, 
                      x: str, 
                      y: str, 
                      df: pd.DataFrame, 
                      hue: Optional[str] = None,
                      dodge: Optional[bool] = None,
                      overtime: bool = False,
                      path_save: Optional[str] = None,
):
    """ plt any categorical plot, given a dataframe and the variables to be plotted"""
    sns.set_theme()
    if overtime ==True:
        conditions = set(list(df["Condition"]))
        for c in conditions:
            df_plot = df[df["Condition"]== c]
            plt.figure(figsize = ((len(set(list(df['Time'])))+1)/3 ,6))
            ax = categorical_dict[plot_type]('Time',y, df_plot, hue, dodge, overtime)
            plt.xticks(rotation=70)
            plt.tight_layout()
            plt.title(str(c))
    else:
        
        plt.figure(figsize = (10,6))
        ax = categorical_dict[plot_type](x, y, df, hue, dodge, overtime)
        plt.xticks(rotation=70)
        plt.tight_layout()
        plt.title(plot_type)
    if path_save != None:
        plt.savefig(os.path.join(path_save, plot_type + '.png'), dpi=200)
        

def area_between_curves(x: List[float],
                        y: List[float], 
                        x_ref: List[float], 
                        y_ref: List[float]): 
   
    # prepare the data into np arrays for similaritymeasures
    curve = np.zeros((len(x), 2))
    curve[:, 0] = x
    curve[:, 1] = y     
    
    ref = np.zeros((len(x), 2))
    ref[:, 0] = x_ref
    ref[:, 1] = y_ref    
    area = similaritymeasures.area_between_two_curves(curve, ref)

    return area


def abc_plots(dict_to_plot: Dict, 
              ref: str, 
              x: str,
              y: str,
              path_save: Optional[str] = None
):
    """
    PLots area between curves 

    Parameters
    ----------
    dict_to_plot : Dict[str:pd.DataFrame]
        Key must be the condition name and value must be a dataframe to plot
    ref : str
        Is the name of the condition to be plotted against 
    x : str
        X variable, usually is the frame (time)
    y : str
        Y variable

    Returns
    -------
    matplotlib figures

    """

    if '/' in y:
        z = y.replace('/', '_')
    else: 
        z = y
    condition_list = list(dict_to_plot.keys()) 
    n_subplots = round(math.sqrt(len(condition_list)-1),1)        # sqrt to find number of subplots
    if n_subplots % 2 == 0:
         rows = int(n_subplots)
         cols = int(n_subplots)
    else:
         rows = int(round(n_subplots))
         cols = int(round(n_subplots) + 1)
    ref_item = dict_to_plot[ref]
    dict_to_plot.pop(ref)
    areas = [0,]
    areas_dict = {ref : 0}
    fig, axs = plt.subplots(nrows=rows, ncols=cols, squeeze=False, figsize = (rows*7, cols*4))
    axs1D= axs.flatten()
    i = 0
    for key, value in dict_to_plot.items():         # plots axes in one figure
         print (key)
         area = area_between_curves(list(value[x]), list(value[y]), 
                                    list(ref_item[x]), list(ref_item[y]))
         areas_dict[key] = area
         key = (key, area)
         axs1D[i] = sns.lineplot(data=value, y=y, x=x, ax=axs1D[i], color='#741E58', sort=False)
         axs1D[i] = sns.lineplot(data=ref_item, y=y, x=x, ax=axs1D[i], color='#F5AA83', sort= False)
         axs1D[i].set_title(key[0])
         axs1D[i].fill_between(value[x], value[y], ref_item[y], alpha= 0.3, 
                                   where=(value[y]> ref_item[y]),interpolate = True,
                                   color='#741E58')
         axs1D[i].fill_between(value[x], value[y], ref_item[y], alpha= 0.3, 
                                   where=(value[y]< ref_item[y]),interpolate = True,
                                   color='#F5AA83')
         axs1D[i].legend([key[0], ref])
         i = i + 1
    if path_save != None:
        plt.savefig(os.path.join(path_save, "Area Between Curves " + z + '.png'), dpi=200)
    if len(areas) > 0:      # plots barplot for area between curves
        abc_df = pd.DataFrame(columns=["Condition", "Area Between Curves"])
        abc_df["Condition"] = list(areas_dict.keys())
        abc_df["Area Between Curves"] = list(areas_dict.values())
        plt.figure(figsize=(12,6))
        ax = sns.barplot(x = "Condition", y= "Area Between Curves", data=abc_df)
        
        if path_save != None:
            plt.savefig(os.path.join(path_save, "Area Between Curves " + z + " columns.png"), dpi=200)

    
def lineplot(x: str, 
             y: str, 
             df: pd.DataFrame, 
             size: Optional[str] = None,
             ci: Optional[int] = None, #confidence interval
             style: Optional[str] = None,   #tipo da linhad e acordo comn o plot
             split: bool = False,
             abc: bool = False,
             ref_abc: Optional[str] = None,
             individual: Optional[bool] = None,    #plotar cada item (se tem tracking) como uma linha
             path_save: Optional[str] = None
             #pra plotar cada um por linha ele tem que dividir por algum marcador do tracking que
             #tenho que adicionar
             #posso mudar isso pra gerar várias figuras acho que é mais fácil
): 

      fsize = round(len(set(list(df[x])))/12, 0) 
      if fsize< 12:
            fsize =12
      plt.figure(figsize=(fsize,6))
      sns.set_theme()
      if split ==True:
        conditions = set(list(df["Condition"]))
        n_subplots = round(math.sqrt(len(conditions)),1)
        if n_subplots % 2 == 0:
            rows = n_subplots
            cols = n_subplots
        else:
            rows = round(n_subplots)
            cols = round(n_subplots) + 1
                    # CONTINUAR ESSA FUNÇÂO
                
            
      else:
        ax =sns.lineplot(data=df, x=x, y=y, hue='Condition', style =style, 
                                 size=size, ci=ci, legend="full", units=individual) 
        plt.xticks(rotation=70)
        plt.tight_layout()
               
     
      if path_save != None:
           if '/' in y:
               z = y.replace('/', '_')
           else:
                z= y
           plt.savefig(os.path.join(path_save, z + '.png'), dpi=200)
        

          
 
def scatterplots(x: str,        #add hue_norm and size_norm? e xy limits?
                 y: str,
                 df: pd.DataFrame,
                 z: Optional[str] = None,
                 hue: Optional[str] = None,
                 size: Optional[str] = None,
                 overtime: bool = False,
                 timelist: Optional[List[int]] = None,
                 split_by: bool = False, #separar grupos em gráficos diferentes (não como hue)
                 path_save: Optional[str] = None): 
    
    # adicionar a condiç~eo do split == Ture para separar em diferentes gráficos    
    sns.set_theme()
    if overtime == True:
        for time in timelist:
             plt.figure(figsize = (10,6))
             df_plot = df[df["Frame"]== time] ###subset aqui, pra seguir a func
             ax = sns.scatterplot(data=df_plot, x=x, y=y, size = size, hue = hue) 
             plt.xticks(rotation=70)
             plt.tight_layout()
             plt.legend()
             plt.title('Frame ' + str(time))
   
    if z is not None:
        a =[] 
        #plot here 3d graph with hue ans size - não sei como faz ainda
    else:
        plt.figure(figsize = (10,6))
        ax = sns.scatterplot(data=df, x=x, y=y, size = size, hue = hue) 
        plt.xticks(rotation=70)
        plt.tight_layout()
    if path_save != None:
        plt.savefig(os.path.join(path_save, x + ' x ' +y + '.png'), dpi=200)
        
 


def cpd (df: pd.DataFrame,
        timelist: List[int],
        abc: bool = True, #area between curves -> fazer separado pra poder chamar em outras func
        path_save: Optional[str] = None
):
    """ Measures the Cumulative Population Doubling of a cell population, given
    a dataframe and a list of timepoints"""
    
    dict_of_pd_lists = {}
    conditions = set(list(df["Condition"])) 
    
    for c in conditions:
        df_plot = df[df["Condition"]== c]       # subsets each condition
        num_cell = df_plot["Frame"].value_counts()      # counts number at each time
        num_cell = list(num_cell.sort_index())      
        n_cell = [num_cell[n]  for n in timelist]       # list with cell number
    
        pd_list = [0,]
   
        for n in range(len(n_cell)-1):
            fim = math.log(n_cell[n+1])
            ini = math.log(n_cell[n])
            doubling = (fim-ini)/math.log(2)
            if n >0:
                doubling = doubling+ pd_list[n-1]
            pd_list.append(doubling)
    
        dict_of_pd_lists[c] = pd_list 
    
    sns.set_theme()
    plt.figure (figsize = (12,6))
    abc_list = []
    x= list(set(list(df["Frame"])))
    x.sort()
    x = [int(x[i]) for i in timelist]
    for key, value in dict_of_pd_lists.items():
        ax = sns.lineplot(y =value, x = x, marker='s', sort= False)
    plt.legend(dict_of_pd_lists.keys())
    plt.title("Cumulative Population Doubling")  
    if path_save != None:
        plt.savefig(os.path.join(path_save,"Cumulative Population Doubling"+ '.png'), dpi=200)
    
    if abc==True:
        dict_of_pd_lists["Initial"] = [0] * len(timelist)
        dict_abc = {}
        for key, value in dict_of_pd_lists.items():
            dict_abc[key] = pd.DataFrame({'CPD': value, "Frame" : timelist})
    
        abc_plots(dict_abc, "Initial", "Frame", "CPD", path_save = path_save)
              
        
           



def moving_average(df: pd. DataFrame,
                   y: str,
                   n: str,      # number to group for moving average
                   abc: bool = False,
                   ref: Optional[str] = None,    # reference for ABC calculations
                   path_save: Optional[str] = None
):
    
    """ 
    Gets a dataframe, its dimension to polot and a number of values to
    group and genetates the moving average plot based on "Frame" column
    """
    
    conditions = list(set(list(df["Condition"])))
    conditions.remove(ref)
    conditions.insert(0, ref)
    
    framelist = set(list(df["Frame"]))
    sns.set_theme()
    fsize = round(len(set(list(df["Frame"])))/12, 0) 
    if fsize< 12:
        fsize =12
    plt.figure(figsize=(fsize,6))
    dict_all_mov = {}
    for c in conditions:
         df_plot = df.loc[df["Condition"]== c]  
         mean = df_plot.groupby("Frame")[y].mean()
         moving_df = mean.to_frame()
         moving_df["Frame"]=moving_df.index
         moving_df["Condition"]= [c]*len(framelist)
         moving_avg = moving_df[y].rolling(n).mean()
         moving_df[y] = moving_avg
         ax = sns.lineplot(data=moving_df, y=y, x = "Frame")
         dict_all_mov[c] =  moving_df
    plt.title("Moving average "+ str(n) + " frames")
    plt.legend(conditions) 
    if '/' in y:
        z = y.replace('/', '_')
    else:
        z= y
    if path_save != None:
       plt.savefig(os.path.join(path_save,"Moving average " +z+ '.png'), dpi=200)
    
    for key, value in dict_all_mov.items():
          dict_all_mov[key] = value.iloc[n:]
    abc_plots(dict_all_mov, ref, "Frame", y, path_save= path_save)
 
    
 
    
 
    
 
#copiar esse gráfico de subplots pro lineplot tbm. Belíssim
#oferecer ABC cos lineplots em relação à uma ref
# calcular porcentagens do nma
#criar plots de foci separando intesidade e tamanho  - no caso scatterplot
#descobrir sobre hue "único"


   
#vou criar um dataset pra testar se ta tufo orolando certo se não vou enlouqucer aqui 
group = "222"

t1= pd.read_csv('D:\\Triagem\\Results\\NEW\\'+ group +'_0.001_1000 Results.csv')
t2= pd.read_csv('D:\\Triagem\\Results\\NEW\\'+ group +'_0.01_1000 Results.csv')
t3= pd.read_csv('D:\\Triagem\\Results\\NEW\\'+ group +'_0.1_1000 Results.csv')
t4= pd.read_csv('D:\\Triagem\\Results\\NEW\\'+ group +'_1_1000 Results.csv')
t5= pd.read_csv('D:\\Triagem\\Results\\NEW\\C_1000 Results.csv')
#t6 =  pd.read_csv('D:\\Triagem\\Results\\NEW\\MEKi_0.17_1000 Results.csv')
#t7 =  pd.read_csv('D:\\Triagem\\Results\\NEW\\MEKi_0.017_1000 Results.csv')

tl =[t5]#,t2,t3,t4, t5]


df = pd.DataFrame( )

for t in tl:
    df = pd.concat([df, t])

ps = 'D:\\Triagem\\Results\\NEW\\Graphs\\erk\\'+ group
ps2 = 'D:\\Triagem\\Results\\NEW\\Graphs\\cpd\\'+group
ps3 = 'D:\\Triagem\\Results\\NEW\\Graphs\\53bp1\\'+group

l = list(t1["Frame"])
l= list(set(l))
l = [int(i) for i in l]
l.sort()
timelist = [int(l[0]), int(l[54]), int(l[101]), int(l[149]), int(l[176]), int(l[183]), int(l[188])]

timelist_cpd = [0,54,101,149,176,182, 188]

l2 = [583,598,613,628,643,658,673,688,718,748,778,808,838,868,898,
 928,958, 988, 1018, 1048, 1078, 1108, 1138, 1168, 1198, 1228, 1258, 1288, 
 1318, 1348,
 1378,
 1408,
 1438,
 1468,
 1498,
 1528,
 1558,
 1588,
 1618 ]


df_plot = pd.DataFrame()

for i in l2:
    dp= t5[t5["Frame"] == i] 
    df_plot = df_plot.append(dp)
    
lineplot('Frame', "Mean_Ellipse/Nucleus_green", df_plot,  ci=95)

#categorical_plots('strip', "Area" , "Area", df, overtime = True )

#lineplot('Frame', "Mean_Ellipse/Nucleus_green", df,  ci=95, path_save =ps)
#lineplot('Frame', "Total_foci_red", df, split = False, ci=95, path_save =ps3)
#scatterplots('NII', 'Area', df, hue= 'Condition', overtime= True, timelist = [0,30,60,90])
#cpd(df, timelist_cpd, abc=True, path_save=ps2)
#moving_average(df, "Mean_Ellipse/Nucleus_green", 20,  abc=True, ref = 'C_1000', path_save = ps)
#moving_average(df, "Total_foci_red", 20,  abc=True, ref = 'C_1000', path_save = ps3)


# gerar tabelas de foci separado !!!!!!! 

#sns.lineplot(data=df, x="Frame", y="Mean_Ellipse/Nucleus_green", hue="Condition", ci=95)
#sns.lineplot(data=df,x="Frame", y="Mean_Ellipse/Nucleus_green", hue='Condition', style =None,
#            size=None,  ci=95, legend="full" ,units=None, 
 #                                sort= False) 
