#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 15:43:42 2021

@author: luiza
"""

from LapTracker.LapTracker import *
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
    
    return track
    

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
md = 50
t = 10 
ms = 5
mg = 5
bb = tracking ('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Aplicação poster/ptx 1/d5_2_gResults.csv',
              max_distance = md,
               time_window= t,
               max_split_distance = ms,
               max_gap_closing_distance = mg)

ims, im_names = generate_tracked_images('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Aplicação poster/ptx 1/d5_2_g/53bp1', bb)

import random, string


letters = string.ascii_lowercase
name = ('md_' + str(md) + ' t_' + str(t)+ ' ms_' + str(ms) + ' mg_'+ str(mg) +  ' linking=true')
path = os.path.join('/media/luiza/DATA/Doutorado/53bp1 py some info/forNMA recente/Aplicação poster/ptx 1/teste tracking ptx', name)
os.makedirs(path)
save_images(ims, im_names,path )
bb.to_csv(os.path.join (path, 'table'))
