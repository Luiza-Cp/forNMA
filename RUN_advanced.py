# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 10:15:39 2021

@author: Luiza
"""

import os
from analyze_folder_advanced import generate_dfs

'''IMPORTANTE:
    1. Todas as instruções estarão nessa cor;
    2. PARA WINDOWS: Sempre que for colocar o caminho de uma psta, coloque entre aspas 
    e com duas barras separando. Exemplo " D:\\Doutorado\\imagens incucyte kaka\\Meki\\Red"  
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

main_dir1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\ju\\r'  #Troque essa info pela sua pasta
main_dir2 = None#'C:\\Users\\Luiza Cherobini\\Desktop\\ju\\g'

#main_dir1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\video kaka\\r'
#main_dir2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\video kaka\\g'


folder_nuc_list = []
if os.path.exists(main_dir1) == False:
    raise ValueError ('This file do not exists: '+ main_dir1)
for i in [f for f in os.listdir(main_dir1) if not f.startswith('.')]:
    full_path = os.path.join(main_dir1, i)
    folder_nuc_list.append(full_path)

        
if main_dir2 is not None: 
    if os.path.exists(main_dir2) == False:
        raise ValueError ('This file do not exists: ' +  main_dir1)
    folder_2_list = []
    for i in [f for f in os.listdir(main_dir2) if not f.startswith('.')]:
        full_path = os.path.join(main_dir2, i)
        folder_2_list.append(full_path)
else:
    folder_2_list = []
    
    '''`Passo 2: 
    Escolha uma pasta para salvar os resultados. Pode ser qualquer pasta
    '''   
path_to_save = 'C:\\Users\\Luiza Cherobini\\Desktop\\ju' #isso é só um exemplo 



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

magnification = 20
pixel_size = 0.6


''' Passo 5:
    Se você quer que análise de raio citoplasmático seja realizada, digite True
    Se você deseja que pontos nucleares sejam contados, digite True. Caso contrário, digte False.
    Se os ontos nucleares estiverem em canal diferente do canal de marcação de núcleos ( por
 exemplo núcleos marcados em DAPI e o 53bp1 está marcado em vermelho), digite True.
    '''
wants_ktr = False
wants_foci =  False
foci_other_channel = False


''' CONFIGURAÇÕES AVANÇADAS
    ok galera vcs vão poder mexer nas avançadas.
    Vou deixar aqui as coisas que podem ser mudadas e na parte de baixo do código
vão ter instruções de como fazer. Peço perdão desde já por eventuais bugs e falhas
porque ficou pornto na pressa. Obg pela compreensão.

THRESHOLD
vocês possuem 11 opções: 'isodata',  'li',  'mean',  'minimun',   'otsu',
    'triangle',   'yen',  'median',  'multiotsu' ------e tem mais dois 
    
    CUIDADO: as duas opções abaixo devem vir acompanhadas da opção OFFSET
    que é um número. Então tem que setar offset = 2 (ou qq outro número)
    Essas duas também demoram mais tempo pra rodar.
    
    'local_mean',  'local_gaussian'
 
para aplicar, é só digitar, por exemplo: threshold = 'mean'    
 
BLUR: é o quanto o contorno núcleo vai ser suavizado (pra não ficar todo irregular/comido)
- colocar um valor de 0 a 15: Exemplo: blur = 7

ADJUST SIZE: reduz ou aumenta o tamanho de todos os contornos. Valores negativos reduzem, 
valores positivos aumentam. Ex.: adjust_size = 2

CUT EDGES: o quanto o forNMA vai forçar um corte quando tem uma célula irregular
que parece ser uma divisão celular. Deve ser um valor de 0 a 1.
exemplo:  cut_edges = 0.7

SHAPE: remove núcleos com formato muito estranho. Deve ser um valor de 0-1 no qual
1 equivale a um núcleo que possui uma envoltória convexa perfeita.
Ex.:  shape = 0.8

ECCNTRICITY: remove núcleos mais alongados. Deve ser um valor de 0-1 onde
0 equivale a um círculo perfeito.
Exemplo:  eccentricity = 0.3

MIN SIZE e MAX SIZE: área máxima e mínima EM PÍXELS.
Ex.: min_size = 500, max_size = 3000

MIN RADIUS e MAX RADIUS = raio máximo e mínimo EM PÍXELS.
Ex.: min_radius = 100, max_radius= 300


FAST_DETECTION 

deve ser TRUE ou FALSE
Criei isso porque a análise ficou demorada. Aí se as fotos estão boas ou não vão ser usadas
pro KTR, é melhor ativar.
Ex>: fast_detection = True'''

###################################################################

if os.path.exists(path_to_save) == False:
    raise ValueError ('This file do not exists: '+ path_to_save)

total_dict = {}
df_list = []

for n in range(len(folder_nuc_list)):
    folder_nuc_items = sorted([os.path.abspath(os.path.join(folder_nuc_list[n],i)) for i in 
                      [f for f in os.listdir(folder_nuc_list[n]) if not f.startswith('.')]])
    foldername = str(os.path.basename(folder_nuc_list[n]))

    #criar aqui a pasta
    folder_save_1 = None
    folder_save_2 = None
    if pixel_size == None:
        pixel_size = 0.5
    
    if save_image == True:
        folder_save_1  = os.path.join(path_to_save, foldername + " Contours")
        os.mkdir(folder_save_1)
       
    if len(folder_2_list) == 0:
        folder_save_2 = None
        folder2_items = None  
    else: 
        foldername2 = str(os.path.basename(folder_2_list[n]))
        folder2_items = sorted([os.path.abspath(os.path.join(folder_2_list[n],i)) for i in 
                         [f for f in os.listdir(folder_2_list[n]) if not f.startswith('.')]])
        if len(folder2_items) != len(folder_nuc_items):
            raise IndexError ("The folders must contain the same number of files")
        if save_image == True:
            folder_save_2  = os.path.join(path_to_save, foldername2 + " Contours")
            os.mkdir(folder_save_2)
        
        ''' Aqui é o local onde vocês ativam aquelas coisas. Elas devem ser adicionadas 
dentro do parênteses, após o foder_save2, entre vírgulas. vou colocar um exemplo aqui, 
mas vocês podem add quantas e quais quiserem.

df_foci, df_nuc, df_categories, cells_dict = generate_dfs(folder_nuc_items, path_to_save,
                save_image, folder_save_1, magnification, folder2_items = folder2_items, 
                folder_save_2 = folder_save_2, fast_detection = True, blur = 5, 
                min_size = 500)

     '''    
    
    
    df_foci, df_nuc, df_categories, cells_dict = generate_dfs(folder_nuc_items, path_to_save,
                save_image, folder_save_1, magnification, folder2_items = folder2_items, 
                folder_save_2 = folder_save_2, wants_ktr =wants_ktr, wants_foci =wants_foci)
    
    
    saving = os.path.join(path_to_save, foldername + '.csv')
    df_nuc.to_csv(saving, sep='\t', index=False)    #mudei isso pro tab
    df_list.append(df_nuc)     
    print ("Pasta", folder_nuc_list[n] + ":", "FEITO")