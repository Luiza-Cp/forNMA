# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 07:23:10 2021

@author: Luiza
"""
import os

f1 = 'D:\\Triagem\\Red_Registered\\177'
f2 = 'D:\\Triagem\\Green_registered\\177'

folders_f1 =sorted(os.listdir(f1))
folders_f2 =sorted(os.listdir(f2))


erro = []
for n in range (len (folders_f1)):
    sub1 =  os.listdir(os.path.join(f1,folders_f1[n]))
    sub2 =  os.listdir(os.path.join(f2,folders_f2[n]))
    

    for i in range(len(sub1)):
        f1_l = os.listdir(os.path.join(f1,folders_f1[n], sub1[i]))
        f2_l = os.listdir(os.path.join(f2,folders_f2[n], sub2[i]))

        l = [ [f,g]  for f, g in zip(f1_l, f2_l) if f[-7:] != g[-7:]]

        z = zip(f1_l, f2_l)
        for i in z:
            print (i)
        
        if len(l) > 0:
            erro.appen(l)
    
    print (len(f1_l), len (f2_l))


if len (erro) == 0:
    print ('TUDO CERTO')