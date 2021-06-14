# -*- coding: utf-8 -*-
"""
Created on Sun Apr 25 23:18:10 2021

@author: Luiza
"""

import similaritymeasures
import pandas as pd
import re
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import math
from statannot import add_stat_annotation
#se eu fizer regex com o final do nome eu posso saber o que vai em cada tempo 
#cada tabela é uma concntração
# com esse dado eu crio a coluna time

one_r = pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\1. True t=120 seg\\177_0.001_1000 reg Results.csv')
one = pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\1. True t=120 seg\\177_0.001_1000 Results')
two_r =  pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\2. False t=108 seg\\177_0.001_1000 reg Results.csv')
two = pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\2. False t=108 seg\\177_0.001_1000 Results')
three_r =  pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\3. True, remove 40, t= 22 min\\177_0.001_1000 reg Results.csv')
three = pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\3. True, remove 40, t= 22 min\\177_0.001_1000 Results')
four_r =  pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\4. True, remove 50, t= 29 min\\177_0.001_1000 reg Results.csv')
four = pd.read_csv('C:\\Users\\Luiza Cherobini\\Desktop\\res\\4. True, remove 50, t= 29 min\\177_0.001_1000 Results')



csv_list = [one_r, one, two_r, two, three_r, three, four_r, four]


table1 = one_r
table2 = one
table3 = two_r
table4 = two
table5 = three_r
table6 = three
table7 = four_r
table8 = four

tt = 'Control '
saving = 'D:\\Triagem'


time_list = []
for name in table1['Image_ch1']:
    a = name[:-10]
    time = a[-7:]
    time_list.append(time)

time_list = list(set(time_list))
time_list.sort()

for t in range(len(time_list)):
   table1.loc[table1['Image_ch1'].str.contains(time_list[t]), "Time"] = t
   table2.loc[table2['Image_ch1'].str.contains(time_list[t]), "Time"] = t
   table3.loc[table3['Image_ch1'].str.contains(time_list[t]), "Time"] = t
   table4.loc[table4['Image_ch1'].str.contains(time_list[t]), "Time"] = t
   table5.loc[table5['Image_ch1'].str.contains(time_list[t]), "Time"] = t
   table6.loc[table6['Image_ch1'].str.contains(time_list[t]), "Time"] = t
   table7.loc[table7['Image_ch1'].str.contains(time_list[t]), "Time"] = t
  


vermelho = '#4C72B0'
roxo = '#DD8452' 
azul = '#55A868'
verde = '#C44E52'
amarelo = '#8172B3'
laranja = '#CCB974'
marrom = '#DA8BC3'


tb = [table1, table2, table3, table4, table5, table6, table7]
c_list =[ vermelho, roxo, azul, verde , amarelo, laranja, marrom ]
leg = ['Control', 'DMSO', 'Meki', '177', '222', 'DBS07', 'DBS16']

tt = 'All'

# Ativação erk -> para colocar váios é só ir botando sns lineplot

for i in range (len(tb)):
    plt.figure(figsize = (10,6))
    ax = sns.lineplot(data=tb[i], x="Time", y="Mean_Ellipse/Nucleus", color = c_list[i]) #, ci=None)
#ax= sns.lineplot(data=table2, x="Time", y="Mean_Ellipse/Nucleus", color = roxo) #, ci=None)
#ax = sns.lineplot(data=table3, x="Time", y="Mean_Ellipse/Nucleus", color = azul) #, ci=None)
#ax = sns.lineplot(data=table4, x="Time", y="Mean_Ellipse/Nucleus", color = verde)#, ci=None)
#ax = sns.lineplot(data=table5, x="Time", y="Mean_Ellipse/Nucleus", color = amarelo) #, ci=None)
#ax = sns.lineplot(data=table6, x="Time", y="Mean_Ellipse/Nucleus", color = laranja) #, ci=None)
#ax = sns.lineplot(data=table7, x="Time", y="Mean_Ellipse/Nucleus", color = marrom) #, ci=None)
    #ax.legend(leg[i])
    plt.xticks(rotation=70)
    plt.axvline(x=0, ymin=0, ymax=1, color ='red', linestyle=':')
    plt.tight_layout()
    plt.title(leg[i])
    plt.savefig(saving+ '//erk ' + leg[i], dpi =200)


#violino com dotplot da ativação
for i in range (len(tb)):
    plt.figure(figsize = (10,6))
    ax = sns.violinplot(x="Time", y="Mean_Ellipse/Nucleus", data=tb[i], inner=None)
    ax = sns.swarmplot(x="Time", y="Mean_Ellipse/Nucleus", data=tb[i],
                   color="black", edgecolor="gray", size = 3)
    plt.axvline(x=0, ymin=0, ymax=1, color ='red', linestyle=':')
    plt.xticks(rotation=70)
    plt.tight_layout()
    plt.title(leg[i])
    test_results = add_stat_annotation(ax, data=tb[i], x="Time", y="Mean_Ellipse/Nucleus",
                                                                     test='Mann-Whitney', text_format='star',
                                                                     loc='outside', verbose=2)
    plt.savefig(saving+ '//erk violin ' + leg[i], dpi =200)
    

#Só dot plot
for i in range(len(tb)):
    plt.figure(figsize = (10,6))
    ax = sns.swarmplot(x="Time", y="Mean_Ellipse/Nucleus", data=tb[i], palette='magma', size=4)
    plt.xticks(rotation=70)
    plt.tight_layout()
    plt.title(leg[i])
    plt.savefig(saving+ '//erk dot ' + leg[i], dpi =200)



#dano lineplot - total de pontos
plt.figure(figsize = (10,6))
ax =sns.lineplot(data=table1, x="Time", y="Total_foci", color = vermelho, ci=None)
ax = sns.lineplot(data=table2, x="Time", y="Total_foci", color = roxo, ci=None)
ax = sns.lineplot(data=table3, x="Time", y="Total_foci", color = azul, ci=None)
ax = sns.lineplot(data=table4, x="Time", y="Total_foci", color = verde, ci=None)
ax = sns.lineplot(data=table5, x="Time", y="Total_foci", color = amarelo, ci=None)
ax = sns.lineplot(data=table6, x="Time", y="Total_foci", color = laranja, ci=None)
ax = sns.lineplot(data=table7, x="Time", y="Total_foci", color = marrom, ci=None)
ax.legend(['Control', 'DMSO', 'Meki', '177', '222', 'DBS07', 'DBS16'])
plt.xticks(rotation=70)
plt.axvline(x=18, ymin=0, ymax=1, color ='red', linestyle=':')
plt.xticks(rotation=70)
plt.tight_layout()
plt.title(tt)
plt.savefig(saving+ '//dano ' + tt, dpi =200)

#dano lineplot - area de pontos
plt.figure(figsize = (10,6))
ax =sns.lineplot(data=table1, x="Time", y="Total_foci_area", color = vermelho, ci=None)
ax = sns.lineplot(data=table2, x="Time", y="Total_foci_area", color = roxo, ci=None)
ax = sns.lineplot(data=table3, x="Time", y="Total_foci_area", color = azul, ci=None)
ax = sns.lineplot(data=table4, x="Time", y="Total_foci_area", color = verde, ci=None)
ax = sns.lineplot(data=table5, x="Time", y="Total_foci_area", color = amarelo, ci=None)
ax = sns.lineplot(data=table6, x="Time", y="Total_foci_area", color = laranja, ci=None)
ax = sns.lineplot(data=table7, x="Time", y="Total_foci_area", color = marrom, ci=None)
ax.legend(['Control', 'DMSO', 'Meki', '177', '222', 'DBS07', 'DBS16'])
plt.xticks(rotation=70)
plt.axvline(x=18, ymin=0, ymax=1, color ='red', linestyle=':')
plt.tight_layout()
plt.title(tt)
plt.savefig(saving+ '//dano area' + tt, dpi =200)

#dano swarmplot
plt.figure(figsize = (15,6))
ax = sns.swarmplot(x="Time", y="Total_foci", data=table1, palette='magma')
plt.xticks(rotation=70)
plt.tight_layout()
plt.title(tt)



#PD

plt.figure(figsize = (8,6))
plt.rcParams['axes.facecolor'] = 'White'

for i in range(len(tb)):
    
    num_cell = tb[i]["Time"].value_counts()
    num_cell2 = list(num_cell.sort_index())
    num_cell =[num_cell2[0], num_cell2[48], num_cell2[96], num_cell[144]]
    pd_list = []
    time_pd = ['day 2','day 3','day 4']
    for n in range(len(num_cell)-1):
        fim = math.log(num_cell[n+1])
        ini = math.log(num_cell[n])
        pd = (fim-ini)/math.log(2)
        pd_list.append(pd)
 
    ax =sns.lineplot(y = pd_list, x = time_pd,marker='s', color=c_list[i])

    
ax.legend(['Control', 'DMSO', 'Meki', '177', '222', 'DBS07', 'DBS16'])   
plt.axvline(x=0, ymin=0, ymax=1, color ='red', linestyle=':') 
plt.xlabel('Time')
plt.ylabel('Cumulative Population Doubling')   
plt.title(tt) 
plt.savefig(saving+ '//pd ' + tt, dpi =200)
# ok, pro NMA eu tenho que selecionar alguns tempos só..




#MÈDIA MOVEL
names = ['Control', 'DMSO', 'Meki', '177', '222', 'DBS07', 'DBS16']
m_list = []
sd_list =[]
plt.figure()
for i in range(len(tb)):
    m = tb[i].groupby("Time")["Mean_Ellipse/Nucleus"].mean()
    sd = tb[i].groupby("Time")["Mean_Ellipse/Nucleus"].std()
    frame = { 'Mean': m, 'SD': sd }
    result = pd.DataFrame(frame)
    m_list.append(m)
    sd_list.append(sd)
    mov = result['Mean'].rolling(4).mean()
    ax = sns.lineplot(data=mov, color=c_list[i])
ax.legend(['Control', 'DMSO', 'Meki', '177', '222', 'DBS07', 'DBS16'])  
plt.axvline(x=0, ymin=0, ymax=1, color ='red', linestyle=':') 
plt.savefig(saving+ '//Média movel' , dpi =200)

dict_means = {}
for i in range(len(names)):
    dict_means[names[i] + ' mean'] =  m_list[i].values
    dict_means[names[i] + ' sd'] = sd_list[i].values
    

df_means = pd.DataFrame.from_dict(dict_means)
df_means.to_csv('D:\\Triagem\\means.csv', sep = '\t')


#area entre curvas
curve_ct =np.zeros((len(m_list[0]), 2))
y = list(range(11))
curve_ct[:, 0] = m_list[0]
curve_ct[:, 1] = y

for i in (m_list):
    y = list(range(11))
    curve = np.zeros((len(i), 2))
    curve[:, 0] = i
    curve[:, 1] = y
    
    area = similaritymeasures.area_between_two_curves(curve_ct, curve)
    print (area)




#NMA
from math import pi
from scipy import stats

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


def find_yx_lim2(df_dict):
    #remove outlier
    max_a = []
    min_a = 0
    max_NII = []
    min_NII = 0
    
    for key, value in df_dict.items():
        value = value[['Area', 'NII']]
        df = value[(np.abs(stats.zscore(value)) < 3).all(axis=1)]
        max_a.append(df['Area'].max())
        #min_a.append(df['Area'].min())
        max_NII.append(df['NII'].max())
        #min_NII.append(df['NII'].min())
        
    return min_a,max(max_a), min_NII, max(max_NII)  





df_dict = {}
for i in range(len(tb)):
    ctr_nma =  tb[i][tb[i]["Time"]  == 6]
    df_dict[leg[i]+ ' -2 h'] =  tb[i][tb[i]["Time"]  == 7]
    df_dict[leg[i]+ ' 2 h'] =  tb[i][tb[i]["Time"]  == 22] #isso é após tto
    df_dict[leg[i]+ ' 14 h'] =  tb[i][tb[i]["Time"]  == 46]
    df_dict[leg[i]+ ' 26 h'] =  tb[i][tb[i]["Time"]  == 70]
    df_dict[leg[i]+ ' 38 h'] =  tb[i][tb[i]["Time"]  == 94]
    df_dict[leg[i]+ ' 50 h'] =  tb[i][tb[i]["Time"]  == 118]
    df_dict[leg[i]+ ' 62 h'] =  tb[i][tb[i]["Time"]  == 142]
    
    mean_NII, mean_a, std_NII, std_a, t = thresh_NMA(ctr_nma)
    xh, yh1, yh2, xv, yv = lines(mean_NII, mean_a, std_NII, std_a)

    lims = find_yx_lim2(df_dict)
    plt.rcParams['axes.facecolor'] = 'white'
    for key, value in df_dict.items():
        fig,ax = plt.subplots(1)
        sns.scatterplot(data=value, x="NII", y="Area", hue = 'Mean_Ellipse/Nucleus', size='Total_foci', ax=ax, s=40) 
        plt.plot( mean_NII+(2*std_NII)*np.cos(t) , mean_a+(2*std_a)*np.sin(t), color= 'black' )
        plt.plot (xh, yh1, xh, yh2, xv, yv, color='black')
        plt.title(key)
        plt.ylim(lims[0], lims[1])
        plt.xlim(lims[2], lims[3])
        plt.savefig('D:\\Triagem\\' + key + '.png', dpi =200)


hue_norm=(0,0.5)



thresh_a = mean_a + 2*std_a
thresh_NII = mean_NII + 2*std_NII

big = ctr_nma.loc[ctr_nma['Area'] > thresh_a]
small =  ctr_nma.loc[ctr_nma['Area'] < thresh_a]


small_regular =  small.loc[small['NII']< thresh_NII].shape[0]
small_irregular = small.loc[small['NII']> thresh_NII].shape[0]
big_regular =  big.loc[big['NII'] < thresh_NII].shape[0]
big_irregular = big.loc[big['NII'] > thresh_NII].shape[0] 
hue_norm=(0,0.5)