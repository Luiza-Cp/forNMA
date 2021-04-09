# -*- coding: utf-8 -*-
"""
Created on Thu Feb  4 14:08:09 2021

@author: Luiza
"""
from scipy import stats
import math 
import os
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from matplotlib.patches import Ellipse
from math import pi

path = 'D:\\Doutorado\\Imagens incucyte\\dinamica 53bp1\\A172\\Resultados\\TMZ 50'
#path = 'D:\\Doutorado\\Imagens eduardo\\Results'

df_list = []
df_dict= {}

for file in os.listdir(path):
    if file.endswith(".csv"):
        print(file)
        table = pd.read_csv(path+ '\\' + file) 
        df_dict[file] = table
        df_list.append(table)
        
# dia 1 e 2 são controle   
df_NMA_dict = {} 
df_NMA_list = [] 
for key, value in df_dict.items():
    df_NMA = value[['Nucleus', 'Nucleus Area',"NII"]]
    df_NMA_list.append(df_NMA)
    df_NMA_dict[key] = df_NMA
   
control_df = pd.concat([df_NMA_list[0]],  ignore_index=True)
#control_df = pd.concat([df_NMA_list[0], df_NMA_list[1]],  ignore_index=True)
#for i in df_NMA_list[2:]:
#    control_df = pd.concat([control_df, i],  ignore_index=True)


def lines(el):
    rx= el[1] - el[1]/2
    ry = el[2] - el[2]/2
    horizontal_x =  [el[0][0] -rx,  el[0][0] + 3*rx]
    horizontal_y_up = [el[0][1]+ry, el[0][1]+ry]
    horizontal_y_down= [el[0][1]-ry, el[0][1]-ry]
    vertical_x =  [el[0][0] +rx,  el[0][0] +rx]
    vertical_y=  [el[0][1] -ry,  el[0][1] + 3*ry]
    return horizontal_x, horizontal_y_up,horizontal_y_down, vertical_x, vertical_y


   
def plot_NMA(name, df, ellipse, xh, yh1, yh2, xv, yv):
    fig,ax = plt.subplots(1)
    sns.scatterplot(data=df, x="NII", y="Nucleus Area", color='#A02F7E', ax=ax) 
    el = Ellipse(ellipse[0], ellipse[1], ellipse[2],color='black', fill=False)
    ax.add_patch(el)
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='black')
    plt.title(name)

def plot_NMA_heatmap(name, df,xh, yh1, yh2, xv, yv, xmin, xmax , ymin, ymax ):
    plt.figure()
    sns.displot(df, x="NII", y="Nucleus Area", cmap= 'rocket', kind='kde', 
                fill=True, thresh= None, levels = 100)
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='white', linewidth = 0.75)
    plt.ylim(ymin, ymax)
    plt.xlim(xmin,xmax)
    plt.title(name)

   

def thresh_NMA(df):
    means_NII = []
    means_area= []
    for i in range(10000):
        df2 = df.sample(replace=True).mean()
        means_NII.append(df2['NII'].mean())
        means_area.append(df2['Nucleus Area'].mean())
    x_ax = stats.describe(means_NII)
    y_ax = stats.describe(means_area)
    sd_x = math.sqrt(x_ax[3])
    sd_y = math.sqrt(y_ax[3])

    ellipse = [(x_ax[2], y_ax[2]), 4*sd_x, 4*sd_y] 
    return ellipse
    

def thresh2(df):
    mean_NII = df['NII'].mean()
    mean_a = df["Nucleus Area"].mean()
    std_NII = df['NII'].std()
    std_a = df["Nucleus Area"].std() 
    ellipse_patch = [(mean_NII, mean_a), 4*std_NII, 4*std_a] 
    #u= mean_NII     #x-position of the center
    #v= mean_a       #y-position of the center
    #a= 2*std_NII    #radius on the x-axis
    #b=2*std_a       #radius on the y-axis
    #t = np.linspace(0, 2*pi, 100) 
    return ellipse_patch #, mean_NII, mean_a, std_NII, std_a, t


from scipy import stats
import numpy as np    
df2 =  control_df[['Nucleus Area', 'NII']]
df3 = df2[(np.abs(stats.zscore(df2)) < 2).all(axis=1)]
ellipse = thresh2(df3)
xh, yh1, yh2, xv, yv = lines(ellipse)


for key, value in df_NMA_dict.items():
    plot_NMA(key, value, ellipse, xh, yh1, yh2, xv, yv)
    #plt.savefig('D:\\Doutorado\\Imagens eduardo\\Results\\Graph_' + key+ '.png', dpi=200) 
     #ax = sns.displot(value,x="NII", y="Nucleus Area", cmap= 'rocket' )
     #plt.plot (xh, yh1, xh, yh2, xv, yv, color='red')
    # t = np.linspace(0, 2*pi, 100)
     #plt.plot( 1+3*np.cos(t) , 100+50*np.sin(t), color = 'red' )
   
    