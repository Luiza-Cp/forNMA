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
from Foci_class import foci
import numpy as np
from typing import List, Optional, Tuple
import os
import cv2 as cv



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
        if value[1]['match_hist'] == True:
            ref_dict[key] = load_image(value[0][0])
        else:
            ref_dict[key] = None

    all_df_list =  []    
    for img_n in range(len((list(ch_dict.values())[0][0]))):      
        img_to_segment = ch_dict[ch_segment][0][img_n]
      #retornar nessa função o int_in, int_out, detection_round
        contours, int_in, int_out, detection_round = find_contours(img_to_segment, 
               magnification = seg_param['magnification'],
               pixel_size = seg_param['pixel_size'], rescale_intensity = seg_param['rescale_intensity'],
               remove_bg = seg_param['remove_bg'],radius_bg = seg_param['radius_bg'],
               threshold = seg_param['threshold'], offset = seg_param['offset'], 
               blur= seg_param['blur'], adjust_size= seg_param['adjust_size'], 
               cut_edges = seg_param['cut_edges'], shape= seg_param['shape'], 
               eccentricity = seg_param['eccentricity'],min_size= seg_param['min_size'], 
               max_size= seg_param['max_size'],min_radius= seg_param['min_radius'], 
               max_radius= seg_param['max_radius'],fast_detection = seg_param['fast_detection'],
               error = seg_param['error'])
        
        #aqui vem o morphology e gero um df e todos os proximos vem ao lado 
        if len(contours) == 0:
            #ele ta dando continue, nem todas imagens vão estar no final pra serem salvas
            continue
        df_morpho_list  = []
        for n in range(len(contours)):
            morpho = Morphology(n+1, contours[n], int_in[n], int_out[n])
            df_morpho_list.append(morpho.df)
        image_df = pd.concat(df_morpho_list)
          
        
        for key, value in ch_dict.items():
            df_ch_list, im, im_name= measure_image(value[0][img_n], value[1], 
                            ref_dict[key], contours, seg_param['magnification'], 
                            seg_param['pixel_size'], key)
            
            df_ch = pd.concat(df_ch_list)
            image_df = pd.merge(image_df, df_ch, on = 'Cell')
            image_df["Frame"] = img_n
            image_df["Error_detection_round"] = detection_round
            
        all_df_list.append(image_df)
    
    all_df = pd.concat(all_df_list)
    all_df["Condition"] = condition
    all_df["Overtime"] =  is_overtime
    #add error here
    all_df["Error"] = (-0.93 * all_df.Roundness - 0.8 * all_df.Error_convex_area ) *-1
    all_df.drop(columns = (["Error_convex_area"]), inplace=True)
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
    col_list_cnt =['Cell', 'X', 'origin_folder']
    col_to_remove = []
    for key in ch_name_list:
        cols = ['Image_'+ key,'Image_name_'+ key, "Nuc_cnt_" + key, "Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key]
        col_list_cnt.extend(cols)
        cols_remove = ["Nuc_cnt_" + key,"Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key, "Unnamed: 0", "Error", "Image_" + key ]
        col_to_remove.extend(cols_remove)
    
    all_col = list(complete_df)
    col_results = [i for i in all_col if i not in col_to_remove]
    df_results = complete_df[col_results]
    col_draw = [i for i in col_list_cnt if i in all_col]
    df_draw = complete_df[col_draw]
    
    return df_results, df_draw
    
   
def save_dfs(df_results: pd.DataFrame,
             path_save: str):
    tables = list(set(df_results['origin_folder']))
    for t in tables:
        df_save =  df_results[df_results["origin_folder"]== t]
        df_save = df_save.reindex(columns=(['Frame'] + list([a for a in df_save.columns if a != 'Frame']) ))
        df_save.drop(columns= (["origin_folder"]), inplace=True)
        df_save.to_csv(os.path.join(path_save, t[:-4]) + 'Results .csv')
        print (os.path.join(path_save, t[:-4]))
    return print("files saved")
 


def draw_and_save(df: pd.DataFrame,
                ch: str,
                saving_dir: str
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
                 cnt = [f[0] for f in cnt if len(f)> 0]
                 img = cv.drawContours(img, cnt, -1, (122, 144,248), 1)
                                    
    
        cv.imwrite(os.path.join(saving_dir, name), img)
    
    

def saving_images(df_draw: pd.DataFrame,
                path_to_save: str,
                ch_name_list: List[str]
):  
   """ 
   Splits dataframaccording to their folders, creates directories
   for saving and pass values to draw_and_save, that draws contours and saves
   images.
   """
   dirs = list(set(df_draw.origin_folder.values))
   #    itera por cada pasta nesse df
   for d in dirs:
       df_dir = df_draw[df_draw["origin_folder"]==d]
       saving_dir = os.path.join(path_to_save, d[:-4])
       os.mkdir(saving_dir)
       #    vai iterar sobre cada canal dessa pasta
       for ch in ch_name_list:
           saving_dir_ch = os.path.join(saving_dir, ch)
           os.mkdir(saving_dir_ch)           
           draw_and_save(df_dir, ch, saving_dir_ch)
         
    
           
   

        
    
   
####funções abaixo não são masi utilizadas mas eu não quis apagar ainda 
## pra caso eu precise editar as de cima heahha
    
   
    
   
def split_dfs_old(
        complete_df: pd.DataFrame,
        ch_dict: dict
)-> pd.DataFrame:
    """ 
    Gets a complete DataFrame and separates it in the user output and the 
    dataframe with information to draw images.
    """
    
    keys = ch_dict.keys()
    col_list_cnt =['Cell', 'X']
    col_to_remove = []
    for key in keys:
        cols = ['Image_'+ key,'Image_name_'+ key, "Nuc_cnt_" + key,"Ring_cnt_" + key, 
                "Ellipse_cnt_" + key, "Foci_cnt_" + key, "Y_draw_" + key]
        col_list_cnt.extend(cols)
        cols_remove = ["Nuc_cnt_" + key,"Ring_cnt_" + key, "Ellipse_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key,]
        col_to_remove.extend(cols_remove)
    df_cnt = complete_df[col_list_cnt]
    
    all_col = list(complete_df)
    col_results = [i for i in all_col if i not in col_to_remove]
    df_results = complete_df[col_results]
    
    for key, value in ch_dict.items():
        if value[1]['wants_foci'] == False:
            drop_foci = ["Total_foci_" + key,"Total_foci_area_" + key,
                         "Total_foci_mean_" + key, "Foci_area_fraction_" + key,]
            df_cnt = df_cnt.drop (columns=(["Foci_cnt_" + key]))
            df_results = df_results.drop(columns = (drop_foci))
        if value[1]['wants_ktr'] == False:
             drop_ktr = [ "Mean_ring_" + key,"Median_ring_" + key, "Mean_ellipse_" + key,
                     "Median_ellipse_" + key,"Mean_Ring/Nucleus_" + key, "Median_Ring/Nucleus_" + key,
                     "Mean_Nucleus/Ring_" + key, "Median_Nucleus/Ring_" + key,
                     "Mean_Ellipse/Nucleus_" + key,"Median_Ellipse/Nucleus_" + key,
                     "Mean_Nucleus/Ellipse_" + key,  "Median_Nucleus/Ellipse_" + key]
                    
             df_cnt = df_cnt.drop (columns=(["Ring_cnt_" + key, 'Ellipse_cnt_' + key]))
             df_results = df_results.drop(columns = (drop_ktr))
        df_results =  df_results.drop(columns = ('Image_' + key))
    
    return df_results, df_cnt
        
     
#se ficar mto pesado eu exlcuo aquele loaded dict e recarrego todas as fotos aqui 
def draw_and_save_old(
        df_cnt: pd.DataFrame,
        df_results: pd.DataFrame, 
        path_to_save: str,
        foldername,         #name of folder containing images
        ch_dict: dict,
        save_img: bool = True
)-> True:
  """ 
   INCOMPLETE FUNCTION
   According to user input, draws images stored in the df_cnt with contours also 
   belongin to it and saves the images and a csv with complete results at 
   path_to_save.
  """
    
  if save_img == True:
     df_results.to_csv(os.path.join(path_to_save, foldername + " Results.csv"))
     fs = cv.getFontScaleFromHeight(2,15,2)
     
     for key, value in ch_dict.items():
         save_ch = os.path.join(path_to_save, foldername, key + " Contours")
         os.makedirs(save_ch)    
        
         df = df_cnt.filter(regex = key+"|Cell|X")
         cnt_groupped = df.groupby(['Image_name_' + key])
         

         for name, group in  cnt_groupped:
             img = group['Image_'+ key].iloc[0]
             img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
             cnt_nuc = list(group['Nuc_cnt_' + key])
             print(name)
             img = cv.drawContours(img, cnt_nuc, -1, (98,59,132), 1)
             for i in range(len(group['Cell'])):
                 img = cv.putText(img, str(group['Cell'].iloc[i]), 
                                  ((group['X']+5).iloc[i], group['Y_draw_' + key].iloc[i]), 
                                  2, fs, (122, 144,248), 1)
         
             if  value[1]['wants_foci'] == True:
                 foci_cnt = list(group['Foci_cnt_' + key])
                 foci_cnt = [i for f in foci_cnt for i in f if len(f)> 0]
                 img = cv.drawContours(img, foci_cnt, -1, (122, 144,248), 1)
                 
             elif value[1]['wants_ktr'] and value[1]['use_ellipse']  == True:
                 el_cnt = list(group['Ellipse_cnt_' + key])
                 el_cnt = [f[0] for f in el_cnt if len(f)> 0]
                 img = cv.drawContours(img, el_cnt, -1, (122, 144,248), 1)
           
             elif value[1]['wants_ktr'] == True:
                 ring_cnt = list(group['Ring_cnt_' + key])
                 ring_cnt = [f[0] for f in ring_cnt if len(f)> 0]
                 img = cv.drawContours(img, ring_cnt, -1, (122, 144,248), 1)
                
         
    
             cv.imwrite(os.path.join(save_ch, name), img)
         
  return True
             
             
             

        
     
        
     
        


# o foldername deve ser o nome da pasta mãe dessa análise (função draw_and_save)
# depois que eu selecionar o que faz sentido pra mim, rodar uma pasta separando 
# campos e poços e ploto so dotplots das médias de areqa e ativação de erk      
     
'''    

p1 = 'C:\\Users\\Luiza Cherobini\\Desktop\\teste r\\r - reg'
p2 = 'C:\\Users\\Luiza Cherobini\\Desktop\\teste g\\g - reg'
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
c = analyze_dict(teste_dict, segment_dict)
d = split_dfs(c, teste_dict)

e = split_dfs(c, teste_dict)
h =draw_and_save( e[1], e[0], 'C:\\Users\\Luiza Cherobini\\Desktop\\', 'a',
              teste_dict, True)       

'''                
