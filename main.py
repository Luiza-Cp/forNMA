# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 14:25:56 2021

@author: Luiza

Will be the main file 
"""


import os
from typing import List, Optional
from analyze_multichannel import check_size, analyze_dict, saving_images,split_dfs, save_dfs
import tempfile
import pandas as pd 
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np




def run(path_to_save: str,
        ch_name_list: List[str],
        ch_path_list: List[str],
        ch_with_nuc: str,
        overtime: bool,
        parameter_list: List[str],
        conditions: List[str],
        segment_dict: dict,
        wants_to_save: bool
        ):
    # cria um dicionário da pasta
    # key: nome de cada canal
    #values: possui 3 valores
        # 0: uam lista com o caminho de todas as pastas nesse canal
        # 1: o param_dict desse canal
        # 2: bool (informa se o canal é o de segmentação nuclear)
        # 3: bool (informa se o canal é o de segmentação citoplasmatica)
    
    subfolder_dict = {}
    for i in range(len(ch_name_list)):
        seg_nuc = ch_with_nuc == ch_path_list[i]
        seg_cyto = parameter_list[i]['cytoplasm']
        subfolders = sorted((os.listdir(ch_path_list[i])))
        subfolder_dict[ch_name_list[i]] = [[os.path.join(ch_path_list[i], f) for f in subfolders],
                                           parameter_list[i],seg_nuc, seg_cyto]
    
    n_sub = len(subfolders)    
     
    
    #testa se as condições estão corretas (isso sai do codigo depois)
    if len(conditions) != n_sub:
        conditions = [False] * n_sub
    
    
    # cria uma tempfile onde vão entrar os total_df, para que seja feita e remoção
    # de erros e filtragem (gating) 
    # a pasta só é eliminada após a função draw_and_save ser chamada

    temp_dir = tempfile.TemporaryDirectory()
    print(temp_dir.name)
    
    
    
    # Cria um dicionário geral de cada subpasta e roda o código nele
    # key: é o canal (nome do canal)
    # items: 
        # 0: lista dos itens da pasta
        # 1: param_dict
        # 2: booleano para saber se é o canal de segmentaçãode núcleo
        # 3: booleano para saber se é canal de segmentação do citoplasma
    
    for i in range(n_sub):
        general_dict ={}   
        for key, value in subfolder_dict.items():
            files = sorted(os.listdir(value[0][i]))
            files = [os.path.join(value[0][i], f) for f in files ]
            general_dict[key] = [files, value[1], value[2], value[3]]

        if not check_size(general_dict):
            raise("The folders contain different image number")

        total_df_nuc, total_df_cyto = analyze_dict(general_dict, segment_dict, overtime, conditions[i]) # ju usa esse pra remover outliers
        filename = os.path.basename(subfolders[i]) 
        
        if total_df_nuc is not None:
            total_df_nuc.to_pickle(os.path.join(temp_dir.name, filename + ' Nucleus-fornma.zip'))
        if total_df_cyto is not None:
            total_df_cyto.to_pickle(os.path.join(temp_dir.name, filename + ' Cytoplasm-fornma.zip'))

        # files foram jogados na temp
    
    
    #abrir todos na temp e juntar num dfzão
    #add a cada df uma coluna com nome da pasta de origem e removo erros
    complete_df_nuc = pd.DataFrame()
    complete_df_cyto = pd.DataFrame()
    for file in os.listdir(temp_dir.name):
        path_to_temp_csv = os.path.join(temp_dir.name, file) 
        df = pd.read_pickle(path_to_temp_csv)
        df["origin_folder"]= file
        if 'Nucleus-fornma' in file:
            complete_df_nuc = complete_df_nuc.append(df)
        if 'Cytoplasm-fornma' in file:
            complete_df_cyto = complete_df_cyto.append(df)
    

    #o complete df vai pra interface para remover outliers, 
    # substituindo as funções que colocarei abaixo
    from clean_dataframe import plot_and_clean, erase_df
    
  
    if complete_df_nuc.empty == False:
        h_down, h_up, v_left, v_right = plot_and_clean(complete_df_nuc, False)
        complete_df_nuc = erase_df(complete_df_nuc, h_down, h_up, v_left, v_right, False)  
        df_results_nuc, df_draw_nuc = split_dfs(complete_df_nuc, general_dict) # aqui dentro eu crio o df foci
        save_dfs(df_results_nuc, path_to_save, False)
    else: 
        df_results_nuc = None
        df_draw_nuc = None 
        
        
    if complete_df_cyto.empty == False:
        h_down, h_up, v_left, v_right = plot_and_clean(complete_df_cyto, True)
        complete_df_cyto = erase_df(complete_df_cyto, h_down, h_up, v_left, v_right, True) 
        df_results_cyto, df_draw_cyto = split_dfs(complete_df_cyto, general_dict)
        save_dfs(df_results_cyto, path_to_save, True)
    else: 
        df_results_cyto = None
        df_draw_cyto = None 
   
   
    if wants_to_save == True:
        ch_name_list_nuc =  [ f for f in df_draw_nuc if 'Image_name' in f]
        ch_name_list_nuc =  [f.replace('Image_name_', '') for f in ch_name_list_nuc]
        ch_name_list_cyto =  [ f for f in df_draw_cyto if 'Image_name' in f]
        ch_name_list_cyto =  [f.replace('Image_name_', '') for f in ch_name_list_cyto]
        if df_draw_cyto is not None and df_draw_nuc is not None:
            saving_images(df_draw_nuc, path_to_save, ch_name_list_nuc,
                          segment_dict['use_cellpose'], False) 
            saving_images(df_draw_cyto, path_to_save, ch_name_list_cyto, True, 
                          True, df_draw_nuc, segment_dict['use_cellpose'])
        elif df_draw_nuc is not None:
            saving_images(df_draw_nuc, path_to_save, ch_name_list_nuc, segment_dict['use_cellpose'], False) 
        elif df_draw_cyto is not None and df_draw_nuc is None:
            saving_images(df_draw_cyto, path_to_save, ch_name_list, True , True) 
        
    # elimina os temp dirs
    
    temp_dir.cleanup()
