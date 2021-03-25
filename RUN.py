# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 15:08:39 2021

@author: Luiza
"""

import os
from analyze_folder_new import generate_dfs

'''IMPORTANTE:
    1. Todas as instruções estarão nessa cor;
    2. Sempre que for colocar o caminho de uma psta, coloque entre aspas e com duas barras 
    separando. Exemplo " D:\\Doutorado\\imagens incucyte kaka\\Meki\\Red"  
    3. Você não precisa ter dois canais de fluorescência.
    4. TODAS as pastas devem estar organizadas em subpastas onde a pasta mãe 
    corresponde a um canal de flurescência diferente. Por exemplo:
        C:\\Pasta\\Imagens no Canal 1\\Pasta 1  (pasta 1 corresponde a um tempo ou condição, etc)
        C:\\Pasta\\Imagens no Canal 1\\Pasta 2
        C:\\Pasta\\Imagens no Canal 2\\Pasta 1  
        C:\\Pasta\\Imagens no Canal 2\\Pasta 2
    (tipo no diagrama abaixo. Por mais que só exista uma pasta em cada canal, ela 
     deve estar dentro de outra)
        
                                    PASTA
                          ____________|______________
                         |                          |
                      CANAL 1                   CANAL 2
         _____________|__________         ___________|____________
        |            |          |        |           |           |
    PASTA1       PASTA2     PASTA N   PASTA 1      PASTA 2     PASTA N
                         
    5. o nome das pastas NÂO PODE TER ACENTO - nossa foi um inferno descobrir que não rodava por isso
    6. Se o código der erro, printa e me envia no wpp
    7. Se por acaso entrar em loop você pode parar tudo apertando ctrl+c
    8. qualquer coisa me chame no whats '''

###############################################################################################

'''  PASSO 1: 
    Adicionar a pasta correpondente ao canal que possui marcação de núcleos no main_dir1.
No exemplo acima, a pasta a ser adicionada é a C:\\Pasta\\Imagens no canal 1
*Essa funçaõ vai digitar automaticamente o caminho de todas as pastas dentro de uma pasta,
no caso do exemplo, ela vai listar as pastas 1, 2, N ...
*Se você possui imagens somente em um canal de fluorescência, deixe a segunda pasta com o
valor None. Caso contrário, adicione a pasta do canal 2'''

#main_dir1 ="C:\\Pasta\\Imagens no canal 1"  #Troque essa info pela sua pasta
#main_dir2 = "C:\\Pasta\\Imagens no canal 2" # ou substitua por None

main_dir1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\video kaka\\r'
main_dir2= 'C:\\Users\\Luiza Cherobini\\Desktop\\video kaka\\g'

folder_nuc_list = []
for i in os.listdir(main_dir1):
    full_path = os.path.join(main_dir1, i)
    folder_nuc_list.append(full_path)
        
if main_dir2 is not None:    
    folder_2_list = []
    for i in os.listdir(main_dir2):
        full_path = os.path.join(main_dir2, i)
        folder_2_list.append(full_path)
else:
    folder_2_list = []



'''`Passo 2: 
    Escolha uma pasta para salvar os resultados. Pode ser qualquer pasta
    '''   
path_to_save = 'C:\\Users\\Luiza Cherobini\\Desktop\\video kaka' #isso é só um exemplo 



"""PASSO 3:
    Se você deseja salvar as imagens contornadas, deixe como True, caso contrário, coloque False""
    """
save_image = True



'''Passo 4:
    Aqui você deve informar em qua aumento essas imagens foram realizadas (magnificação) e o
tamanho do píxel em micrômetros. Tamanho do píxel é uma informação vem junto ao equipamento 
e nas metainformações da imagem. Se não souber qual o pixel size, abra a imagem no imageJ e vá em
Image> Show Info
    '''

magnification = 4
pixel_size = 1


''' Passo 5:
    Se você quer que análise de raio citoplasmático seja realizada, digite True
    Se você deseja que pontos nucleares sejam contados, digite True. Caso contrário, digte False.
    Se os ontos nucleares estiverem em canal diferente do canal de marcação de núcleos ( por
 exemplo núcleos marcados em DAPI e o 53bp1 está marcado em vermelho), digite True.
    '''
wants_ktr = True
wants_foci =  False
foci_other_channel = False


'''Agora é só rodar o código.
Não mexa em nada abaixo dessa linha.
Qualquer coisa me chama'''

###################################################################

total_dict = {}
df_list = []

for n in range(len(folder_nuc_list)):
    folder_nuc_items = [os.path.abspath(os.path.join(folder_nuc_list[n],i)) for i in os.listdir(folder_nuc_list[n])]
    foldername = str(os.path.basename(folder_nuc_list[n]))  
    #criar aqui a pasta
    folder_save_1 = None
    folder_save_2 = None
    if save_image == True:
        os.mkdir(path_to_save + '\\' + foldername + ' Contours')
        folder_save_1 = path_to_save + '\\' + foldername + ' Contours\\'
    
    if len(folder_2_list) == 0 :
        if pixel_size is None:
           df_foci, df_nuc, df_categories, cells_dict  = generate_dfs(folder_nuc_items, 
                                    wants_foci, wants_ktr,foci_other_channel, magnification,
                                    path_to_save, save_image, folder_save_1, folder_save_2)
        else:
           df_foci, df_nuc, df_categories, cells_dict  = generate_dfs(folder_nuc_items, 
                                    wants_foci, wants_ktr,foci_other_channel, magnification,
                                    path_to_save, save_image, folder_save_1, folder_save_2,
                                    pixel_size = pixel_size)
            
    else:
        foldername2 = str(os.path.basename(folder_2_list[n]))
        folder2_items = [os.path.abspath(os.path.join(folder_2_list[n],i)) for i in os.listdir(folder_2_list[n])]
        if save_image == True:
            os.mkdir(path_to_save + '\\' + foldername2 + ' Contours')    
            folder_save_2 = path_to_save + '\\' + foldername2 + ' Contours\\'
       
        if pixel_size is None:
           df_foci, df_nuc, df_categories, cells_dict  = generate_dfs(folder_nuc_items, 
                                    wants_foci, wants_ktr,foci_other_channel, magnification,
                                    path_to_save, save_image, folder_save_1, folder_save_2,
                                    folder2_items = folder2_items)
        else:
           df_foci, df_nuc, df_categories, cells_dict  = generate_dfs(folder_nuc_items, 
                                    wants_foci, wants_ktr,foci_other_channel, magnification,
                                    path_to_save, save_image, folder_save_1, folder_save_2,
                                    pixel_size = pixel_size, folder2_items = folder2_items)
            
    
    df_nuc.to_csv(path_to_save+ '\\' + foldername + '.csv', sep='\t')    #mudei isso pro tab
    df_list.append(df_nuc)        
   #total_dict[foldername] = [df_foci, df_nuc, df_categories, cells_dict]
    
  #aqui ele pergunta se a pasta que ele fez é controle. Se sim já calcula o aro e guarda essa elipse
  #de resto chamar um código de plotaar
  #plota NMA, cada dado nos gráficos de pontinhos e em violinos, plota pontos
  # pergunta se é timescle, se sim plota médias com IC ao longo do tempo 
  
        
        
        
    
#aqui eu faço toda uma parte de plotar os gráficos chamando eles de outras funções  