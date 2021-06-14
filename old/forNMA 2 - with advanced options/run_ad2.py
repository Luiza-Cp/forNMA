# -*- coding: utf-8 -*-
"""
Created on Sun Apr 25 15:12:09 2021

@author: Luiza

esse vai ser tipo o run
"""

import os
from teste_substituto_analyze import get_file_list, analyze, split_dfs, draw_and_save
from preview import load_image
import time

st = time.time()
main_dir1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\teste r'
main_dir2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\teste g'
path_to_save = 'C:\\Users\\Luiza Cherobini\\Desktop\\res'

folders_list1 = []
if os.path.exists(main_dir1) == False:
    raise ValueError ('This file do not exists: '+ main_dir1)
for i in [f for f in os.listdir(main_dir1) if not f.startswith('.')]:
    full_path = os.path.join(main_dir1, i)
    folders_list1.append(full_path)

        
if main_dir2 is not None: 
    if os.path.exists(main_dir2) == False:
        raise ValueError ('This file do not exists: ' +  main_dir1)
    folders_list2 = []
    for i in [f for f in os.listdir(main_dir2) if not f.startswith('.')]:
        full_path = os.path.join(main_dir2, i)
        folders_list2.append(full_path)
else:
    folders_list2 = None
    


for i in range (len(folders_list1)):
    ch1_files, ch2_files, foldername1, foldername2, ch1_save, ch2_save = get_file_list (
                                                                        folders_list1[i], 
                                                                        path_to_save, True, 
                                                                        folders_list2[i] )
    
    #esses serão os itens de referência - tem que estar no códigooo    
    ref_ch1 = load_image(ch1_files[0], rescale_intensity = False)
    ref_ch2 =None 
    if ch2_files is not None:
        ref_ch2 = load_image(ch2_files[0],rescale_intensity = False)
    #se tiver mais cainais eu posso fazer um ref dict. Pra cada folserlist sla
    #tenho que pensar melhor nisso aqoui 
    
    
    
   #AQUI QUE MUDA OS PARAMETROS
    df_total = analyze(ch1_files, 40, 0.1 ,ref_ch1 = None, ref_ch2 = None,
                       wants_foci = True, foci_channel2= False, 
                       foci_min_size = 15, wants_ktr= True, use_ellipse= True,   
                       files_ch2= ch2_files, rescale_intensity = True, min_size = 30,
                       remove_bg = False, radius =30)
    
    
    df_save, df_cnt = split_dfs(df_total, wants_foci= True, wants_ktr = True)
    
    saving = os.path.join(path_to_save, foldername1 + '.csv')
    df_save.to_csv(saving, index=False)    
    print ('aqui')
    draw_and_save(df_cnt, ch1_save, ch2= True, path_save2 =ch2_save, wants_ktr = True, 
                  use_ellipse = True, wants_foci = True, foci_ch2 = False, 
                  rescale_intensity = True, remove_bg = False, radius =30, 
                  ref_ch1 = ref_ch1, ref_ch2 = ref_ch2)
                   
et =time.time()
print ('Tempo: ',et-st)   

