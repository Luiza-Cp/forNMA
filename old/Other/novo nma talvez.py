# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 03:42:09 2021

@author: Luiza
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



df_control = None
df_analyze = None 

df_list = [ df_controle, df_analyze]

#abaixo vai add a coluna Tempo nos dois dfs
for df in df_list:
    time_list = []
    for name in df['Image_ch1']:
        a = name[:-5]
        time = a[-12:]
        time_list.append(time)

    time_list = list(set(time_list))
    time_list.sort()

    for t in range(len(time_list)):
        df.loc[df['Image_ch1'].str.contains(time_list[t]), "Time"] = t





### Aplicar essas funções no dataframe do controle ou no tempo do controle
def thresh_NMA(df):
    mean_NII = df['NII'].mean()
    mean_a = df["Nucleus Area"].mean()
    std_NII = df['NII'].std()
    std_a = df["Nucleus Area"].std() 
    t = np.linspace(0, 2*pi, 100) 
    return mean_NII, mean_a, std_NII, std_a, t


def lines(mean_NII, mean_a, std_NII, std_a):
    rx= 2*std_NII
    ry = 2* std_a
    horizontal_x =  [mean_NII -rx,  mean_NII + 3*rx]
    horizontal_y_up = [mean_a +ry, mean_a +ry]
    horizontal_y_down= [mean_a-ry, mean_a-ry]
    vertical_x =  [mean_NII +rx,  mean_NII +rx]
    vertical_y=  [mean_a -ry,  mean_a + 3*ry]
    return horizontal_x, horizontal_y_up,horizontal_y_down, vertical_x, vertical_y


#########

mean_NII, mean_a, std_NII, std_a, t = thresh_NMA( df_control)
hx, hy_up,hy_down, vx, vy = lines(mean_NII, mean_a, std_NII, std_a)


#####

#Aqui é no df pra valer


def find_yx_lim2(df_dict):
    #remove outlier
    max_a = []
    min_a = []
    max_NII = []
    min_NII = []
    for key, value in df_NMA_dict.items():
        df = value[(np.abs(stats.zscore(value)) < 3).all(axis=1)]
        max_a.append(df['Nucleus Area'].max())
        min_a.append(df['Nucleus Area'].min())
        max_NII.append(df['NII'].max())
        min_NII.append(df['NII'].min())
    return min(min_a),max(max_a), min(min_NII), max(max_NII)  


