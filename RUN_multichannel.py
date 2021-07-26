# -*- coding: utf-8 -*-
"""
Created on Sun May 30 09:36:15 2021

@author: Luiza
"""
# A: esse código eu passei pro pessoal do lab rodar mais fácil, mas isso vai aontecer
#via interface. Como já tre expliquei, as imagens podem ter  muitos canais, então mais
#dicionários são adicionados 
#sorry pelos typos e erros de ingês e português,fica à vontade pra corrigir tbm

path_to_save=  'C:\\Users\\Luiza Cherobini\\Desktop\\kk'

ch1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\kk\\r'     #pasta contendo as pastas de imagens de um canal 
ch2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\kk\\r'   #pasta contendo as pastas de imagens de um canal 
#ch3 = 'C:\\Users\\Luiza Cherobini\\Documents\\Nicolas\\Run\\gH2AX'

#como você nomeia o canal
ch1_name = "red"
ch2_name = 'green'
ch3_name ='gH2AX'
#add mais ch conforme demanda. Se usar só um, remover o restante.

ch_with_nuc = ch1  #canal que possui imagens do núcleo

save_images = True #recomendo deixar True


#parâmetros para encontrar núcleos. Não excluir nenhum. Valores podem ser mudados.
#Mantenham as vírgulas
#Não recomendo remoção de bg aqui
segment_dict = {'magnification': 20,   
                'pixel_size':  0.6,     
                'rescale_intensity': True,      # seta o valor mínimo para 0 e máximo para 255
                'remove_bg': False,     
                'radius_bg': 0,                 # raio da rolling-balll (igual ao imageJ)
                'threshold': 'triangle',        # Descrição das opções vem abaixo 
                'offset': 0,                    # Deve ser usado para os thresholds locais 
                'blur': 12,                     # o quanto deve suavizar o contorno do núcleo
                'adjust_size': 0,               # Expandir ou diminuir o contorno (número negativo para diminuir)
                'cut_edges':  0.7,              # o quanto deve forçar o corte entre os núcleos 
                'shape':  0.88,                 # remove células com formatos muito loucos
                'eccentricity': None,           # Vai de 0 a 1. Valores mais próximos de 0 represenntam mais circular, mais perto de 1 é mais oval
                'min_size': None, 
                'max_size': None, 
                'min_radius': None, 
                'max_radius': None, 
                'fast_detection': False,
                'error': None                   #  não mudar esse
  }



#modificações a serem feitas nas imagens do canal 1. Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais
param_ch1 = {'rescale_intensity': True,
           'remove_bg' : True,
           'radius_bg': 50,
           'match_hist' : False,
           'wants_ktr' : False,
           'ring_size': 3,                      # raio do citoplasma 
           'use_ellipse': False,                # deixar True se quer usar elipse
           'wants_foci': True,
           'foci_min_size' : 5,
           'foci_max_size': None,
           'foci_min_int' : None,               # int = intensidade 
           'foci_max_int' : None,       
           'foci_proeminence' : 600           # quantas vezes mais intenso o ponto deve ser em relação ao núcleo
           }

#modificações a serem feitas nas imagens do canal 2.  Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais
param_ch2 = {'rescale_intensity': True,
           'remove_bg' :True,
           'radius_bg': 50,
           'match_hist' : False,
           'wants_ktr' : True,
           'ring_size': 3,
           'use_ellipse': True,
           'wants_foci': False,
           'foci_min_size' : 5,
           'foci_max_size': None,
           'foci_min_int' : None,
           'foci_max_int' : None,
           'foci_proeminence' : None
           }  

param_ch3 = {'rescale_intensity': False,
           'remove_bg' :False,
           'radius_bg': 40,
           'match_hist' : False,
           'wants_ktr' : False,
           'ring_size': 3,
           'use_ellipse': True,
           'wants_foci': True,
           'foci_min_size' : 7,
           'foci_max_size': None,
           'foci_min_int' : None,
           'foci_max_int' : None,
           'foci_proeminence' : 100
           }  


#se existirem mais canais, mais params devem ser adicionados.
#se existirem menos canais, parâmetros devem ser removidos

ch_list = [ch1, ch2]
ch_name_list = [ch1_name, ch2_name]
parameter_list = [param_ch1, param_ch2]

# para cada subpasta dentro da pasta mãe, adicionar uma lista de condições
# se deixar vazia ou com numero diferente do tamanho de subpastas vai colcoar none
conditions = ['controle']

#Vai checar se dados são sequencia temporal
#se for sequencia temporal, favor colocar 1 campo por pasta!
overtime = False

##### That's it #####


import os
from analyze_multichannel import check_size, analyze_dict, split_dfs, draw_and_save
import time 
ts = time.time()

# cria um dicionário da pasta
# key: nome de cada canal
#values: possui 3 valores
    # 0: uam lista com o caminho de todas as pastas nesse canal
    # 1: o param_dict desse canal
    # 2: bool (informa se o canal é o de segmentação ou não)

subfolder_dict = {}
for i in range(len(ch_name_list)):
    if ch_with_nuc == ch_list[i]:
        seg = True 
    else:
        seg = False
    subfolders = sorted((os.listdir(ch_list[i])))
    subfolder_dict[ch_name_list[i]] = [[os.path.join(ch_list[i], f) for f in subfolders],
                                       parameter_list[i],seg]

n_sub = len(subfolders)    
 

#testa se as condições estão corretas (isso sai do codigo depois)
if len(conditions) == n_sub:
    conditions = conditions
else:
    conditions = [None] * n_sub


# Cria um dicionário geral de cada subpasta e roda o código nele
# key: é o canal (nome do canal)
# items: 
    # 0: lista dos itens da pasta
    # 1: param_dict
    # 2: booleano para saber se é de segmentação

for i in range(n_sub):
    general_dict ={}   
    for key, value in subfolder_dict.items():
        files = sorted(os.listdir(value[0][i]))
        files = [os.path.join(value[0][i], f) for f in files ]
        general_dict[key] = [files, value[1], value[2]]
    
    size = check_size(general_dict)
    if size == False:
        raise("The folders contain different image number")
    else:
    
        total_df = analyze_dict(general_dict, segment_dict, overtime, conditions[i]) # ju usa esse pra remover outliers
        df_results, df_cnt = split_dfs(total_df, general_dict)
        draw_and_save(df_cnt, df_results, path_to_save, os.path.basename((value[0][i])),
              general_dict, save_images)       

te = time.time()
print ('Time: ', te-ts)
