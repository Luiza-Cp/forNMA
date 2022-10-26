#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 30 08:03:13 2021

@author: luiza
"""
import pandas as pd
import math 
from scipy.optimize import linear_sum_assignment


pcp20 = '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/Measurements_Nuclei.csv'
pij20 = '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/NMA_organizado.csv'
pfornma20 = '/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/Fornma_results_blur3.csv'


cp = pd.read_csv(pcp20,  encoding='latin-1')
ij = pd.read_csv(pij20)
fornma = pd.read_csv(pfornma20) 


# organizar os dfs antes ##########################
cp['Aspect'] = cp['AreaShape_MajorAxisLength']/ cp['AreaShape_MinorAxisLength']

cp = cp[['Image', 'ObjectNumber',  'AreaShape_Center_X',
         'AreaShape_Center_Y' , 'AreaShape_Area', 'Aspect',
         'AreaShape_Extent', 'Condition']]

ij = ij[['Image', 'Cell', 'X', 'Y', 'Area', 'Aspect', 'Ar_box', 'Condition',
         'Radius_ratio', 'Roundness', 'NII']]
fornma = fornma[["Image_name_Dapi", 'Cell', "X", "Y", 'Area', 'Aspect', 'Extent', 
                'Condition' ,  'Radius_ratio', 'Roundness', 'NII']]


fornma.dropna(inplace=True)
#normalizar intensidade média 
# divido a int máxima da imagem pela intensidade média do núcleo 

col_names =['Image', 'Cell', 'X', 'Y', 'Area', 'Aspect', 'Extent','Condition', 
            'Radius_ratio', 'Roundness', 'NII'] 
cp.columns =col_names
ij.columns= col_names
fornma.columns = col_names


ij = ij.reset_index()
cp = cp.reset_index()
fornma = fornma.reset_index()


#cp['Image'] = cp['Image'].str.replace(' 40x','')
#cp['Image'] = cp['Image'].str.replace('–','-')
#ij['Image'] = ij['Image'].str.replace('–','-')
#fornma['Image'] = fornma['Image'].str.replace('–','-')


################




def calculate_dist_matrix(df1: pd.DataFrame, # dataframe com as medidas de núcleo 1 -> vira row (idx))
                          df2: pd.DataFrame, # dataframe com medidas de nucleo 2 -> vira coluna
                                    ):
    """ 
    Calcula matriz de distâncias entre um núcleo em uma imagem contra
    todos os núcleos na outra imagem.
    Retorna um dicionário onde cada key corresponde a uma imagem e o valor a um dataframe 
    com a matriz de distancia. 
    O índice de cada df corresponde à coluna cell do df1 e as colunas de cada df
    correspondem à coluna cell do df2.
    * fiz em formato de dataframe poris a proxima função retorna indices, então eu uso
    esses índices para encontrar qual seria o valor da célula nos indices e colunas do df
    """
    
    img_list = list(df1['Image'])
    img_list.extend(list(df2['Image']))
    img_list = list(set(img_list))
    
    df_im_dict  ={}
    for image in img_list:
        dfa = df1[df1['Image'] == image]
        dfb = df2[df2['Image'] == image]
        dfc = pd.DataFrame(index=dfa['Cell'], columns= dfb["Cell"])
        
        for col in dfc.columns:
            #print (col, 'co')
            x1 = dfb.loc[dfb['Cell'] == col, 'X'].values[0]
            y1 = dfb.loc[dfb['Cell'] == col, 'X'].values[0]
            dist_list = []
            for idx in dfc.index:
                #print (idx, 'id')
                x2 = dfa.loc[dfa['Cell'] == idx, 'X'].values[0]
                y2 = dfa.loc[dfa['Cell'] == idx, 'X'].values[0]
                dist = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                dist_list.append(dist)
            dfc[col] = dist_list
        df_im_dict[image] = dfc
    return df_im_dict
# retorna um dicionário onde a chave é o nome da imagem e o valor é um dataframe 
# o df do valor contem o numero da célula nos indices e colunas e vai ser usado 
# pra comparar os valores de saída do np 




def get_matches(dic: dict, # didiconário com 
                name1: str, # nome do row (primeiro item passado na função anterior)
                name2: str, #nome da coluna (segundo itempda função anterior)
                ): 
    
    ''' 
        Aplica o algoritmo  de linear sum assignment aos dataframes qarmazenados
    no value do dicionário.
    Retorna um dataframe com as imagens de origem e os pares de células 
    (para obter os pares ele usa os índices vindos do linear_sum_assignment
    para procurar a celula correspondente no index e row do dataframe)
    '''
    df_pair_list = []
        
    for key, value in dic.items():
                
        row_ind, col_ind = linear_sum_assignment(value)
        # essa linha pega o índice do dataframe (o valor da célula) com base no 
        # row_ind, que é o indíce do np.array (ordem em que as células parecem, mas não
        #necessariamnete a célula em si)
        row = [value.iloc[[f]].index[0] for f in row_ind] 
        
        # essa linha pega a coluna do df (o valor da célula do dataframe 2 (name2)) com base no 
        # col_ind, que é o indíce do np.array (ordem em que as células parecem, mas não
        # necessariamnete a célula em si)
        col = [value[value.columns[f]].name for f in col_ind]
        
        
        #cria dataframe pareano numero das células que correspondem nas duas iamges 
        # e add o nome da imagem.
        # a coluna possui o nome do método de detecção
        df = pd.DataFrame()
        df['Image'] = [key] *len(col)
        df[name1] = row
        df[name2] = col
        df_pair_list.append(df)
    
    pairs_df = pd.concat(df_pair_list)
    return pairs_df

# pairs_df é um dfzão com todos os pares e nomes da imagem de origem


def get_paired_dfs(df_match, # df com as células pareadas
                   df1, # peimeiro df (o que nomeia a primeira coluna)
                   df2,): # o df que nomeia a segunda coluna
    '''
    Pega a ordem dos matches e reorganiza os dataframes, removendo linhas de células
    não retornadas pelo linear_sum_alignemnt. Retorna os dois dataframes iniciais,
    agora organizadfos
    '''

    new_df1_list = []
    new_df2_list = []
    images = list(set(df_match.Image))
    for img in images:
        match= df_match.loc[df_match['Image'] == img]
        
        a = df1.loc[df1['Image'] == img]
        a.Cell = a.Cell.astype("category")
        a.Cell.cat.set_categories(list(match[match.columns[1]]), inplace = True)
        a = a.dropna()
        a = a.sort_values(["Cell"])
        new_df1_list.append(a)

        b = df2.loc[df2['Image'] == img]
        b.Cell = b.Cell.astype("category")
        b.Cell.cat.set_categories(list(match[match.columns[2]]), inplace = True)
        b = b.dropna()
        b = b.sort_values(["Cell"])
        new_df2_list.append(b)

    new_df1= pd.concat(new_df1_list)
    new_df2 = pd.concat(new_df2_list)
    
    new_df1.rename(columns=lambda x: x +'_' + df_match[df_match.columns[1]].name, inplace=True)
    new_df2.rename(columns=lambda x: x +'_' + df_match[df_match.columns[2]].name, inplace=True)

        
    return new_df1, new_df2


def pair_df(df1: pd.DataFrame, # fornecer 2 dfs e o nome e cada df (grupo de origem, ex: imageJ, cellProfiler)
            df2: pd.DataFrame,
            name1: str,
            name2: str
            ):
    
    """ Pega 2 dfs e retorna eles reordenados e com o mesmo número de linhas,
    de modo que cada linha de um df corresponda à mesma linha do outro """
    
    dict_distances = calculate_dist_matrix (df1, df2)
    matches = get_matches(dict_distances, name1, name2)
    new_df1, new_df2 =get_paired_dfs(matches, df1, df2)
    return new_df1, new_df2

##### chamei assim ó  #######
ij_cp, cp_ij =  pair_df(ij, cp, 'IPP', 'CP') 
ij_fornma, fornma_ij = pair_df(ij,fornma, 'IPP', 'FORNMA') 
cp_fornma, fornma_cp = pair_df(cp, fornma, 'CP', 'FORNMA') 


ij_cp.to_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/blur 3/ImageJ (organized against Cellprofiler).csv')
ij_fornma.to_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/blur 3/IPP (organized against forNMA).csv')
cp_ij.to_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/blur 3/Cellprofiler (organized against ImageJ).csv')
cp_fornma.to_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/blur 3/Cellprofiler (organized against forNMA).csv')
fornma_cp.to_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/blur 3/forNMA (organized against Cellprofiler).csv')
fornma_ij.to_csv('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Validations/NMA/paired_df/blur 3/forNMA (organized against IPP).csv')
###############