# -*- coding: utf-8 -*-
"""
Created on Sun May 30 09:36:15 2021

@author: Luiza
"""
# A: esse código eu passei pro pessoal do lab rodar mais fácil, mas isso vai aontecer
#via interface. Como já tre expliquei, as imagens podem ter  muitos canais, então mais
#dicionários são adicionados 
#sorry pelos typos e erros de ingês e português,fica à vontade pra corrigir tbm

path_to_save= '/media/luiza/DATA/paper/Registradas'

ch1_path = '/media/luiza/DATA/paper/Registradas/Red' #pasta contendo as pastas de imagens de um canal 
ch2_path = '/media/luiza/DATA/paper/Registradas/Green'  #pasta contendo as pastas de imagens de um canal 
ch3_path = '/media/luiza/DATA/Doutorado/Nicolas/RPE ETOPO/imgs teste/RPE retopo 0.2 um/Verde'

#como você nomeia o canal
ch1_name =' 53bp1'
ch2_name = 'ERK'
ch3_name ='gH2AX'
#add mais ch conforme demanda. Se usar só um, remover o restante.

ch_with_nuc = ch1_path  #canal que possui imagens do núcleo

save_images = True #recomendo deixar True


#parâmetros para encontrar núcleos. Não excluir nenhum. Valores podem ser mudados.
#Mantenham as vírgulas
#Não recomendo remoção de bg aqui
segment_dict = {'magnification': 20,   
                'pixel_size': 0.6,     
                'rescale_intensity': True,      # seta o valor mínimo para 0 e máximo para 255
                'remove_bg': True,     
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
                'use_cellpose': False,          # usar o cellpose pra detecção nuclear. Parametros do cellpose abaixo
                'invert': False,                # invert image pixel intensity before running network (if True, image is also normalized)
                'normalize': True,              # normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel
                'diameter': 5 ,               # if set to None, then diameter is automatically estimated if size model is loaded
                'net_avg': True,                # runs the 4 built-in networks and averages them if True, runs one network if False
                'resample': True,               # run dynamics at original image size (will be slower but create more accurate boundaries)
                'flow_threshold': 0.4,          # flow error threshold (all cells with errors below threshold are kept)
                'mask_threshold': 0.0 ,         # all pixels with value above threshold kept for masks, decrease to find more and larger masks
                'use_gpu': True
    }



#modificações a serem feitas nas imagens do canal 1. Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais
param_ch1 = {'rescale_intensity': True,
           'remove_bg' : True,
           'radius_bg': 40,
           'match_hist' : False,
           'wants_ktr' : False,
           'ring_size': 3,                      # raio do citoplasma 
           'use_ellipse': False,                # deixar True se quer usar elipse
           'wants_foci': False,
           'foci_min_size' : 7,
           'foci_max_size': None,
           'foci_min_int' : None,               # int = intensidade 
           'foci_max_int' : None,       
           'foci_proeminence' : 1.2           # quantas vezes mais intenso o ponto deve ser em relação ao núcleo
           }

#modificações a serem feitas nas imagens do canal 2.  Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais
param_ch2 = {'rescale_intensity': True,
           'remove_bg' : True,
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
           'foci_proeminence' : 1.3
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
           'foci_proeminence' : 1.3
           }  


#se existirem mais canais, mais params devem ser adicionados.
#se existirem menos canais, parâmetros devem ser removidos

ch_path_list = [ch1_path, ch2_path]#, ch3_path]
ch_name_list = [ch1_name, ch2_name] #, ch3_name]
parameter_list = [param_ch1,  param_ch2] #, param_ch3]

# para cada subpasta dentro da pasta mãe, adicionar uma lista de condições
# se deixar vazia ou com numero diferente do tamanho de subpastas vai colcoar none
conditions = [] #'ETO', 'GEM', 'TAXOL', 'TAXOL+CARBO']#, "B"]

#Vai checar se dados são sequencia temporal
#se for sequencia temporal, favor colocar 1 campo por pasta!
overtime = False



import time 
from run import run
%matplotlib 
ts = time.time()

run (path_to_save, ch_name_list, ch_path_list, ch_with_nuc, overtime, parameter_list,
     conditions, segment_dict, save_images)
te = time.time()

import os
with open(os.path.join(path_to_save,"parameters.txt"), 'w') as f: 
    f.write('\n'+ 'Segmentation parameters \n')
    for key, value in segment_dict.items(): 
        f.write('%s:%s\n' % (key, value))
    f.write('\n'+ 'Detection parameters \n')    
    for i in range(len(ch_name_list)):
        f.write('\n'+ str(ch_name_list[i] + '\n'))
        for key, value in parameter_list[i].items():
            f.write('%s:%s\n' % (key, value))

    f.close()
    
    
print ('Time: ', te-ts)