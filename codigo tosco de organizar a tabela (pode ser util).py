# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 09:27:58 2021

@author: Luiza
"""
import pandas as pd
import os

path = 'D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\Meki\\Results'

l= ['10h45m', '10h50m', '10h55m', '11h00m', '11h05m', '11h10m', '11h15m', '11h20m', 
    '11h25m', '11h30m', '11h35m', '11h40m', '11h45m', '11h50m', '11h55m', '12h00m', 
    '12h05m', '12h10m', '12h15m', '12h20m', '12h25m', '12h30m', '12h35m', '12h40m', 
    '12h45m', '12h50m', '12h55m', '13h00m', '13h05m', '13h10m', '13h15m', '13h20m', 
    '13h25m', '13h30m', '13h35m', '13h40m', '13h45m']
        

  
A11 = pd.DataFrame([])
A12 = pd.DataFrame([])
A13 = pd.DataFrame([])
A14 = pd.DataFrame([])
A15 = pd.DataFrame([])
A16 = pd.DataFrame([])
A17 = pd.DataFrame([])
A18 = pd.DataFrame([])
A19 = pd.DataFrame([])
A21 = pd.DataFrame([])
A22 = pd.DataFrame([])
A23 = pd.DataFrame([])
A24 = pd.DataFrame([])
A25 = pd.DataFrame([])
A26 = pd.DataFrame([])
A27 = pd.DataFrame([])
A28 = pd.DataFrame([])
A29 = pd.DataFrame([])




      
for file in os.listdir(path):
    if file.endswith(".csv"):
        print(os.path.join(path, file))
        table = pd.read_csv(path+ '\\' + file)
        table['Image'] = table['Image'].str[:-23]

        
        
        df1 = table[table['Image'] == 'VID85_A1_1']
        df2 = table[table['Image'] == 'VID85_A1_2']
        df3 = table[table['Image'] == 'VID85_A1_3']
        df4 = table[table['Image'] == 'VID85_A1_4']
        df5 = table[table['Image'] == 'VID85_A1_5']
        df6 = table[table['Image'] == 'VID85_A1_6']
        df7 = table[table['Image'] == 'VID85_A1_7']
        df8 = table[table['Image'] == 'VID85_A1_8']
        df9 = table[table['Image'] == 'VID85_A1_9']
        df10 = table[table['Image'] == 'VID85_A2_1']
        df11 = table[table['Image'] == 'VID85_A2_2']
        df12 = table[table['Image'] == 'VID85_A2_3']
        df13 = table[table['Image'] == 'VID85_A2_4']
        df14 = table[table['Image'] == 'VID85_A2_5']
        df15 = table[table['Image'] == 'VID85_A2_6']
        df16 = table[table['Image'] == 'VID85_A2_7']
        df17 = table[table['Image'] == 'VID85_A2_8']
        df18 = table[table['Image'] == 'VID85_A2_9']

        

        A11 = pd.concat([A11, df1[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A12 = pd.concat([A12, df2[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A13 = pd.concat([A13, df3[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A14 = pd.concat([A14, df4[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A15 = pd.concat([A15, df5[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A16 = pd.concat([A16, df6[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A17 = pd.concat([A17, df7[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A18 = pd.concat([A18, df8[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A19 = pd.concat([A19, df9[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A21 = pd.concat([A21, df10[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A22 = pd.concat([A22, df11[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A23 = pd.concat([A23, df12[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A24 = pd.concat([A24, df13[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A25 = pd.concat([A25, df14[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A26 = pd.concat([A26, df15[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A27 = pd.concat([A27, df16[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A28 = pd.concat([A28, df17[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        A29 = pd.concat([A29, df18[['CE/N Mean Normalized']]], axis=1, ignore_index =True)
        
  

df_list = [ A11, A12, A13, A14, A15, A16, A17, A18, A19 ,A21 ,A22, A23, A24, A25, A26, A27, A28, A29 ]

for d in df_list:
    d.columns =  l   

A11 = A11.apply(lambda x: pd.Series(x.dropna().values))
A12 = A12.apply(lambda x: pd.Series(x.dropna().values))
A13 = A13.apply(lambda x: pd.Series(x.dropna().values))
A14 = A14.apply(lambda x: pd.Series(x.dropna().values))
A15 = A15.apply(lambda x: pd.Series(x.dropna().values))
A16 = A16.apply(lambda x: pd.Series(x.dropna().values))
A17 = A17.apply(lambda x: pd.Series(x.dropna().values))
A18 = A18.apply(lambda x: pd.Series(x.dropna().values))
A19 = A19.apply(lambda x: pd.Series(x.dropna().values))
A21 = A21.apply(lambda x: pd.Series(x.dropna().values))
A22 = A22.apply(lambda x: pd.Series(x.dropna().values))
A23 = A23.apply(lambda x: pd.Series(x.dropna().values))
A24 = A24.apply(lambda x: pd.Series(x.dropna().values))
A25 = A25.apply(lambda x: pd.Series(x.dropna().values))
A26 = A26.apply(lambda x: pd.Series(x.dropna().values))
A27 = A27.apply(lambda x: pd.Series(x.dropna().values))
A28 = A28.apply(lambda x: pd.Series(x.dropna().values))
A29 = A29.apply(lambda x: pd.Series(x.dropna().values))       

All = pd.concat([A11, A12, A13, A14,A15,A16,A17,A18,A19], axis =0)
All = All.apply(lambda x: pd.Series(x.dropna().values))    

All2 = pd.concat([A21, A22, A23, A24,A25,A26,A27,A28,A29], axis =0)
All2 = All2.apply(lambda x: pd.Series(x.dropna().values))     

writer = pd.ExcelWriter('D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\Meki\\Results_A1_A2.xlsx')
All.to_excel(writer, 'A1')
All2.to_excel(writer, 'A2')
#writer.save()


import seaborn as sns
from matplotlib import pyplot as plt



df_All = pd.DataFrame(columns=['C/N', 'Time'])

for col in All.columns:
    print(col)
    dfall= All[[col]]
    dfall['Time'] = col
    dfall = dfall.rename(columns={str(col): "C/N"})
    dfall.dropna()
    dfall.reset_index(drop=True)
    #df_All = pd.concat([df_All, dfall])
    df_All = df_All.append(dfall)
    
df_All2 = pd.DataFrame(columns=['C/N', 'Time'])

for col in All2.columns:
    print(col)
    dfall2= All2[[col]]
    dfall2['Time'] = col
    dfall2 = dfall2.rename(columns={str(col): "C/N"})
    dfall2.dropna()
    dfall2.reset_index(drop=True)
    #df_All = pd.concat([df_All, dfall])
    df_All2 = df_All2.append(dfall2)


plt.figure()
sns.lineplot(data=df_All, x="Time", y="C/N", color = '#F65886' )
plt.xticks(rotation=70)
plt.tight_layout()
plt.title('Todos os Campos')
plt.savefig('D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\Meki\\graphs a1 e a2\\A1\\all.png', dpi=200) 

plt.figure()
sns.lineplot(data=All.var(axis=0))
plt.xticks(rotation=70)
plt.tight_layout()
plt.title('Todos os Campos (variância)')
plt.savefig('D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\Meki\\graphs a1 e a2\\A1\\all_var.png', dpi=200) 
plt.figure()
sns.violinplot( data=All, inner= None)
plt.xticks(rotation=70)
plt.tight_layout()
plt.title('Todos os Campos')
plt.savefig('D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\Meki\\graphs a1 e a2\\A1\\violin.png', dpi=200) 

plt.figure()
sns.swarmplot( data=All, size=1)
plt.xticks(rotation=70)
plt.tight_layout()
plt.title('Todos os Campos2')
plt.savefig('D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\Meki\\graphs a1 e a2\\A1\\dot.png', dpi=200) 

'''

df_list = [A11, A12, A13, A14,A15,A16,A17,A18,A19,A21,A22,A23,A24,A25,A26,A27,A28,A29]
n= 0 
for d in df_list:

    dfd=pd.DataFrame(columns=['C/N', 'Time'])
    for col in d.columns:
        dfa= d[[col]]
        dfa['Time'] = col
        dfa = dfa.rename(columns={str(col): "C/N"})
        dfa.dropna()
        dfa.reset_index(drop=True)
        dfd = dfd.append(dfa)
    plt.figure()   
    sns.lineplot(data=dfd, x="Time", y="C/N", color = '#F65886' )
    plt.xticks(rotation=70)
    plt.tight_layout()
    plt.savefig('D:\\Doutorado\\imagens incucyte kaka\\Meki\\tablas separando A1 e A2\\A2\\results\\' + str(n)+ '.png', dpi=200) 
    
    plt.figure()   
    sns.lineplot(data=d.var(axis=0))
    plt.xticks(rotation=70)
    plt.tight_layout()
    plt.savefig('D:\\Doutorado\\imagens incucyte kaka\\Meki\\tablas separando A1 e A2\\A2\\results\\' + str(n)+ '(var).png', dpi=200) 

    n = n+1
'''
'''

#df_plot1 = dfAll c/

#Create combo chart
fig, ax1 = plt.subplots(figsize=(10,6))
plt.xticks(rotation=70)
color = 'tab:green'
#bar plot creation
sns.lineplot(data=df_All, x="Time", y="C/N", color = '#F65886' )
#specify we want to share the same x-axis
#ax2= ax1.twinx()
ax2 = ax1
color = 'tab:red'
#line plot creation
sns.lineplot(data=df_All2, x="Time", y="C/N", color = '#064878')
ax2.tick_params(axis='y', color=color)
plt.xticks(rotation=70)
#show plot

plt.savefig('D:\\Doutorado\\Imagens incucyte\\imagens incucyte kaka\\Meki', dpi=200) 

'''