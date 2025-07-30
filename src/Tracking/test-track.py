import math
import os
import pandas as pd

pd.options.mode.chained_assignment = None
from typing import List
from src.Tracking.LapTracker.LapTracker import LapTracker


def set_initial_family(df):
    df_initial = df[df['Frame'] == 0]
    initial_track_ids = list(set(df_initial['track_id']))
    df['family'] = None
    for track_id, cells in df.groupby('track_id'):
        if track_id in initial_track_ids:
            df.loc[df['track_id'] == track_id, 'family'] = track_id

    return df


def calc_smaller_distance(df, cell):
    previous_frame = cell['Frame'] - 1
    df_previous_frame = df[df['Frame'] == previous_frame]
    x = cell['X']
    y = cell['Y']
    df_previous_frame['distance'] = np.sqrt(
        df_previous_frame['X'].apply(lambda n: (n-x)**2) + df_previous_frame['Y'].apply(lambda n: (n-y)**2)
    )
    closer = df_previous_frame.sort_values(by=['distance']).iloc[0]

    return closer


def set_families(df):
    missing_family = df[df['family'].isna()]
    while not missing_family.empty:
        track_family_dict = {}
        for track, cells in missing_family.groupby('track_id'):
            cell = cells[cells['is_start'] == 1].sort_values(by=['Frame']).iloc[0]
            family = calc_smaller_distance(df, cell)['family']
            track_family_dict[track] = family
        for track, family in track_family_dict.items():
            df.loc[df['track_id'] == track, 'family'] = family
            missing_family = df[df['family'].isna()]

    return df


def get_previous_position(df, mg, tw):
    df['previous_x'] = None
    df['previous_y'] = None
    df.loc[df['Frame'] == 0, 'previous_x'] = df['X']
    df.loc[df['Frame'] == 0, 'previous_y'] = df['Y']
    df.loc[df['is_start'] == 0, 'previous_x'] = df.groupby('track_id')['X'].shift(1)
    df.loc[df['is_start'] == 0, 'previous_y'] = df.groupby('track_id')['Y'].shift(1)
    missing_previous = df.loc[(df['is_start'] == 1) & (df['Frame'] != 0)]
    for index, row in missing_previous.iterrows():
        original_frame = row['Frame']
        df_tw = df.loc[(df['Frame'] < original_frame) & (df['Frame'] > original_frame - tw)]
        if row['track_id'] in list(df_tw['track_id']):  # checa se o track id existe no time window
            df_tw = df_tw.loc[df_tw['track_id'] == row['track_id']]
            df_tw = df_tw.sort_values(by="Frame", ascending=False)
            cell = df_tw.iloc[0]

        else:
            cell = calc_smaller_distance(df, row)  # se não calcula a menor distancia
            while cell['distance'] > 4 * mg:
                if (row['Frame'] == original_frame - tw) or (row['Frame'] == 1):
                    break
                row['Frame'] = row['Frame'] - 1
                cell = calc_smaller_distance(df, row)

        df.at[index, 'previous_x'] = cell['X']
        df.at[index, 'previous_y'] = cell['Y']

    return df


def track_family_names(df):
    df['cell_track'] = None
    df.loc[df['Frame'] == 0, 'cell_track'] = df['family'].apply(lambda x: f'{str(x)}.')
    df = df.sort_values(['X', 'Y'])

    for frame, df_frame in df.groupby('Frame'):
 #       if frame == 3:
 #           break

        if frame == 0:
            continue

        # primeiro puxo o track_id do frame anterior e coloco no df
        df_previous_frame = df.loc[df['Frame'] == frame - 1][['X', 'Y', 'cell_track', ]]
        df_previous_frame = df_previous_frame.rename(columns={'X': 'previous_x', 'Y': 'previous_y'})
        merged_df = df_frame.merge(df_previous_frame, on=['previous_x', 'previous_y'], how='left')
        merged_df['cell_track'] = merged_df['cell_track_y']
        merged_df.drop(columns=['cell_track_x', 'cell_track_y'], inplace=True)
        merged_df = merged_df.sort_values(['X', 'Y'])
        merged_df.drop_duplicates(subset=['unique_id'], inplace=True)
###
        nan_df = merged_df[merged_df['cell_track'].isna()]
        missing_tracks_at_merged_df = [f for f in df_previous_frame['cell_track'] if f not in list(merged_df['cell_track'])]
        u_id_track = {}
        if len(missing_tracks_at_merged_df) == 0:
            for i, r, in nan_df.iterrows():
                same_track_id_cells = merged_df[merged_df['track_id'] == r['track_id']]
                if len(list(same_track_id_cells['cell_track'].dropna())) > 0:
                    u_id_track[r['unique_id']] = list(same_track_id_cells['cell_track'].dropna())[0]

        else:
            df_missing_tracks = df_previous_frame[df_previous_frame['cell_track'].isin(missing_tracks_at_merged_df)]
            for i, r in df_missing_tracks.iterrows():
                x = r['previous_x']
                y = r['previous_y']
                nan_df['distance'] = np.sqrt(
                    nan_df['previous_x'].apply(lambda n: (n - x) ** 2) + nan_df['previous_y'].apply(lambda n: (n - y) ** 2)
                )
                closer = nan_df.sort_values(by=['distance']).iloc[0]
                u_id_track[closer['unique_id']] = r['cell_track']


        for u_id, ct in u_id_track.items():
                merged_df.loc[merged_df['unique_id'] == u_id, 'cell_track'] = ct
###
        # talvez de pra pegar o track id anterior
        df.loc[df['Frame'] == frame, 'cell_track'] = list(merged_df['cell_track'])

        df_frame = df.loc[df["Frame"] == frame]
        duplicates = df_frame[df_frame.duplicated(subset=['previous_x', 'previous_y'], keep=False)]

        if not duplicates.empty:  # significa que tem células que vieram da mesma posição
            for new_cells, new_cells_df in duplicates.groupby(['previous_x', 'previous_y']):
                print(new_cells)
                sister_number = 1
                for index, row in new_cells_df.iterrows():
                    # add .1 e .2  nas céluals desse grupo
                    df.at[index, 'cell_track'] = str(row['cell_track']) + f'{sister_number}.'
                    sister_number += 1
    return df


def tracking(path_to_table: str,
             path_to_save: str,
             max_distance: int = 30,
             time_window: int = 5,
             max_split_distance: int = 30,
             max_gap_closing_distance: int = 30, # esse valor e muio chave. Se ele for baixo vai gerar segmentos ligados de lugares nada a ver nas arvores
             allow_merging=True
             ) -> None:
    """ Gets a dataframe and user parameters and applies LapTracker for cell tracking."""

    table = pd.read_csv(path_to_table)
    for i in table.columns:
        if 'Image_name' in i:
            img_name = i
            break

    cols = ['X', "Y", 'Frame', img_name]
    df2 = table[cols]
    df2['X'] = pd.to_numeric(df2['X'], downcast='integer')
    df2['Y'] = pd.to_numeric(df2['Y'], downcast='integer')
    df2['Frame'] = pd.to_numeric(df2['Frame'], downcast='integer')
    tracker = LapTracker(max_distance=max_distance, time_window=time_window,
                         max_split_distance=max_split_distance,
                         max_gap_closing_distance=max_gap_closing_distance)
    tracker.track_df(df2, identifiers=cols)
    tracked_df = tracker.df
    tracked_df = set_initial_family(tracked_df)
    tracked_df = set_families(tracked_df)
    tracked_df = get_previous_position(tracked_df, max_gap_closing_distance, time_window)
    tracked_df = track_family_names(tracked_df)

    return tracked_df


# separar por familia para dar a cor
# iterar pelos frames
# pra cada frame desenhar os segmentos e todos anteriorea
import cv2 as cv
import os
import numpy as np


def draw(df, folder, save):
    img_col = [f for f in df.columns if 'Image_name' in f ][0]
    for frame, df_frame in df.groupby("Frame"):
        df = df.sort_values(by='Frame')
        image_to_open = df_frame[img_col].iloc[0]
        img = cv.imread(os.path.join(folder, image_to_open))
        df_0 = df.loc[df['Frame'] == frame]
        coordinates = list(zip(df_0['X'].astype(int), df_0['Y'].astype(int)))
        family = list(df_0['cell_track'].astype(str))
        [cv.circle(img, f, 2, (171, 235, 85), 2) for f in coordinates]
        [cv.putText(img, f, g, cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2) for f, g in zip(family, coordinates)]

        tracks_df = df.loc[df["Frame"] <= frame].sort_values('Frame')
        line = list(zip(tracks_df['X'].astype(int), tracks_df['Y'].astype(int)))
        line_previous = list(zip(tracks_df['previous_x'].astype(int), tracks_df['previous_y'].astype(int)))
        [cv.line(img, f, g, (0, 0, 255), thickness=2) for f, g in zip(line, line_previous)]
        track = list(df['cell_track'].astype(str))
        #[A for f, g in zip(track, line)]
        cv.imwrite(save + str(frame) + '.jpeg', img)

    return



path_to_table = '/media/luiza/DATA/Doutorado/forNMA/experimentos/exp kaka/Experimento_ Karine-Julia_STV+TMZ 100 uM/results/results geral/A1_2 primeiro tempo-teste.csv'
saving_path = 'aaa'

result=tracking(path_to_table, 'aa')
folder = '/media/luiza/DATA/Doutorado/forNMA/experimentos/exp kaka/Experimento_ Karine-Julia_STV+TMZ 100 uM/results/results geral/A1_2/frames 0-20'
save = '/media/luiza/DATA/Doutorado/forNMA/experimentos/exp kaka/Experimento_ Karine-Julia_STV+TMZ 100 uM/results/results geral/A1_2/teste tracking/6/'

draw(result, folder, save)


# Agora surgiu um problema pior
#cuidar a célula 35. ERla perde o track e retorna cmo 2.1
# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
