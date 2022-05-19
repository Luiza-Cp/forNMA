#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 15:43:42 2021

@author: luiza
"""

from LapTracker.LapTracker import LapTracker
import numpy as np
import pandas as pd
import os
import math
import random
from typing import List, Dict
import seaborn as sns
import cv2 as cv
import os


def find_parent(tracking_df: pd.DataFrame,
                segment_ids: List[int],
                df_frame_before: pd.DataFrame,
                frame: int)-> Dict:
    """ 
        Pairs in a dictionary a segment with a previous segment based on  the 
    distance to the cellsin the previous frame. 
    """
    
    segment_parent_dict = {}
    
    for segment in segment_ids:
        segment_x = tracking_df[(tracking_df['Frame'] == frame) & (tracking_df['Lineage_track'] == segment)]['X'].values[0]
        segment_y = tracking_df[(tracking_df['Frame'] == frame) & (tracking_df['Lineage_track'] == segment)]['Y'].values[0]
       
        df_frame_before['distance'] = np.nan
                               
        for index, row in df_frame_before.iterrows():
           df_frame_before['distance'].loc[index] = math.sqrt((row['X'] - segment_x)**2 
                                                         + (row['Y'] - segment_y)**2)
        
        min_dist = df_frame_before['distance'].idxmin()     
        parent_cell_number = df_frame_before.loc[min_dist]['Lineage_track']
        segment_parent_dict[segment] = parent_cell_number
       
       
    
    return segment_parent_dict


# ISSO TA TUDO ERRADO TIPO 100%
def adjust_tracking(single_track: pd.DataFrame) -> pd.DataFrame:
    """ Finds mother-daugther relationships from single trcaking branches. """
     
    track = single_track.sort_values(by=['Frame'])
    track['Lineage_track']= track['segment_id']
    is_start_true = sorted(list(set( track.loc[track['is_start'] == 1]['Frame'])))     # represents cell division
    frame_set = sorted(list(set(track['Frame'])))   # lists all frames 

    cell0 = track.loc[track['Frame'] == is_start_true[0], 'segment_id'].values[0]   # segment_id of initial cell
    
    # The first cell keeps the segment_id as lineage_track 
    if len(is_start_true) == 1:
        track['Lineage_track'] = str(cell0)
    else:
        track.loc[track.Frame < is_start_true[1], 'Lineage_track'] = str(cell0)
   
    # The next cell will recieve parent information
    if len(is_start_true)>1:
        track['Lineage_track'] = np.where((track['Frame']>= is_start_true[1]) &
                                     (track['Lineage_track'] == cell0), 
                                     str(cell0) + '.1', track['Lineage_track'])
        nn = list( track.loc[track['Frame'] == is_start_true[1], 'Lineage_track'].values) 
        if str(cell0) +'.1' in  nn:
            nn.remove(str(cell0) +'.1')
        
            track['Lineage_track'] = np.where((track['Frame']>= is_start_true[1]) &
                                     (track['Lineage_track'] == nn[0]), 
                                     str(cell0) + '.2', track['Lineage_track'])
        elif str(cell0) +'.0' in nn:
            nn.remove(str(cell0)+'.0')
        # This is used for non connected segments inside a track_id. Puts a 0
        # bfore the number to indicate. 
        else:
           print( 'esse track_id teve coisas novas surgindo')
           track['Lineage_track'] = np.where((track['Frame']>= is_start_true[1]) &
                                    (track['Lineage_track'] == nn[0]), 
                                    str(cell0) +'.0' , track['Lineage_track'])
            
    # All following cells have to find their mother, acording to distance to 
    # cells in previous frames 
    if len(is_start_true)>2:
        for i in is_start_true[2:]:
           
            segment_ids = list(track.loc[track['Frame'] == i, 'Lineage_track'].values)
            segment_ids = [ f for f in segment_ids if type(f) != str]
            frame_before = frame_set[frame_set.index(i)-1]
            df_frame_before = track.loc[track["Frame"] == frame_before]
            segment_parent_dict = find_parent(track, segment_ids, df_frame_before, i)
            print (segment_ids, segment_parent_dict)
    
            for key, value in segment_parent_dict.items():
                track['Lineage_track'] = np.where((track['Frame']>= i) &
                                             (track['Lineage_track'] == value), 
                                             str(value) + '.1', track['Lineage_track'])
                track['Lineage_track'] = np.where((track['Frame']>= i) &
                                             (track['Lineage_track'] == key), 
                                             str(value) + '.2', track['Lineage_track'])

    return track



def tracking(path_to_table: str,
             max_distance: int = 30,
             time_window: int = 5,
             max_split_distance: int = 30,
             max_gap_closing_distance: int = 30,
             allow_merging = True
)-> pd.DataFrame :
    """ Gets a dataframe and user parameters and applies LapTracker for cell tracking."""
    
    table = pd.read_csv(path_to_table)
    table.columns
    for i in table.columns:
        if 'Image_name' in i:
            name = i 
            break
             
    cols = ['X', "Y", 'Frame', name]
    df2 = table[cols]
    df2['X'] = pd.to_numeric(df2['X'], downcast='integer')
    df2['Y']  =pd.to_numeric(df2['Y'], downcast='integer')
    df2['Frame']  =pd.to_numeric(df2['Frame'], downcast='integer')
    tracker = LapTracker(max_distance=max_distance, time_window=time_window,
                         max_split_distance=max_split_distance,
                         max_gap_closing_distance=max_gap_closing_distance)
    tracker.track_df(df2, identifiers=cols)
    tracked_df = tracker.df
    
    identified_tracks =[]
    for i in range(len(list(set(tracked_df['track_id'])))):
        track = tracked_df.loc[tracked_df['track_id'] == i]
        track = adjust_tracking(track)
        identified_tracks.append(track)
    
    track  = pd.concat(identified_tracks)
    track['Lineage_track'] = track['Lineage_track'].astype(str) + '.'
    
    return track # tracked_df
    

def draw_tracking_at_iamges(img: np.ndarray,
                            frame: int,
                            df_track: pd.DataFrame,
                            track_color_dict: dict,
                            circle_radius: int,
                            linewidth: int
)-> List[np.ndarray]:
    """ Draws tracking elements in one image, given by its frame. """
    
    df_draw_image = df_track.loc[df_track["Frame"]<= frame]
    for key, value in track_color_dict.items():
        value = (value[2]*255, value[1]*255, value[0]*255)
        tree = df_draw_image[df_draw_image['Lineage_track'].str.startswith(key +'.')]
        if tree.shape[0] == 0:
            continue
        else:
            x = tree['X'].values[0]
            y = tree['Y'].values[0]
            img = cv.circle(img, (int(x), int(y)), circle_radius, value, cv.FILLED)
            
            if tree.shape[0] == 1:
                img =img
            else:
                x_list = tree['X'].values
                y_list = tree['Y'].values
                for i in range(len(x_list)-1):
                   cv.line(img, (int(x_list[i]), int(y_list[i])),
                                 (int(x_list[i+1]), int(y_list[i+1])), 
                            value, linewidth)
                #cv.putText(img, key, (int(x_list[i]+ 10), int(y_list[i])+ 5),
                #              cv.FONT_HERSHEY_SIMPLEX, 1, value)
                   
               
    return img 

    
def save_images(image_list: List[np.ndarray],
                image_names: List[str],
                path: str
)-> bool:
        """ Saves images at the given path"""
        for i in range(len(image_list)):
           cv.imwrite(os.path.join(path, image_names[i]), image_list[i])
    
        return True

#from skimage import img_as_ubyte, exposure
def generate_tracked_images(path: str,
                            df_track: pd.DataFrame,                   
) -> np.ndarray:
    """ 
        Draws cell trajectory at imagens within a path based on information
    stored at df_track.
    """
    image_names = sorted(os.listdir(path))
    frames = sorted(list(set(df_track['Frame'].values)))
    
    print (len(frames), len(image_names))
    track_color_dict = {}
    tracks = sorted(list(set(df_track['track_id'])))
    for t in tracks:
        track_color_dict[str(t)] =  sns.color_palette('deep', len(tracks))[t]
    
    images = []
    print(frames)
    for frame in frames:
         img = cv.imread(os.path.join(path,image_names[frame]), cv.IMREAD_COLOR)
         #img = exposure.rescale_intensity(img, in_range='image', out_range='dtype')
         circle_radius = 5 if img.shape[0]*img.shape[1] < 4000000 else 10
         linewidth = 2 if img.shape[0]*img.shape[1] < 4000000 else 5
         img = draw_tracking_at_iamges(img, frame, df_track,track_color_dict,
                                       circle_radius, linewidth)
        
         images.append(img)
     
    return images, image_names

    
#exemplo de como chamar 
# fazer testes com imagens da kaka
#md = 50
#t = 10 
#ms = 5
#mg = 5
md = 250
t = 7
ms = 25
mg = 10

bb = tracking ('/media/luiza/DATA/Doutorado/Teste tracking/2  arvores/teste arvore mentira 2 arvores.csv',
              max_distance = md,
               time_window= t,
               max_split_distance = ms,
               max_gap_closing_distance = mg)

ims, im_names = generate_tracked_images('/media/luiza/DATA/Doutorado/Teste tracking/2  arvores/imagens', bb)

import random, string


letters = string.ascii_lowercase
name = ('md_' + str(md) + ' t_' + str(t)+ ' ms_' + str(ms) + ' mg_'+ str(mg) +  ' linking=true')
path = os.path.join('/media/luiza/DATA/Doutorado/Teste tracking/2  arvores', name)
os.makedirs(path)
save_images(ims, im_names,path )
bb['X'] = pd.to_numeric(bb['X'])
bb['Y'] = pd.to_numeric(bb['Y'])
bb['uniquer_id'] = pd.to_numeric(bb['unique_id'])
bb.to_csv(os.path.join (path, 'table'))



bb_fram = bb.loc[bb['is_start'] == 1]

bb_fram = bb_fram.sort_values(by = 'Frame')

## AQUI DESENHA O UNIQUE id

folder = '/media/luiza/DATA/Doutorado/Teste tracking/2  arvores/md_250 t_7 ms_25 mg_10 linking=true (outra cópia)'
files= [os.path.join(folder, f) for f in os.listdir(folder)]
frames = sorted(list(set(bb['Frame'].values)))
for i in range(len(files)):
   img = cv.imread(files[i], cv.IMREAD_COLOR)
   frame_df = bb.loc[bb['Frame'] == i]
   x =list(frame_df['X'])
   y =list(frame_df['Y'])
   val =list(frame_df['unique_id'])
   for j in range(len(x)):
       cv.putText(img, str(val[j]),(int(x[j]), int(y[j])), cv.FONT_HERSHEY_DUPLEX, 2.0, (125, 246, 55), 1)
   cv.imwrite(files[i], img)
##

### achar parent_track

def calc_distance(x, y, x_list, y_list, unique_ids):
    dist_dict = {}
    for i in range(len(x_list)):
        dist = math.dist((x,y), (x_list[i], y_list[i]))
        dist_dict[unique_ids[i]]= dist 
    
    u_id =  min(dist_dict, key=dist_dict.get)
    return u_id


tracks = set(list(bb['track_id']))
bb2 = bb.copy()
bb2['parent_track'] = None
for track in tracks:
    sub_df = bb.loc[bb['track_id']== track]
    first_frame = sub_df['Frame'].min()
    x = sub_df.loc[sub_df['Frame'] == first_frame, 'X'].iloc[0]
    y = sub_df.loc[sub_df['Frame'] == first_frame, 'Y'].iloc[0]
    if first_frame == 0:
        continue
    cells = bb.loc[bb['Frame'] == first_frame-1]
    x_list = list(cells['X'])
    y_list = list(cells['Y'])
    unique_ids = list(cells.unique_id)
    unique = calc_distance(x, y, x_list, y_list, unique_ids)        
    track_id_parent = bb.loc[bb['unique_id'] == unique, 'track_id'].iloc[0]
    bb.drop(bb[bb['unique_id'] == unique].index, inplace = True)
    bb2["parent_track"].mask( bb2["track_id"] == track,track_id_parent, inplace=True )

###

#### Achar family track

# cria dicionário de todos pais com seus filhos
parents = [f for f in list(set(bb2['parent_track'])) if f is not None]
parent_dict = {}
for p in parents:
    sub_df = bb2.loc[bb2['parent_track'] ==  p]
    parent_dict[p] = list(set(sub_df['track_id']))
    
# une todos os pais nas suas famílias,
# as keys com value são as que iniciam árvores
for p in parents:
    for key, track_list in parent_dict.items():
        if p in track_list:
            print(p, track_list, parent_dict[p])
            t = track_list
            t.extend(parent_dict[p])
            parent_dict[key] = t
            parent_dict[p] = []

# key é o número da arvore, valor são os track_ids nessa arvore            
tree_dict = {}
n = 1
for key, value in parent_dict.items():
    if len(value)>0:
        value.append(key)
        tree_dict[n] = value
        n=n+1
        
bb2['family_id'] = None
for key, value in tree_dict.items():
    bb2["family_id"].mask( bb2["track_id"].isin(value), key, inplace=True )
    
    
####


##### fazer família numerada


def get_df_first_frames(df): # nãop ta retornando o first frame
    grouped =df.groupby('track_id')
    rows=[]
    for name, group in grouped:
        first_frame = group['Frame'].min() 
        first_frame_row = group.loc[group['Frame'] == first_frame]
        rows.append(first_frame_row)
    first_frame_df = pd.concat(rows)
    return first_frame_df

def naming_cell_trees(track_id, df_first_frames, df_final, main = False):
    #track_id = 9
    #df_final = bb2
    #main = True
   # DF FIRST FRAMES SÓ TEM OS FRAMES DOS FILHOS DESSE TRACK_ID
    if main == True:
        n = str(df_first_frames['family_id'].iloc[0]) + '.' # primeiro número da arvore n.1.1.1
    else: 
        # o first frame desse -1 -> pega valor do cell_id do parent
        parent_frame =  df_final.loc[df_final['track_id']==track_id, 'Frame'].min() -1  # primeiro frame do track que to -1
        parant_track_id = df_final.loc[df_final['track_id']==track_id, 'parent_track'].iloc[0] #track_id do pai
        df_previous_frame = df_final.loc[df_final['Frame'] == parent_frame]
        n =  str(df_previous_frame.loc[ df_previous_frame['track_id']== parant_track_id, 'Cell_id'].iloc[0]) 
        

    #DESCOBRIR COMO ACHAR ESSE FODIDO DO N
        #n =  df_final[(['Frame']== parent_frame) & (df_final['parent_track'] == parent_id)]['family_id']  
                      # ao family_id do parent no frame anterior
        
    #selecionar filhos do track_id selecionado
    daughters = list(df_first_frames.loc[df_first_frames['parent_track'] == track_id, 'Frame'])

    #seleciona só o dito track_id
    df_track = df_final.loc[df_final['track_id']==track_id]
    df_track['Cell_id'] = str(n)  # add o n.
   
       
    # esse if else é pra add o .2 ou .1 de acorod com a ocasião -> sempre q for ramo daughter de um ramo
    if main == True:
        if len(daughters)== 0:
            df_track['Cell_id'] = str(n) + '1.'
            return df_final 
        df_track["Cell_id"].mask(df_track["Frame"] >= daughters[0], str(n)+ '1.', inplace=True ) # aqui seria else
        n = str(n) + '1.'
        if len(daughters)>1:
            for i in daughters[1:]:
                df_track["Cell_id"].mask(df_track["Frame"] >= i, str(n)+ '1.', inplace=True )
                n = str(n) + '1.'
        
    else:
        
        df_track['Cell_id'] = str(n) + '2.'
        #df_track["Cell_id"].mask(df_track["Frame"] >= daughters[0], str(n)+ '2.', inplace=True )
        n = str(n) + '2.'
        if len(daughters)== 0:
            df_final.update(df_track)
            return df_final 
        
        if len(daughters)>=1: ## TROCAR PRA ELSE
            for i in daughters:
                df_track["Cell_id"].mask(df_track["Frame"] >= i, str(n)+ '1.', inplace=True )
                n = str(n) + '1.'
            
            
    df_final.update(df_track)        
    return df_final



bb2['Cell_id'] = None
total_df = bb2
families = list(set(bb2['family_id']))
for family in families:
    df_family = bb2.loc[bb2['family_id']== family]
    df_first_frames = get_df_first_frames(df_family) ######
    main_branch = df_first_frames['Frame'].min() 
    main_branch = df_first_frames.loc[df_first_frames['Frame'] == first_frame, 'track_id'].iloc[0]
    total_df = naming_cell_trees(main_branch, df_first_frames, total_df, True)
    df_first_frames.sort_values(by=['Frame'], inplace=True)
    for track_id in df_first_frames['track_id'][1:]: # pula o frame do main (1º frame)
        print(track_id)
        total_df = naming_cell_trees( track_id, df_first_frames, total_df, False)

   


folder = '/media/luiza/DATA/Doutorado/Teste tracking/2  arvores/md_250 t_7 ms_25 mg_10 linking=true (outra cópia)'
files= [os.path.join(folder, f) for f in os.listdir(folder)]
frames = sorted(list(set(total_df['Frame'].values)))
for i in range(len(files)):
   img = cv.imread(files[i], cv.IMREAD_COLOR)
   frame_df = total_df.loc[total_df['Frame'] == i]
   x =list(frame_df['X'])
   y =list(frame_df['Y'])
   val =list(frame_df['Cell_id'])
   for j in range(len(x)):
       cv.putText(img, str(val[j]),(int(x[j]), int(y[j])), cv.FONT_HERSHEY_DUPLEX, 1.0, (125, 246, 55), 1)
   cv.imwrite(files[i], img)