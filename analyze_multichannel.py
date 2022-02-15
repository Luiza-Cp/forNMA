# -*- coding: utf-8 -*-
"""
Created on Sun May 16 20:11:52 2021

@author: Luiza
"""
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from initializing_functions_multichannel import load_image
from find_contours_multichannel import find_contours
from Morphology_class import Morphology 
from Cell_class_multichannel import Cell
import numpy as np
from typing import List, Optional, Tuple
import os
import cv2 as cv
from cellpose_integration import run_cellpose


#channel dict: key = channel (1, 2 3, 4 ..)
#value = list  ([files], dict{parameters do canal}, bool)
# o bool só pode ter um true, que é o canal que vai ser usado pra segmentar nuc

def check_size(ch_dict: dict)-> bool:
    """ Sorts files and checks if all file_lists have the same size. """
    
    len_files = len (list(ch_dict.values())[0][0])      #first file list
    for key, value in ch_dict.items():
        value[0] = sorted(value[0])
        if len(value[0]) != len_files:
            
            return False
        
    return True
     

#nessa função que tenho que mexer para add foci     
def measure_image(
        path_image: str, 
        dict_param: dict,
        ref: np.ndarray, 
        contour_list: List[np.ndarray],
        mag: int,
        ps: float,
        channel_name: str
)-> pd.DataFrame:
    
    """
    Loads an image - given by its path - using parameters present in dict_param.
    Uses de ref as reference for matchiong histograms during load.
    Creates Cells based on parameters present at dict_param and returns a
    dataframe with its measurements.
    """
    
    dp = dict_param 
    name = os.path.basename(path_image)
    img_to_measure = load_image(path_image, rescale_intensity = dp['rescale_intensity'],
                       remove_bg = dp['remove_bg'], radius_bg = dp['radius_bg'],
                       ref = ref)
    cell_df_list = []
    for i in range(len(contour_list)):
        cell_obj = Cell(i+1, contour_list[i], mag, ps, img_to_measure, name, 
                        channel_name, dp['wants_ktr'], dp['ring_size'], 
                        dp['wants_foci'], dp['foci_min_size'], 
                        dp['foci_max_size'], dp['foci_min_int'], 
                        dp['foci_max_int'], dp['foci_proeminence'], 
                        dp['use_ellipse'])
        cell_df_list.append(cell_obj.df)
       
    return cell_df_list, img_to_measure, name
    


def drop_cols(
        complete_df: pd.DataFrame,
        ch_dict: dict
)-> pd.DataFrame:
    """ Drops columns tht store values not required by user."""
    
    for key, value in ch_dict.items():
        if value[1]['wants_foci'] == False:
            drop_foci = ["Total_foci_" + key,"Total_foci_area_" + key,
                         "Total_foci_mean_" + key, "Foci_area_fraction_" + key,
                         "Foci_cnt_" + key]
            complete_df.drop(columns = (drop_foci), inplace=True)
       
        if value[1]['wants_ktr'] == False:
             drop_ktr = [ "Mean_ring_" + key,"Median_ring_" + key, "Mean_ellipse_" + key,
                     "Median_ellipse_" + key,"Mean_Ring/Nucleus_" + key, "Median_Ring/Nucleus_" + key,
                     "Mean_Nucleus/Ring_" + key, "Median_Nucleus/Ring_" + key,
                     "Mean_Ellipse/Nucleus_" + key,"Median_Ellipse/Nucleus_" + key,
                     "Mean_Nucleus/Ellipse_" + key,  "Median_Nucleus/Ellipse_" + key,
                     "Cyto_ring_cnt_" + key]
                    
             complete_df.drop(columns = (drop_ktr), inplace=True)

    return complete_df

def perform_measure(contours: np.ndarray,
                    img_n: int,
                    ch_dict: dict,
                    ref_dict: dict,
                    seg_param: dict
                    ):
    """ 
        Applies functions needed for cell morphometry and intesity measures
    Returns a dataframe with all image information.
    """
    df_morpho_list  = []
    for n in range(len(contours)):
        #checar len(n) tem que ter ao menos 5 ptos no contorno para fitar uma elipse
        if len(contours[n]>5):
            morpho = Morphology(n+1, contours[n], seg_param['use_cellpose'])
            df_morpho_list.append(morpho.df)
    image_df = pd.concat(df_morpho_list)
      
    
    for key, value in ch_dict.items():
        df_ch_list, im, im_name= measure_image(value[0][img_n], value[1], 
                        ref_dict[key], contours, seg_param['magnification'], 
                        seg_param['pixel_size'], key)
        
        df_ch = pd.concat(df_ch_list)
        image_df = pd.merge(image_df, df_ch, on = 'Cell')
        image_df["Frame"] = img_n
    
    return image_df



#ELE nÂo salva imagens que estão sem contornos, tenho que corrigir isso 

def analyze_dict(
        ch_dict: dict,      # dic of every channel 
        seg_param: dict,     # dic of global parameters
        is_overtime: bool,
        condition: Optional[str]
        
)-> pd.DataFrame:
    
    """
    Given a dictionary containing information about each image channel analysis
    and the parameters used to perform cell segmentation, returns a dataframe
    containing the measurements and contours of each cell in every channel.
    """
    
    ref_dict = {}
    
    for key, value in ch_dict.items():
        if value[2] == True:
            ch_segment = key
        ref_dict[key] = load_image(value[0][0]) if value[1]['match_hist'] else None

    all_df_list =  []    
    for img_n in range(len((list(ch_dict.values())[0][0]))):      
        img_to_segment = ch_dict[ch_segment][0][img_n]
        
        cellpose =  seg_param['use_cellpose']
        
        if cellpose == True:
            #aqui chamo a função que vai pegar essa img já aberta e rodar... 
            #não sei se fazer ssim não deixa mais lento
            image_cp =load_image(img_to_segment)
            contours = run_cellpose(image_cp, seg_param['use_gpu'], 
                            seg_param['diameter'], seg_param['magnification'],
                            seg_param['pixel_size'], seg_param['shape'], 
                            seg_param['eccentricity'],seg_param['min_size'], 
                            seg_param['max_size'],seg_param['min_radius'], 
                            seg_param['max_radius'], seg_param['invert'], 
                            seg_param['normalize'], seg_param['net_avg'],
                            seg_param['resample'], seg_param['flow_threshold'],
                            seg_param['mask_threshold'])
           
            print(len(contours))
        else: 
            contours = find_contours(img_to_segment, 
               magnification = seg_param['magnification'],
               pixel_size = seg_param['pixel_size'], rescale_intensity = seg_param['rescale_intensity'],
               remove_bg = seg_param['remove_bg'],radius_bg = seg_param['radius_bg'],
               threshold = seg_param['threshold'], offset = seg_param['offset'], 
               blur= seg_param['blur'], adjust_size= seg_param['adjust_size'], 
               cut_edges = seg_param['cut_edges'], shape= seg_param['shape'], 
               eccentricity = seg_param['eccentricity'],min_size= seg_param['min_size'], 
               max_size= seg_param['max_size'],min_radius= seg_param['min_radius'], 
               max_radius= seg_param['max_radius'],fast_detection = seg_param['fast_detection'],
               weakly_labeled = seg_param['weakly_labeled']
               )
        
        #aqui vem o morphology e gero um df e todos os proximos vem ao lado 
        if len(contours) == 0:
            #ele ta dando continue, nem todas imagens vão estar no final pra serem salvas
            continue
        image_df = perform_measure(contours, img_n, ch_dict, ref_dict, seg_param)
           
            
        all_df_list.append(image_df)
    
    all_df = pd.concat(all_df_list)
    all_df["Condition"] = condition
    all_df["Overtime"] =  is_overtime
    all_df = all_df.reset_index(drop= True)
    
    #drop columns here 
    all_df = drop_cols(all_df, ch_dict)
    
    return all_df   # esse df vai pra parte de remover outliers 
          
   
def split_dfs(
        complete_df: pd.DataFrame,
        ch_name_list: List[str]
)-> Tuple[pd.DataFrame, pd.DataFrame]:
    """ 
    Gets a complete DataFrame and separates it in the user output and the 
    dataframe with information to draw images.
    """
    col_list_cnt =['Frame', 'Cell', 'X', 'origin_folder']
    col_to_remove = []
    for key in ch_name_list:
        cols = ['Image_'+ key,'Image_name_'+ key, "Nuc_cnt_" + key, "Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key]
        col_list_cnt.extend(cols)
        cols_remove = ["Nuc_cnt_" + key,"Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key, "Unnamed: 0", "Image_" + key ]
        col_to_remove.extend(cols_remove)
    
    all_col = list(complete_df)
    col_results = [i for i in all_col if i not in col_to_remove]
    df_results = complete_df[col_results]
    col_draw = [i for i in col_list_cnt if i in all_col]
    df_draw = complete_df[col_draw]
    
    return df_results, df_draw


def organize_df_foci(frames: List[int],
                      overtime: List[bool],
                      condition: List[str],
                      image_names: List[str],
                      foci_dfs: List[Optional[pd.DataFrame]]
)-> List[pd.DataFrame]:
    
    """ 
    Gets a dataframe list and other information lists and create new 
    dataframe columns. Stores all dataframes in a list trat is returned.
    """
    
    assert len(frames) == len(overtime) == len(condition) == len(image_names) == len(foci_dfs)
    foci_df_list = []
    for i in range(len(foci_dfs)):
        if isinstance(foci_dfs[i], pd.DataFrame): 
            foci_dfs[i]['Frame'] = frames[i]
            foci_dfs[i]['Is_overtime'] = overtime[i]
            foci_dfs[i]['Condition'] = condition[i]
            foci_dfs[i]['Image_name'] = image_names[i]
            foci_df_list.append(foci_dfs[i])
    
    return foci_df_list



def get_foci_df(df_results: pd.DataFrame): 
     """ Generates foci df from dataframes stored inside df_results. """
   
     df_results_cols = list(df_results.columns)
     cols_channel = [f for f in df_results_cols if "Total_foci" in f]
     print(cols_channel)
     channels_with_foci = [f.replace('Total_foci_', '') for f in cols_channel]
     channels_with_foci = [f for f in channels_with_foci if "area" not in f]
     channels_with_foci = [f for f in channels_with_foci if "mean" not in f]
     print(channels_with_foci)
     
    
     frames = list(df_results['Frame'])
     overtime = list(df_results['Overtime'])
     condition = list(df_results['Condition'])
     
     dfs_foci_to_append = []
     for ch in channels_with_foci:
         image_names = list(df_results['Image_name_' + ch])
         foci_dfs = list(df_results['foci_df_' + ch])
         df_foci_list = organize_df_foci(frames, overtime, condition,
                                         image_names, foci_dfs)
         dfs_foci_to_append.extend(df_foci_list)
         #df_results.drop(columns= (["foci_df_"+ ch]), inplace=True)
    
     df_foci = pd.concat(dfs_foci_to_append)
     df_foci = df_foci[['Channel', 'Image_name', 'Frame', "Origin_nucleus", 
                        'Focus_number', 'Focus_mean_intensity',	'Focus_Area', 
                        'Focus_perimeter', 'Focus_centroid_x', 'Focus_centroid_y', 
                        'Condition', 'Is_overtime']] 
     
     return df_foci, df_results
    
   
def save_dfs(df_results: pd.DataFrame,
             path_save: str):
    
    """ Saves dataframes"""
    tables = list(set(df_results['origin_folder']))
    for t in tables:
        df_foci, df_results = get_foci_df(df_results)
        df_save =  df_results[df_results["origin_folder"]== t]
        df_save = df_save.reindex(columns=(['Frame'] + list([a for a in df_save.columns if a != 'Frame']) ))
        df_save.drop(columns= (["origin_folder"]), inplace=True)
        cols = [f for f in df_save.columns if 'foci_df' not in f]
        df_save = df_save[cols]        
        df_save.to_csv(os.path.join(path_save, t[:-4]) + ' Results.csv')
        df_foci.to_csv(os.path.join(path_save, t[:-4]) + ' Foci Results.csv')
        print (os.path.join(path_save, t[:-4]))
    return print("files saved")
 


def draw_and_save(df: pd.DataFrame,
                 ch: str,
                 saving_dir: str,
                 use_cellpose: bool
):
    """ 
    Loop though a dataframe based on its channels and draws contours at the
    specified images and then saves them.
    """
     
    cols_to_draw = [ f for f in list(df.columns) if ch in f 
                    and 'Y_draw' not in f and 'Image_' not in f]
    
    df = df.filter(regex = ch+"|Cell|X")
    cnt_groupped = df.groupby(['Image_name_' + ch])
    fs = cv.getFontScaleFromHeight(2,15,2)   
    for name, group in  cnt_groupped:
        img = group['Image_'+ ch].iloc[0]
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
        cnt_nuc = list(group['Nuc_cnt_' + ch])
        print(name)
        img = cv.drawContours(img, cnt_nuc, -1, (98,59,132), 1)
        for i in range(len(group['Cell'])):
            img = cv.putText(img, str(int(group['Cell'].iloc[i])), 
                            ((group['X']+5).iloc[i], group['Y_draw_' + ch].iloc[i]), 
                            2, fs, (122, 144,248), 1)
         
        for col in cols_to_draw:
            if 'Foci' in col:
                 foci_cnt = list(group['Foci_cnt_' + ch])
                 foci_cnt = [i for f in foci_cnt for i in f if len(f)> 0]
                 img = cv.drawContours(img, foci_cnt, -1, (122, 144,248), 1)
                 
            else:                           
                 cnt = list(group[col])
                 cnt = [f[0] for f in cnt if len(f)> 0] if use_cellpose == False else cnt
                 img = cv.drawContours(img, cnt, -1, (122, 144,248), 1)
                                    
    
        cv.imwrite(os.path.join(saving_dir, name), img)
    
    

def saving_images(df_draw: pd.DataFrame,
                path_to_save: str,
                ch_name_list: List[str],
                use_cellpose: bool
):  
   """ 
   Splits dataframaccording to their folders, creates directories
   for saving and pass values to draw_and_save, that draws contours and saves
   images.
   """
   dirs = list(set(df_draw.origin_folder.values))
   df_draw.to_pickle(os.path.join(path_to_save, 'Results.pkl'))
   
   #    itera por cada pasta nesse df
   for d in dirs:
       df_dir = df_draw[df_draw["origin_folder"]==d]
       saving_dir = os.path.join(path_to_save, d[:-4] + '-') if os.path.isdir(os.path.join(path_to_save, d[:-4])) else os.path.join(path_to_save, d[:-4])
       os.mkdir(saving_dir) 
       #    vai iterar sobre cada canal dessa pasta
       for ch in ch_name_list:
           saving_dir_ch = os.path.join(saving_dir, ch)
           os.mkdir(saving_dir_ch)           
           draw_and_save(df_dir, ch, saving_dir_ch, use_cellpose)
         
    
           
   

    

# o foldername deve ser o nome da pasta mãe dessa análise (função draw_and_save)
# depois que eu selecionar o que faz sentido pra mim, rodar uma pasta separando 
# campos e poços e ploto so dotplots das médias de areqa e ativação de erk   

#abaixo exemplo de como chamar para eventuais testes (sem ter que roar tudo a partir do run)   
'''    
       
p1 = '/media/luiza/DATA/àrea de trabalho/video kaka/registradas/r/red'
p2 = '/media/luiza/DATA/àrea de trabalho/video kaka/registradas/g/green'
r = os.listdir (p1) 
r = [os.path.join(p1, i) for i in r]
g = os.listdir (p2 ) 
g = [os.path.join(p2, i) for i in g]

param_r = {'rescale_intensity' : True,
           'remove_bg' : False,
           'radius_bg': 50,
           'match_hist' : False,
           'wants_ktr' : False,
           'ring_size': 3,
           'use_ellipse': False,
           'wants_foci': True,
           'foci_min_size' : None,
           'foci_max_size': None,
           'foci_min_int' : None,
           'foci_max_int' : None,
           'foci_proeminence' : None
           }

param_g = {'rescale_intensity' : True,
           'remove_bg' : False,
           'radius_bg': 50,
           'match_hist' : False,
           'wants_ktr' : True,
           'ring_size': 3,
           'use_ellipse': True,
           'wants_foci': False,
           'foci_min_size' : None,
           'foci_max_size': None,
           'foci_min_int' : None,
           'foci_max_int' : None,
           'foci_proeminence' : None
           }


teste_dict = {'red': [r, param_r, True],
              'green' : [g, param_g, False]}

segment_dict = {'magnification': 20,
                'pixel_size':  0.6,
                'rescale_intensity':  True,
                'remove_bg': False,
                'radius_bg': 0,
                'threshold': 'triangle',
                'offset': 0,
                'blur' : 12, 
                'adjust_size': 0, 
                'cut_edges':  0.7, 
                'shape':  0.88, 
                'eccentricity': None, 
                'min_size': None, 
                'max_size': None, 
                'min_radius': None, 
                'max_radius': None, 
                'fast_detection': False,
                'error': None 
  }

     
check_size(teste_dict)
c = analyze_dict(teste_dict, segment_dict, True, 'c')
d = split_dfs(c, teste_dict)

e = split_dfs(c, teste_dict)
#h =draw_and_save( e[1], e[0], 'C:\\Users\\Luiza Cherobini\\Desktop\\', 'a',
#              teste_dict, True)       

'''               
