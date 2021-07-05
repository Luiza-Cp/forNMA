# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 17:42:48 2021

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

path = 'C:\\Users\\Luiza Cherobini\\Documents\\Nicolas\\results\\A'
#path = 'D:\\Doutorado\\Imagens eduardo\\Results'

df_list = []
df_dict= {}

for file in os.listdir(path):
    if file.endswith(".csv"):
        print(file)
        table = pd.read_csv(path+ '\\' + file) 
        table = table[table['Area'] > 1000]
        df_dict[file] = table
        df_list.append(table)
  
  
  
# dia 1 e 2 são controle   
df_NMA_dict = {} 
df_NMA_list = [] 
for key, value in df_dict.items():
    df_NMA = value[['Cell', 'Area',"NII"]]
    df_NMA_list.append(df_NMA)
    df_NMA_dict[key] = df_NMA
   
control_df = pd.concat([df_NMA_list[0]],  ignore_index=True)


#control_df = pd.concat([df_NMA_list[0], df_NMA_list[1]],  ignore_index=True)
#for i in df_NMA_list[2:]:
#    control_df = pd.concat([control_df, i],  ignore_index=True)


def thresh_NMA(df):
    mean_NII = df['NII'].mean()
    mean_a = df["Area"].mean()
    std_NII = df['NII'].std()
    std_a = df["Area"].std() 
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


def find_yx_lim(df_dict):
    max_a = []
    min_a = []
    max_NII = []
    min_NII = []
    for key, value in df_dict.items():
        max_a.append(value['Area'].max())
        min_a.append(value['Area'].min())
        max_NII.append(value['NII'].max())
        min_NII.append(value['NII'].min())
    return min(min_a),max(max_a), min(min_NII), max(max_NII)  

def find_yx_lim2(df_dict):
    #remove outlier
    max_a = []
    min_a = 3000
    max_NII = []
    min_NII = 2
    for key, value in df_NMA_dict.items():
        df = value[(np.abs(stats.zscore(value)) < 3).all(axis=1)]
        max_a.append(df['Area'].max())
        #min_a.append(df['Area'].min())
        max_NII.append(df['NII'].max())
        #min_NII.append(df['NII'].min())
    return min_a,max(max_a), min_NII, max(max_NII)  


def get_sample(df):
    df_sample = df.sample(n = 200)
    p_NII_var = f_test(df['NII'].values, df_sample['NII'].values)
    p_a_var = f_test( df['Area'].values,df_sample['Area'].values)
    p_NII_mean = stats.ttest_ind(df['NII'].values, df_sample['NII'].values)[1]
    p_a_mean = stats.ttest_ind( df['Area'].values,df_sample['Area'].values)[1]
        
    if p_NII_var > 0.05 and p_a_var > 0.05 and p_NII_mean > 0.05 and p_a_mean >0.05:
        boolean = True         
    else: 
        boolean = False
    return df_sample, boolean
    

def f_test(x, y):
    x = np.array(x)
    y = np.array(y)
    f = np.var(x, ddof=1)/np.var(y, ddof=1) #calculate F test statistic 
    dfn = x.size-1 #define degrees of freedom numerator 
    dfd = y.size-1 #define degrees of freedom denominator 
    p = 1- stats.f.cdf(f, dfn, dfd) #find p-value of F test statistic 
    return p

#antes de plotar isso tem que perguntar se tem mais de 200
#usar xy lim
def plot_NMA_200(name, df, xh, yh1, yh2, xv, yv, mean_NII, mean_a, std_NII, std_a, t, lims):
    df_sample, boolean = get_sample(df)
    while boolean == False:
        df_sample, boolean = get_sample(df)
    plt.rcParams['axes.facecolor'] = 'white'
    fig,ax = plt.subplots(1)
    sns.scatterplot(data=df_sample, x="NII", y="Area", size ='Total_foci_53BP1', 
                    hue = 'Total_foci_gamaH2AX', hue_norm =(0.0,40.0),
                    size_norm =(0.0,20.0), ax=ax, s=40) 
    plt.plot( mean_NII+(2*std_NII)*np.cos(t) , mean_a+(2*std_a)*np.sin(t), color= 'black' )
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='black')
    plt.ylim(lims[0], lims[1])
    plt.xlim(lims[2], lims[3])
    plt.title(name)

def plot_NMA_heatmap(name, df, xh, yh1, yh2, xv, yv, mean_NII, mean_a, std_NII, std_a, t, lims):
    plt.rcParams['axes.facecolor'] = '#03051A'
    plt.figure()
    #fig,ax = plt.subplots(1)
    sns.displot(df, x="NII", y="Area", cmap= 'rocket', kind='kde', 
                    fill=True, thresh= None, levels = 60)
    #plt.plot( mean_NII+(2*std_NII)*np.cos(t) , mean_a+(2*std_a)*np.sin(t), color= 'white', linewidth = 0.75 )
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='white', linewidth = 0.75)
    plt.ylim(lims[0], lims[1])
    plt.xlim(lims[2], lims[3])
    plt.title(name)

def plot_NMA_heatmap_dot(name, df, xh, yh1, yh2, xv, yv, mean_NII, mean_a, std_NII, std_a, t, lims):
    plt.rcParams['axes.facecolor'] = 'white'
    plt.figure()
    sns.displot(df,x="NII", y="Area", cmap= 'rocket')
    plt.plot( mean_NII+(2*std_NII)*np.cos(t) , mean_a+(2*std_a)*np.sin(t), color= 'red', linewidth = 0.75 )
    plt.plot (xh, yh1, xh, yh2, xv, yv, color='red', linewidth = 0.75)
    plt.title(name)

def  pop_doubling(df_list, time_list):
    num = []
    time = time_list[1:]
    for n in range(len(df_list)):
        num.append(df_list[n].shape[0])
    ln_num = np.log(num) 
    print (ln_num)
    pd_list = []
    for n in range (len(ln_num)-1):
        pd = (ln_num[n+1]- ln_num[n])/np.log(2)
        pd_list.append(pd)
    
    plt.figure()
    plt.rcParams['axes.facecolor'] = 'White'
    sns.lineplot(y = pd_list, x = time,marker='s', color='#A02F7E')
    plt.xlabel('Time')
    plt.ylabel('Cumulative Population Doubling')

        

df2 =  control_df[['Area', 'NII']]
df3 = df2[(np.abs(stats.zscore(df2)) < 2).all(axis=1)]
mean_NII, mean_a, std_NII, std_a, t = thresh_NMA(df3)
xh, yh1, yh2, xv, yv = lines(mean_NII, mean_a, std_NII, std_a)
lims = find_yx_lim2(df_dict)

for key, value in df_dict.items():
    plot_NMA_200(key, value ,xh, yh1, yh2, xv, yv, mean_NII, mean_a, std_NII, std_a,t , lims)
    #plot_NMA_heatmap(key, value, xh, yh1, yh2, xv, yv, mean_NII, mean_a, std_NII, std_a, t, lims )

    plt.savefig(path +'\\ sample ' + key +'.svg', dpi=200)

#l = [5,6,7,8,9,11,12,13]
#pop_doubling(df_list, l)

# DESCOBRIR COMO CALCLAR OS LEVELS AUTOMATICAMENTEEEE
for key, value in df_dict.items():
    print (key + '53bp1', value['Total_foci_53BP1'].mean())
    print (key + 'gH2AX', value['Total_foci_gamaH2AX'].mean())