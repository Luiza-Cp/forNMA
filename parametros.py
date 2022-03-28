#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 16:44:10 2022

@author: luiza
"""


path_to_save= '/media/luiza/DATA/àrea de trabalho/teste (del)/2 canais só cyto'

#adicionar todos os ccaminhos para os canais nessa lista
channel_path_list = ['/media/luiza/DATA/àrea de trabalho/teste (del)/2 canais só cyto/r' ,
                     '/media/luiza/DATA/àrea de trabalho/teste (del)/2 canais só cyto/g' ]


#add nessa lista todos os nomes dos canais das pastas acima
channel_names_list = ['53bp1', 'erk']
conditions = ['Control'] # daseado no numero de pastas dentro do canal
ch_with_nuc = 'None'  #canal que possui imagens do núcleo-> se for analisar só citoplasma ele é None

save_images = True #recomendo deixar True
overtime = False

#parâmetros para encontrar núcleos. Não excluir nenhum. Valores podem ser mudados.
#Mantenham as vírgulas
#Não recomendo remoção de bg aqui
segment_dict = {'magnification': 20,   
                'pixel_size': 0.6,     
                'rescale_intensity': True,      # seta o valor mínimo para 0 e máximo para 255
                'remove_bg': False,     
                'radius_bg': 40,                # raio da rolling-balll (igual ao imageJ)
                'threshold':'triangle',        # Descrição das opções vem abaixo 
                'offset': 5,                    # Deve ser usado para os thresholds locais 
                'blur': 13,                     # o quanto deve suavizar o contorno do núcleo
                'adjust_size': -1,               # Expandir ou diminuir o contorno (número negativo para diminuir)
                'cut_edges': 0.9,            # o quanto deve forçar o corte entre os núcleos, pode ser False 
                'shape':  0.88,                 # remove células com formatos muito loucos
                'eccentricity': None,           # Vai de 0 a 1. Valores mais próximos de 0 represenntam mais circular, mais perto de 1 é mais oval
                'min_size': None, 
                'max_size': None, 
                'min_radius': None, 
                'max_radius': None, 
                'fast_detection': False,
                'weakly_labeled': False ,        # setar como true se tiverem marcações fracas e baixa densidade de cell
                'use_cellpose':True,          # usar o cellpose pra detecção nuclear. Parametros do cellpose abaixo
                'invert': False,                # invert image pixel intensity before running network (if True, image is also normalized)
                'normalize': True,              # normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel
                'diameter': 5 ,               # if set to None, then diameter is automatically estimated if size model is loaded
                'net_avg': True,                # runs the 4 built-in networks and averages them if True, runs one network if False
                'resample': True,               # run dynamics at original image size (will be slower but create more accurate boundaries)
                'flow_threshold': 0.4,          # flow error threshold (all cells with errors below threshold are kept)
                'mask_threshold': 0.0 ,         # all pixels with value above threshold kept for masks, decrease to find more and larger masks
                'use_gpu': True,
                'model_for_cyto': 'cyto2',     #cellpose model for cytoplasmatic measures
                'cyto_diameter': 70 ,               # if set to None, then diameter is automatically estimated if size model is loaded
                'cyto_flow_threshold': 0.6,          # flow error threshold (all cells with errors below threshold are kept)
                'cyto_mask_threshold': 0.0 ,   
    }



#modificações a serem feitas nas imagens do canal 1. Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais

param_ch1 = {'rescale_intensity': True,
           'remove_bg' : False,
           'radius_bg': 40,
           'match_hist' : False,
           'wants_ktr' : False,
           'ring_size': 3,                      # raio do citoplasma 
           'use_ellipse': False,                # deixar True se quer usar elipse
           'wants_foci': True,
           'foci_min_size' : 7,
           'foci_max_size': None,
           'foci_min_int' : None,               # int = intensidade 
           'foci_max_int' : None,       
           'foci_proeminence' : 1.2,            # quantas vezes mais intenso o ponto deve ser em relação ao núcleo
           'cytoplasm' : True
           }

#modificações a serem feitas nas imagens do canal 2.  Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais
param_ch2 = {'rescale_intensity': True,
           'remove_bg' : False,
           'radius_bg': 40,
           'match_hist' : False,
           'wants_ktr' : True,
           'ring_size': 3,
           'use_ellipse': True,
           'wants_foci': False,
           'foci_min_size' : 7,
           'foci_max_size': None,
           'foci_min_int' : None,
           'foci_max_int' : None,
           'foci_proeminence' : 1.3,
           'cytoplasm' : True
           }  

param_ch3 = {'rescale_intensity': False,
           'remove_bg' : False,
           'radius_bg': 50,
           'match_hist' : False,
           'wants_ktr' : False,
           'ring_size': 3,
           'use_ellipse': True,
           'wants_foci': True,
           'foci_min_size' : 7,
           'foci_max_size': None,
           'foci_min_int' : None,
           'foci_max_int' : None,
           'foci_proeminence' : 1.3,
           'cytoplasm' : False
           }  


#se existirem mais canais, mais params devem ser adicionados.
parameter_list = [param_ch1, param_ch2]



parameters = path_to_save, channel_names_list, channel_path_list, ch_with_nuc, overtime, parameter_list, conditions, segment_dict, save_images

