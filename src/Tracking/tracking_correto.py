import os
import pandas as pd
import numpy as np
from src.Tracking.LapTracker.LapTracker import LapTracker
import cv2 as cv
import random
import ast

pd.options.mode.chained_assignment = None


def find_previous_positions(df: pd.DataFrame) -> pd.DataFrame:
    """ Uses track_id information to find the previous x and y position of a cell """
    dfs = []
    for track, group in df.groupby('track_id'):
        group.sort_values(by=['Frame', 'X', 'Y'], inplace=True)
        #groupby frame
        # fazer o previous do group anterior
        if group['Frame'].duplicated().any():
            frames = list(set(group['Frame']))
            new_group = []
            for f in range(len(frames)):
                df_frame = group[group['Frame'] == frames[f]]
                if f == 0:
                    df_frame['previous_x'] = np.nan
                    df_frame['previous_y'] = np.nan
                else:
                    df_frame['previous_x'] = group[group['Frame'] == frames[f-1]]['X'].iloc[0]
                    df_frame['previous_y'] = group[group['Frame'] == frames[f-1]]['Y'].iloc[0]
                new_group.append(df_frame)
            group = pd.concat(new_group)
        else:
            group['previous_x'] = group['X'].shift(1)
            group['previous_y'] = group['Y'].shift(1)
        dfs.append(group)

    return pd.concat(dfs)


def run_laptracker(
        path_to_table: str,
        max_distance: int = 30,
        time_window: int = 5,
        max_split_distance: int = 10,  # essa aqui que separa os segmentos mto grudados (2024)
        max_gap_closing_distance: int = 30,
        # esse valor e muio chave. Se ele for baixo vai gerar segmentos ligados de lugares nada a ver nas arvores
        allow_merging=True
) -> pd.DataFrame:
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
    tracked_df = find_previous_positions(tracked_df)

    return tracked_df


def calc_smaller_distance(
        df: pd.DataFrame,
        cell: pd.Series
) -> pd.Series:
    """
    Measures the distance between a cell, represented by a row of the dataframe, to all cells in a dataframe.
    Returns the row with smaller distance
    """
    previous_frame = cell['Frame'] - 1
    df_previous_frame = df[df['Frame'] == previous_frame]
    if df_previous_frame.empty:
        previous_frame = df[df['Frame'] < previous_frame]['Frame'].max()
        df_previous_frame = df[df['Frame'] == previous_frame]
    x = cell['X']
    y = cell['Y']
    df_previous_frame['distance'] = np.sqrt(
        df_previous_frame['X'].apply(lambda n: (n - x) ** 2) + df_previous_frame['Y'].apply(lambda n: (n - y) ** 2)
    )
    closer = df_previous_frame.sort_values(by=['distance']).iloc[0]

    return closer


def find_family(
        df: pd.DataFrame,
        min_frame: int,
        max_distance: int
) -> pd.DataFrame:
    """ Attributes all tracks to a family. """
    df['family'] = None
    df = df.sort_values(by='Frame')
    for name, group in df.groupby('track_id', sort=False):
        if min_frame in list(group['Frame']):
            df.loc[group.index, 'family'] = name
        else:
            row = group.sort_values(by="Frame").iloc[0]
            closer_cell = calc_smaller_distance(df, row)
            if closer_cell['distance'] <= max_distance:
                df.loc[group.index, 'family'] = closer_cell['family'] if closer_cell['family'] is not None else name
                df.at[group.sort_values(by="Frame").index[0], 'previous_x'] = closer_cell['X']
                df.at[group.sort_values(by="Frame").index[0], 'previous_y'] = closer_cell['Y']
            else:
                df.loc[group.index, 'family'] = name
    return df


def create_tree_nomenclature(df: pd.DataFrame, max_gap_closing_distance) -> pd.DataFrame:
    """ Based on track and family information, creates cell nomenclature for each family"""
    df['family_name'] = None
    for family, df_family in df.groupby('family'):
        df_family['family_name'] = str(f'{family}.')
        df.loc[df_family.index, 'family_name'] = str(f'{family}.')
        same_parent = df_family[
            df_family.duplicated(subset=['previous_x', 'previous_y', 'Frame'], keep=False)].sort_values(
            by='Frame').dropna(subset='previous_x')
        for frame in sorted(list(set(same_parent['Frame']))):
            df_frame = df_family[df_family['Frame'] == frame]  # células duplicadas em um frame
            # como pode haver 2 divisões celulares em uma mesma familia em dado tempo, eu agrupo as células novamente
            # pelos previous x e y
            for sisters_name, df_sisters in df_frame.groupby(['previous_x', 'previous_y']):
                track_ids = list(df_sisters['track_id'])
                if len(set(track_ids)) > 1:
                    # para garantir se não é uma das células que o tracker coloca no memso segmento (mesmo sendo duas diferentes)
                    previous_cell = df[(df['Frame'] == frame - 1) &
                                       (df['X'] == df_sisters['previous_x'].iloc[0]) &
                                       (df['Y'] == df_sisters['previous_y'].iloc[0])]
                    # pode ser vazio por não ter análise no tempo anterior ou
                    # pode ser vazio pq o tracker linkou o segmento ao longo do tempo, então tenho que ir voltando
                    # considerando o time_gap
                    if previous_cell.empty:
                        for subtractor in range(2, max_gap_closing_distance+1):
                            previous_cell = df[(df['Frame'] == frame - subtractor) &
                                               (df['X'] == df_sisters['previous_x'].iloc[0]) &
                                               (df['Y'] == df_sisters['previous_y'].iloc[0])]
                            if not previous_cell.empty:
                                break

                    sisters_track_ids = list(df_sisters['track_id'])
                    #df a partir desse frame até o fim com o track_id uando o nome da previus cell
                    i = 1
                    for sister_id in sisters_track_ids:
                        df_cell = df[(df['Frame'] >= frame) & (df[
                                                                   'track_id'] == sister_id)]  # todos os frames a aprtir do atual no track dessa célula
                        family_name_sister = str(f"{previous_cell['family_name'].iloc[0]}{i}.")
                        df.loc[df_cell.index, 'family_name'] = family_name_sister
                        i += 1
                    #coloco .1, .2 etc agora, pq peguei todas que vieram de uma mesma cell

    return df


def tracking(
        path_to_table: str,
        max_distance: int = 30,
        time_window: int = 5,
        max_split_distance: int = 10,  # essa aqui que separa os segmentos mto grudados (2024)
        max_gap_closing_distance: int = 30,
) -> None:

    df = run_laptracker(path_to_table, max_distance, time_window, max_split_distance, max_gap_closing_distance)
    min_frame = df['Frame'].min()
    df = find_family(df, min_frame, max_distance)
    df = create_tree_nomenclature(df, max_gap_closing_distance)

    return df


# ajustar função abaixo
def draw_track(df, folder, save):
    img_col = [f for f in df.columns if 'Image_name' in f][0]
    df['family_color'] = None
    for family, df_family in df.groupby('family'):
        seq = list(range(0, 256))
        random_color = (random.choice(seq), random.choice(seq), random.choice(seq))
        df.loc[df['family'] == family, 'family_color'] = [str(random_color)] * len(df_family)
    df['family_color'] = df['family_color'].apply(ast.literal_eval)

    for frame, df_frame in df.groupby("Frame"):
        df = df.sort_values(by='Frame')
        image_to_open = df_frame[img_col].iloc[0]
        img = cv.imread(os.path.join(folder, image_to_open))
        df_0 = df.loc[df['Frame'] == frame]
        coordinates = list(zip(df_0['X'].astype(int), df_0['Y'].astype(int)))
        track = list(df_0['track_id'].astype(str))
        family_name = list(df_0['family_name'].astype(str))
        color = list(df_0['family_color'])
        [cv.circle(img, f, 2, (171, 235, 85), 2) for f in coordinates]
      #  [cv.putText(img, f, g, cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 1) for f, g in zip(track, coordinates)]
        [cv.putText(img, f, (g[0] + 35, g[1]), cv.FONT_HERSHEY_SIMPLEX, 0.7, h, 1) for f, g, h in
         zip(family_name, coordinates, color)]

        tracks_df = df.loc[df["Frame"] <= frame].sort_values(by='Frame')
        tracks_df = tracks_df.loc[tracks_df["Frame"] >= frame-15].sort_values(by='Frame')
        line = list(zip(tracks_df['X'], tracks_df['Y']))
        line_previous = list(zip(tracks_df['previous_x'], tracks_df['previous_y']))
        color_list = list(tracks_df['family_color'])
        for f, g, h in zip(line, line_previous, color_list):
            if not np.isnan(f[0]) and not np.isnan(g[0]):
                g = (int(g[0]), int(g[1]))
                cv.line(img, f, g, h, thickness=1)

        cv.imwrite(save + str(frame) + '.jpeg', img)

    return

#path_to_table = '/media/luiza/DATA/Doutorado/forNMA/experimentos/exp_kaka/populacional 1/exp kaka populacional 1/results/dados para tracking/results/GREEN_D9_2 Registered/Results_NMA_para_tracking.csv'
#df = tracking(path_to_table,30, 5, 10,  10 )

#df.to_csv('/media/luiza/DATA/Doutorado/forNMA/experimentos/exp_kaka/populacional 1/exp kaka populacional 1/results/dados para tracking/results/GREEN_D9_2 Registered/tracked.csv')