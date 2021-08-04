# -*- coding: utf-8 -*-
"""
Created on Sun May 30 09:36:15 2021

@author: Luiza
"""
# A: esse código eu passei pro pessoal do lab rodar mais fácil, mas isso vai aontecer
#via interface. Como já tre expliquei, as imagens podem ter  muitos canais, então mais
#dicionários são adicionados 
#sorry pelos typos e erros de ingês e português,fica à vontade pra corrigir tbm

path_to_save= 'C:\\Users\\Luiza Cherobini\\Desktop\\kk'

ch1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\kk\\r'     #pasta contendo as pastas de imagens de um canal 
ch2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\kk\\g'   #pasta contendo as pastas de imagens de um canal 
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
                'error': 7                   #  não mudar esse
  }



#modificações a serem feitas nas imagens do canal 1. Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais
param_ch1 = {'rescale_intensity': True,
           'remove_bg' : False,
           'radius_bg': 50,
           'match_hist' : False,
           'wants_ktr' : False,
           'ring_size': 3,                      # raio do citoplasma 
           'use_ellipse': False,                # deixar True se quer usar elipse
           'wants_foci': False,
           'foci_min_size' : 5,
           'foci_max_size': None,
           'foci_min_int' : None,               # int = intensidade 
           'foci_max_int' : None,       
           'foci_proeminence' : 600           # quantas vezes mais intenso o ponto deve ser em relação ao núcleo
           }

#modificações a serem feitas nas imagens do canal 2.  Vão ser usados somente na quantificações
# o ideal seria manter os 3 primeiros iguais entre todos os canais
param_ch2 = {'rescale_intensity': True,
           'remove_bg' :False,
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
ch_name_list = [ch1_name,ch2_name]
parameter_list = [param_ch1, param_ch2]

# para cada subpasta dentro da pasta mãe, adicionar uma lista de condições
# se deixar vazia ou com numero diferente do tamanho de subpastas vai colcoar none
conditions = ['A', "B"]

#Vai checar se dados são sequencia temporal
#se for sequencia temporal, favor colocar 1 campo por pasta!
overtime = False



import time 
from main import run
ts = time.time()

run (path_to_save, ch_name_list, ch_list, ch_with_nuc, overtime, parameter_list,
     conditions, segment_dict, save_images)
te = time.time()
print ('Time: ', te-ts)