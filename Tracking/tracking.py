#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 15:43:42 2021

@author: luiza
"""
import math
import os
import pandas as pd
from typing import List
from LapTracker.LapTracker import LapTracker


def calc_distance(x: float, 
                  y: float, 
                  x_list: List[float], 
                  y_list: List[float], 
                  unique_ids: List[int]
)-> int:
    """Measures the distance betwen a point (given by x y) to a series of 
    points (in x_lis, y_list) and returns the unique_id of the closest 
    point (from unique_id list)
    """
    dist_dict = {}
    for i in range(len(x_list)):
        dist = math.dist((x,y), (x_list[i], y_list[i]))
        dist_dict[unique_ids[i]]= dist 
    
    u_id =  min(dist_dict, key=dist_dict.get)
    
    return u_id


def find_parent_track(df: pd.DataFrame)-> pd.DataFrame:
    """
    Searches the parent track of a track (given by track_id) in a dataframe
    with tracking information
    """
    tracks = set(list(df['track_id']))
    df2 = df.copy()
    df2['parent_track'] = None
    for track in tracks:
        sub_df = df.loc[df['track_id']== track]
        first_frame = sub_df['Frame'].min()
        x = sub_df.loc[sub_df['Frame'] == first_frame, 'X'].iloc[0]
        y = sub_df.loc[sub_df['Frame'] == first_frame, 'Y'].iloc[0]
        if first_frame == 0:
            continue
        cells = df.loc[df['Frame'] == first_frame-1]
        x_list = list(cells['X'])
        y_list = list(cells['Y'])
        unique_ids = list(cells.unique_id)
        unique = calc_distance(x, y, x_list, y_list, unique_ids)        
        track_id_parent = df.loc[df['unique_id'] == unique, 'track_id'].iloc[0]
        df.drop(df[df['unique_id'] == unique].index, inplace = True)
        df2["parent_track"].mask( df2["track_id"] == track,track_id_parent, inplace=True )

    return df2


def find_family_track(df: pd.DataFrame)-> pd.DataFrame:
    """ From a tracked dataframe, uses parent track information to find family tracks """
    parents = [f for f in list(set(df['parent_track'])) if f is not None]
    parent_dict = {} # parents are keys, its daughters are values
    for p in parents:
        sub_df = df.loc[df['parent_track'] ==  p]
        parent_dict[p] = list(set(sub_df['track_id']))

    for p in parents: # unites all daughters in the dict value where parent is
        for key, track_list in parent_dict.items():
            if p in track_list:
                t = track_list
                t.extend(parent_dict[p])
                parent_dict[key] = t
                parent_dict[p] = []
                
    tree_dict = {} # key is tree name and values are all track_ids within it
    n = 1
    for key, value in parent_dict.items():
        if len(value)>0:
            value.append(key)
            tree_dict[n] = value
            n=n+1
        
    df['family_id'] = None
    for key, value in tree_dict.items():
        df["family_id"].mask( df["track_id"].isin(value), key, inplace=True )
        
    return df
        

def get_df_first_frames(df: pd.DataFrame)-> pd.DataFrame: 
    """ 
    Finds a dataframe with only rows where each track starts (smaller frame
    associated with each track_id)
    """
    grouped =df.groupby('track_id')
    rows=[]
    for name, group in grouped:
        first_frame = group['Frame'].min() 
        first_frame_row = group.loc[group['Frame'] == first_frame]
        rows.append(first_frame_row)
    first_frame_df = pd.concat(rows)
    
    return first_frame_df


def naming_cell_trees(track_id: int,
                      df_first_frames: pd.DataFrame, 
                      df_final: pd.DataFrame, 
                      main:bool
)-> pd.DataFrame:
    """ 
    Adds tree nomenclature to tracks.
    It uses daughter cells to identify  where the cell divisions occur to 
    add the generation nomenclatue (ie. .1.2.2.1) """
    
    if main == True:
        n = str(df_first_frames['family_id'].iloc[0]) + '.' # first tree number (n.1.1.1...)
    else: 
        parent_frame =  df_final.loc[df_final['track_id']==track_id, 'Frame'].min() -1  # first frame of current track -1
        parant_track_id = df_final.loc[df_final['track_id']==track_id, 'parent_track'].iloc[0] 
        df_previous_frame = df_final.loc[df_final['Frame'] == parent_frame]
        n =  str(df_previous_frame.loc[ df_previous_frame['track_id']== parant_track_id, 'Cell_id'].iloc[0]) 
        
    # find daughters of current track
    daughters = list(df_first_frames.loc[df_first_frames['parent_track'] == track_id, 'Frame'])

    df_track = df_final.loc[df_final['track_id']==track_id] # selects only current track from eh complete dataframe
    df_track['Cell_id'] = str(n)  # adds the n.
          
    # this if/else statement adds .1 or .2 to tracks (.2 in daughters)
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
        n = str(n) + '2.'
        if len(daughters)== 0:
            df_final.update(df_track)
            return df_final 
        else: 
            for i in daughters:
                df_track["Cell_id"].mask(df_track["Frame"] >= i, str(n)+ '1.', inplace=True )
                n = str(n) + '1.'
                 
    df_final.update(df_track)        
    return df_final


def create_tree_nomenclature(df: pd.DataFrame)-> pd.DataFrame:
    """
    From family and parent information in a tracked dataframe, finds the 
    family numeration and thus cell division frames    
    """   
    
    df['Cell_id'] = None
    total_df =df
    families = list(set(df['family_id']))
    for family in families: # iteratesone family at time
        df_family = df.loc[df['family_id']== family]
        df_first_frames = get_df_first_frames(df_family) # df with fist frame where each track apears 
        first_frame = df_first_frames['Frame'].min() 
        main_branch = df_first_frames.loc[df_first_frames['Frame'] == first_frame, 'track_id'].iloc[0]
        total_df = naming_cell_trees(main_branch, df_first_frames, total_df, True) 
        df_first_frames.sort_values(by=['Frame'], inplace=True)
        for track_id in df_first_frames['track_id'][1:]: # skips frame form main cell (1st frame)
            total_df = naming_cell_trees( track_id, df_first_frames, total_df, False)
    
    return df



def tracking(path_to_table: str,
             path_to_save: str,
             max_distance: int = 30,
             time_window: int = 5,
             max_split_distance: int = 30,
             max_gap_closing_distance: int = 30,
             allow_merging = True
)-> None :
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
    tracked_df = find_parent_track(tracked_df)
    tracked_df =find_family_track(tracked_df)
    tracked_df = create_tree_nomenclature(tracked_df)
    
    cols_to_use = tracked_df.columns.difference(table.columns)
    final_df = table.merge(tracked_df[cols_to_use], how='outer', left_index=True, right_index=True) # merge dataframes
    
    final_df.to_csv(os.path.join(path_to_save, 'Tracked - ' + os.path.basename(path_to_table)))
    final_df.drop(columns = ['filer'])
    
    return None
 




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


