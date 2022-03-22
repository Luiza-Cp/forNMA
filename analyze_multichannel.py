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
from cellpose_integration import run_cellpose_nuc, run_cellpose_cyto


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
        df_nuc: pd.DataFrame,
        df_cyto: pd.DataFrame,
        ch_dict: dict
)-> pd.DataFrame:
    """ Drops columns tht store values not required by user."""
    
    
    for key, value in ch_dict.items():
        if value[1]['cytoplasm'] == True :
            df_cyto.drop(columns = ('Cyto_NII'), inplace=True)
        if value[1]['wants_foci'] == False:
            drop_foci = ["Total_foci_" + key,"Total_foci_area_" + key,
                         "Total_foci_mean_" + key, "Foci_area_fraction_" + key,
                         "Foci_cnt_" + key]
            df_cyto.drop(columns = (drop_foci), inplace=True) if value[1]['cytoplasm'] == True else df_nuc.drop(columns = (drop_foci), inplace=True)
            
       
        if value[1]['wants_ktr'] == False:
             drop_ktr = [ "Mean_ring_" + key,"Median_ring_" + key, "Mean_ellipse_" + key,
                     "Median_ellipse_" + key,"Mean_Ring/Nucleus_" + key, "Median_Ring/Nucleus_" + key,
                     "Mean_Nucleus/Ring_" + key, "Median_Nucleus/Ring_" + key,
                     "Mean_Ellipse/Nucleus_" + key,"Median_Ellipse/Nucleus_" + key,
                     "Mean_Nucleus/Ellipse_" + key,  "Median_Nucleus/Ellipse_" + key,
                     "Cyto_ring_cnt_" + key]
                    
             df_cyto.drop(columns = (drop_ktr), inplace=True) if value[1]['cytoplasm'] == True else df_nuc.drop(columns = (drop_ktr), inplace=True)

    return df_nuc, df_cyto



def get_image_morphology_dataframe(nuc_contours: List[np.ndarray],
                                   cyto_contours: List[np.ndarray],
                                   seg_param: dict
)-> Tuple[pd.DataFrame]:
    """
    Applies contours to morphology class to generate information about cell
    and nuclear shape. Retrurns a nuclear and a cytoplasmatic dataframe with
    the measured caracteristics and contours.
    """
    if len(nuc_contours) > 0:       # if there are nuclear contours
        df_morpho_nuc_list  = []
        for n in range(len(nuc_contours)):      # iterate over contours
            if len(nuc_contours[n]>5):          # if contour is not a square (has more than 4 points)
                morpho = Morphology(n+1, nuc_contours[n], seg_param['use_cellpose']) 
                df_morpho_nuc_list.append(morpho.df)
        image_nuc_df = pd.concat(df_morpho_nuc_list)
        image_nuc_df = rename_columns(image_nuc_df, True)  
    else:
        image_nuc_df = None
        
    if len(cyto_contours) > 0:      # if there are cytoplasmatic contours
        df_morpho_cyto_list  = []
        for n in range(len(cyto_contours)):
            if len(cyto_contours[n]>5):
                morpho = Morphology(n+1, cyto_contours[n], True)   
                # Last arg is true because it allways uses cellpose for cytoplasm
                df_morpho_cyto_list.append(morpho.df)
        image_cyto_df = pd.concat(df_morpho_cyto_list)
        image_cyto_df = rename_columns(image_cyto_df, False)  
    else:
         image_cyto_df = None
               
    return image_nuc_df, image_cyto_df
     

def rename_columns(df: pd.DataFrame,
                   is_nuc: bool
)-> Tuple[pd.DataFrame]:
    """ Renames dataframe columns accordimg to nuclear or cytoplasmatic option"""
    
    cn = 'Nuc_'if is_nuc == True else 'Cyto_'        
        
    cols = [cn + f for f in df.columns[1:]]
    cols.insert(0, "Cell")
    df.columns = cols
    
    return df 
        
    

def perform_measure(nuc_contours: List[np.ndarray],
                    cyto_contours: List[np.ndarray],
                    img_n: int,
                    ch_dict: dict,
                    ref_dict: dict,
                    seg_param: dict
)-> Tuple[pd.DataFrame]:
    """ 
        Applies functions needed for cell morphometry and intesity measures
    Returns a dataframe with all image information.
    """
    
    # generates a DatFrame with cell and nuclear morphology 
    image_nuc_df, image_cyto_df = get_image_morphology_dataframe(nuc_contours,
                                       cyto_contours, seg_param)

    
    # iterate over image ch_dict 
    for key, value in ch_dict.items():
        # checks if for that specific channel it wants to measure cytoplasm
        # utilising the segment_parameters (value[1])
        if value[1]['cytoplasm'] == True:
            print(key, 'cytoooooo')
            contours = cyto_contours        # pass the cytoplasm contours
            df_ch_list, im, im_name= measure_image(value[0][img_n], value[1], 
                        ref_dict[key], contours, seg_param['magnification'], 
                        seg_param['pixel_size'], key)
            df_ch = pd.concat(df_ch_list)
            image_cyto_df = pd.merge(image_cyto_df, df_ch, on = 'Cell')
            image_cyto_df["Frame"] = img_n
        
        # else is considered it wants to measure nuclei
        else:
            print(key, 'nuc')
            contours = nuc_contours         # pass the nuclei contours
            df_ch_list, im, im_name= measure_image(value[0][img_n], value[1], 
                        ref_dict[key], contours, seg_param['magnification'], 
                        seg_param['pixel_size'], key)
        
            df_ch = pd.concat(df_ch_list)
            image_nuc_df = pd.merge(image_nuc_df, df_ch, on = 'Cell')
            image_nuc_df["Frame"] = img_n
   
    return image_nuc_df, image_cyto_df


def segment_nuc_and_cyto(img_n: int,
                         ch_dict: dict,
                         seg_param: dict
)-> Tuple[List[np.ndarray]]:
    
    
    
    # encontra canal onde devem ser encontrados os cnt de núcleos e canal com cnt de cytop.
    ch_nuc_list = []
    ch_cyto_list = [] 
    for key, value in ch_dict.items():
        ch_nuc = key if value[2] == True else None
        ch_nuc_list.append(ch_nuc)
        ch_cyto = key if value[3] == True else None
        ch_cyto_list.append(ch_cyto)
    
    ch_nuc = [f for f in ch_nuc_list if f != None]
    ch_cyto = [f for f in ch_cyto_list if f != None]
    
    ch_nuc = ch_nuc[0] if len(ch_nuc)> 0 else None
    ch_cyto = ch_cyto[0] if len(ch_cyto)> 0 else None
    
    print (ch_nuc, ch_cyto) # printa aqui
    
    #se algum canal tem núcleo:
    if ch_nuc != None:  
        img_to_segment =  ch_dict[ch_nuc][0][img_n] # pega a imagem do canal do nucleo
        if seg_param['use_cellpose'] == True:  #usa os parametros do seg_param pra medir nucleos com ou sem cellpose
            image_cp = load_image(img_to_segment) 
            nuc_contours = run_cellpose_nuc(image_cp, seg_param['use_gpu'], 
                            seg_param['diameter'], seg_param['magnification'],
                            seg_param['pixel_size'], seg_param['shape'], 
                            seg_param['eccentricity'],seg_param['min_size'], 
                            seg_param['max_size'],seg_param['min_radius'], 
                            seg_param['max_radius'], seg_param['invert'], 
                            seg_param['normalize'], seg_param['net_avg'],
                            seg_param['resample'], seg_param['flow_threshold'],
                            seg_param['mask_threshold'])
        else:
            nuc_contours = find_contours(img_to_segment, 
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
    else: # se não tem detecção de nucleo devlve a lista vazia
         nuc_contours = []
        
    
    
    if ch_cyto != None: #se quer medida de citoplasma
        '''# aqui pode ter uma opção de ter ou não cellpose_CYTO 
        # se opção for não, usar voronoi com centroide do contorno anterior.
        #Beautiful
        '''
        img_to_segment =  ch_dict[ch_cyto][0][img_n] #abre a imagem do canal do citoplasma
        image_cp = load_image(img_to_segment)
        cyto_contours = run_cellpose_cyto(image_cp, seg_param['use_gpu'], #usa os parametros do seg_param pra medir 
                        seg_param['cyto_diameter'], seg_param['cyto_flow_threshold'],
                        seg_param['cyto_mask_threshold'],  seg_param['model_for_cyto'])
       
    else:
        cyto_contours = [] # se não tem detecção de  citoplasma devolve a lista vazia
    
    print('nuc_cnt:', len(nuc_contours),'cyto_cnt', len(cyto_contours))
         
    return nuc_contours, cyto_contours
    


def match_nuc_cyto(image_nuc_df: pd.DataFrame,
                   image_cyto_df: pd.DataFrame
) -> pd.DataFrame:
    
    """ 
    Matches cells to nuclei inside them. Returns dataframe with columns 
    indicating it.
    """
    cd = image_cyto_df.copy()
    nd = image_nuc_df.copy()
    
    df_cell_nuc_info = [] # stores number of nuclei in each cell 
    
    image_nuc_df['Origin_cell'] = np.nan
    
    col = [f for f in image_cyto_df.columns if 'Image_name' in f][0]
    image_nuc_df['Origin_cell_image'] = image_cyto_df[col].iloc[0]
    
    cnt_col = [f for f in image_cyto_df.columns if 'Nuc_cnt_' in f][0]
    print(cnt_col)
    for cell in zip(cd['Cell'], cd[cnt_col]):
        nuc_idx = [f[0] for f in zip(nd['Cell'], nd['Nuc_X'], nd['Nuc_Y']) if cv.pointPolygonTest(cell[1], [f[1], f[2]], False) == True]
        # returns list with nucleus index inside this cell
        # each cell can have more than one nuclei and none nuclei too 
        df_cell_nuc_info. append(len(nuc_idx)) 
        for idx in nuc_idx:
            # adds the cytoplasm cell number to its nuclei
            image_nuc_df.loc[image_nuc_df['Cell'] == idx, 'Origin_cell'] = cell[0]
    
    image_cyto_df['Nuclei_detected'] = df_cell_nuc_info
             
    return image_nuc_df, image_cyto_df
    
    

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
    
    ch_dict structure:
    str: List[List[str], Dict, bool bool]
    image_channel: [[list of image paths], segmentation parameters, detect nuclei?, detect cytoplasm?]
    both boolean can be false (in that case, forNMA will not segment the specified
    image and will use it just in measurements)
    """
    
    ref_dict = {}
    
    for key, value in ch_dict.items():
        if value[2] == True:
            ch_segment = key
        ref_dict[key] = load_image(value[0][0]) if value[1]['match_hist'] else None

    all_df_nuc_list = []
    all_df_cyto_list = []

    # iterate trough image list, ie. value[0] of ch_dict
    for img_n in range(len((list(ch_dict.values())[0][0]))): 
        # find nuclear and cytoplasmatic contours 
        nuc_contours, cyto_contours = segment_nuc_and_cyto(img_n, ch_dict, seg_param)
        # If there aro no contours, the image is skipped
        if len(nuc_contours) == 0 and len(cyto_contours)== 0: 
            continue
        
        # Utilising nuc and cyto contours, iterate over all channels to perform measurments
        image_nuc_df, image_cyto_df = perform_measure(nuc_contours,cyto_contours,
                                            img_n, ch_dict, ref_dict, seg_param)
        
    
        # then both dataframes pass trough a function to acess each nuclei to 
        # its cytoplasm
        if image_nuc_df is not None and image_cyto_df is not None:
            image_nuc_df, image_cyto_df = match_nuc_cyto(image_nuc_df, image_cyto_df)
            all_df_nuc_list.append(image_nuc_df)
            all_df_cyto_list.append(image_cyto_df)
        elif image_nuc_df is not None :
            all_df_nuc_list.append(image_nuc_df)
        else:
            all_df_cyto_list.append(image_cyto_df)
         

    if len(all_df_nuc_list) > 0:
        all_nuc_df = pd.concat(all_df_nuc_list)
        all_nuc_df["Condition"] = condition
        all_nuc_df["Overtime"] =  is_overtime
        all_nuc_df = all_nuc_df.reset_index(drop= True)
    else:
        all_nuc_df = None
   
    if len(all_df_cyto_list) > 0:
        all_cyto_df = pd.concat(all_df_cyto_list)
        all_cyto_df["Condition"] = condition
        all_cyto_df["Overtime"] =  is_overtime
        all_cyto_df = all_cyto_df.reset_index(drop= True)
    else:
        all_cyto_df = None
    
    #drop columns here 
    all_nuc_df, all_cyto_df = drop_cols(all_nuc_df, all_cyto_df, ch_dict)
    
    return all_nuc_df, all_cyto_df   # esses dfs vao pra parte de remover outliers 
         
   
def split_dfs(
        complete_df: pd.DataFrame,
        ch_name_list: List[str]
)-> Tuple[pd.DataFrame, pd.DataFrame]:
    """ 
    Gets a complete DataFrame and separates it in the user output and the 
    dataframe with information to draw images.
    """
    
    col_list_cnt =['Frame', 'Cell', 'origin_folder']
    col_to_remove = []
    for key, value in ch_name_list.items():
        nuc_or_cyto = 'Cyto_' if value[1]['cytoplasm'] == True else 'Nuc_'
        
        cols = [nuc_or_cyto+'X', 'Image_'+ key,'Image_name_'+ key, "Nuc_cnt_" + key, "Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key]
        col_list_cnt.extend(cols)
        cols_remove = ["Nuc_cnt_" + key,"Cyto_ring_cnt_" + key,
                "Foci_cnt_" + key, "Y_draw_" + key, "Unnamed: 0", "Image_" + key ]
        col_to_remove.extend(cols_remove)
    
    all_col = list(complete_df)
    print(all_col)
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
    
     channels_with_foci = [f.replace('Total_foci_', '') for f in cols_channel]
     channels_with_foci = [f for f in channels_with_foci if "area" not in f]
     channels_with_foci = [f for f in channels_with_foci if "mean" not in f]
     
     
    
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
     if len (dfs_foci_to_append) > 0:
         df_foci = pd.concat(dfs_foci_to_append)
         df_foci = df_foci[['Channel', 'Image_name', 'Frame', "Origin_nucleus", 
                            'Focus_number', 'Focus_mean_intensity',	'Focus_Area', 
                            'Focus_perimeter', 'Focus_centroid_x', 'Focus_centroid_y', 
                            'Condition', 'Is_overtime']] 
     else:
         df_foci= None
         
     return df_foci, df_results
    
   
def save_dfs(df_results: pd.DataFrame,
             path_save: str,
             is_cyto: bool):
    
    """ Saves dataframes"""
    c_or_n = ' Cytoplasm' if is_cyto == True else ' Nuclei'    
    tables = list(set(df_results['origin_folder']))
    for t in tables:
        df_foci, df_results = get_foci_df(df_results)
        df_save =  df_results[df_results["origin_folder"]== t]
        df_save = df_save.reindex(columns=(['Frame'] + list([a for a in df_save.columns if a != 'Frame']) ))
        df_save.drop(columns= (["origin_folder"]), inplace=True)
        cols = [f for f in df_save.columns if 'foci_df' not in f]
        df_save = df_save[cols]   
        df_save.to_csv(os.path.join(path_save, t[:-4]) + c_or_n  +' Results.csv')
        if df_foci is not None:
            df_foci.to_csv(os.path.join(path_save, t[:-4]) + c_or_n  + ' Foci Results.csv')
        print (os.path.join(path_save, t[:-4]))
    return print("files saved")
 


def draw_and_save(df: pd.DataFrame,
                 ch: str,
                 saving_dir: str,
                 use_cellpose: bool,
                 is_cyto: bool,
                 df2: Optional[pd.DataFrame] = None,
                 use_cp_nucs: bool = False
):
    """ 
    Loop though a dataframe based on its channels and draws contours at the
    specified images and then saves them.
    """
   
    c_or_n = 'Nuc_' if is_cyto ==False else "Cyto_" 
    cols_to_draw = [ f for f in list(df.columns) if ch in f 
                    and 'Y_draw' not in f and 'Image_' not in f]
    
    df = df.filter(regex = ch+"|Frame|Cell|X")
    cnt_groupped = df.groupby(['Image_name_' + ch])
    fs = cv.getFontScaleFromHeight(2,15,2)   
    for name, group in  cnt_groupped:
        img = group['Image_'+ ch].iloc[0]
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
        cnt_nuc = list(group['Nuc_cnt_' + ch])
        img = cv.drawContours(img, cnt_nuc, -1, (98,59,132), 1)
        for i in range(len(group['Cell'])):
            img = cv.putText(img, str(int(group['Cell'].iloc[i])), 
                            ((group[c_or_n + 'X']+5).iloc[i], group['Y_draw_' + ch].iloc[i]), 
                            2, fs, (122, 144,248), 1)
         
        for col in cols_to_draw:
            if 'Foci' in col:
                 foci_cnt = list(group['Foci_cnt_' + ch])
                 foci_cnt = [i for f in foci_cnt for i in f if len(f)> 0]
                 img = cv.drawContours(img, foci_cnt, -1, (122, 144,248), 1)
                 
            else:                           
                 cnt = list(group[col])
                 cnt = [f[0]for f in cnt if len(f)> 4] if use_cellpose == False else cnt
                 img = cv.drawContours(img, cnt, -1, (122, 144,248), 1)
                             
        if df2 is not None: 
            frame = group["Frame"].iloc[0]
            nuc_cnt_df = df2.loc[df2['Frame'] == frame]
            col2 = [f for f in df2.columns if "Nuc_cnt" in f][0]
            nuc_cnt2 = list(nuc_cnt_df[col2])
            #nuc_cnt2 = [f[0] for f in nuc_cnt2 if len(f)> 0] if use_cp_nucs == False else nuc_cnt2
            print(frame)
            img = cv.drawContours(img, nuc_cnt2, -1, (122, 144,248), 1)
            
    
        cv.imwrite(os.path.join(saving_dir, name), img)
   

def saving_images(df_draw: pd.DataFrame,
                path_to_save: str,
                ch_name_list: List[str],
                use_cellpose: bool,
                is_cyto = bool,
                df_draw2: Optional[pd.DataFrame] = None,
                use_cp_nucs: bool = False, # when it has cytoplasm, were nuc contours generated with cellpose?
                create_saving_dir: bool = True
):  
   """ 
   Splits dataframaccording to their folders, creates directories
   for saving and pass values to draw_and_save, that draws contours and saves
   images.
   """
   
   
   dirs = list(set(df_draw.origin_folder.values))
   
   c_or_n = 'Nucleus ' if is_cyto == False else "Cytoplasm "
   use_cellpose = True if is_cyto == True else False
   df_draw.to_pickle(os.path.join(path_to_save,c_or_n + 'Results.pkl'))
   
   #    itera por cada pasta nesse df
   for d in dirs:
       df_dir = df_draw[df_draw["origin_folder"]==d]
       d2 = d.replace("Cytoplasm", "Nucleus")
       df_dir2 = df_draw2[df_draw2["origin_folder"]==d2] if df_draw2 is not None else None
       saving_dir = os.path.join(path_to_save, d[:-4] )
       os.mkdir(saving_dir) if create_saving_dir == True else None
       #    vai iterar sobre cada canal dessa pasta
       for ch in ch_name_list:
           saving_dir_ch = os.path.join(saving_dir, ch)
           os.mkdir(saving_dir_ch)        
           draw_and_save(df_dir, ch, saving_dir_ch, use_cellpose, is_cyto, df_dir2, use_cp_nucs)
  
          
# =============================================================================
# 
#     
# 
# # o foldername deve ser o nome da pasta mãe dessa análise (função draw_and_save)
# # depois que eu selecionar o que faz sentido pra mim, rodar uma pasta separando 
# # campos e poços e ploto so dotplots das médias de areqa e ativação de erk   
# 
# #abaixo exemplo de como chamar para eventuais testes (sem ter que roar tudo a partir do run)   
#     
#         
# p1 = '/media/luiza/DATA/àrea de trabalho/teste (del)/r/red'
# p2 = '/media/luiza/DATA/àrea de trabalho/teste (del)/g/green'
# r = os.listdir (p1) 
# r = [os.path.join(p1, i) for i in r]
# g = os.listdir (p2 ) 
# g = [os.path.join(p2, i) for i in g]
# 
# param_r = {'rescale_intensity' : True,
#             'remove_bg' : False,
#             'radius_bg': 50,
#             'match_hist' : False,
#             'wants_ktr' : False,
#             'ring_size': 3,
#             'use_ellipse': False,
#             'wants_foci': True,
#             'foci_min_size' : None,
#             'foci_max_size': None,
#             'foci_min_int' : None,
#             'foci_max_int' : None,
#             'foci_proeminence' : None,
#             'cytoplasm' : False
#             }
# 
# param_g = {'rescale_intensity' : True,
#             'remove_bg' : False,
#             'radius_bg': 50,
#             'match_hist' : False,
#             'wants_ktr' : True,
#             'ring_size': 3,
#             'use_ellipse': True,
#             'wants_foci': False,
#             'foci_min_size' : None,
#             'foci_max_size': None,
#             'foci_min_int' : None,
#             'foci_max_int' : None,
#             'foci_proeminence' : None,
#             'cytoplasm' : True
#             }
# 
# 
# teste_dict = {'red': [r, param_r, True, False],
#               'green' : [g, param_g, False, True]}
# 
# segment_dict = {'magnification': 20,   
#                 'pixel_size': 0.6,      
#                 'rescale_intensity': True,      # seta o valor mínimo para 0 e máximo para 255
#                 'remove_bg': False,     
#                 'radius_bg': 40,                # raio da rolling-balll (igual ao imageJ)
#                 'threshold':'triangle',        # Descrição das opções vem abaixo 
#                 'offset': 5,                    # Deve ser usado para os thresholds locais 
#                 'blur': 13,                     # o quanto deve suavizar o contorno do núcleo
#                 'adjust_size': -1,               # Expandir ou diminuir o contorno (número negativo para diminuir)
#                 'cut_edges': 0.9,            # o quanto deve forçar o corte entre os núcleos, pode ser False 
#                 'shape':  0.88,                 # remove células com formatos muito loucos
#                 'eccentricity': None,           # Vai de 0 a 1. Valores mais próximos de 0 represenntam mais circular, mais perto de 1 é mais oval
#                 'min_size': None, 
#                 'max_size': None, 
#                 'min_radius': None, 
#                 'max_radius': None, 
#                 'fast_detection': False,
#                 'weakly_labeled': False ,        # setar como true se tiverem marcações fracas e baixa densidade de cell
#                 'use_cellpose': False,          # usar o cellpose pra detecção nuclear. Parametros do cellpose abaixo
#                 'invert': False,                # invert image pixel intensity before running network (if True, image is also normalized)
#                 'normalize': True,              # normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel
#                 'diameter': 5 ,                 # if set to None, then diameter is automatically estimated if size model is loaded
#                 'net_avg': True,                # runs the 4 built-in networks and averages them if True, runs one network if False
#                 'resample': True,               # run dynamics at original image size (will be slower but create more accurate boundaries)
#                 'flow_threshold': 0.4,          # flow error threshold (all cells with errors below threshold are kept)
#                 'mask_threshold': 0.0,         # all pixels with value above threshold kept for masks, decrease to find more and larger masks
#                 'use_gpu': True,
#                 'model_for_cyto': 'cyto2',     #cellpose model for cytoplasmatic measures
#                 'cyto_diameter': 60 ,               # if set to None, then diameter is automatically estimated if size model is loaded
#                 'cyto_flow_threshold': 0.6,          # flow error threshold (all cells with errors below threshold are kept)
#                 'cyto_mask_threshold': 0.0 ,   
#   }
# 
#       
# check_size(teste_dict)
# c = analyze_dict(teste_dict, segment_dict, True, 'c')
# 
# 
# red_r, red_d = split_dfs(c[0], teste_dict)
# phase_r, phase_d = split_dfs(c[1], teste_dict)
# 
# 
# #h =draw_and_save( e[1], e[0], 'C:\\Users\\Luiza Cherobini\\Desktop\\', 'a',
# #              teste_dict, True)       
#             
# 
# =============================================================================
