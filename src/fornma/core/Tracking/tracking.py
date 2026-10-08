import os
import pandas as pd
import numpy as np
from .LapTracker.LapTracker import LapTracker
import cv2 as cv
import random
import ast
import random
from fornma.core.image_io import imread, imwrite

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
        image_col: str | None = None,
        max_distance: int = 30,
        time_window: int = 5,
        max_split_distance: int = 10,  # essa aqui que separa os segmentos mto grudados (2024)
        max_gap_closing_distance: int = 30,
        # esse valor e muio chave. Se ele for baixo vai gerar segmentos ligados de lugares nada a ver nas arvores
        allow_merging=True
) -> pd.DataFrame:
    """ Gets a dataframe and user parameters and applies LapTracker for cell tracking."""

    table = pd.read_csv(path_to_table)
    cols_all = [str(c) for c in table.columns]
    img_name = None
    if image_col:
        if image_col in cols_all:
            img_name = image_col
        else:
            norm = str(image_col).strip().casefold()
            img_name = next((c for c in cols_all if str(c).strip().casefold() == norm), None)
    if img_name is None:
        img_name = next((c for c in cols_all if "image_name" in str(c).strip().casefold()), None)
    if img_name is None:
        raise KeyError("Image column not found in tracking table")

    cols = ['Cell', 'X', "Y", 'Frame', img_name]
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
        saving_path: str,
        max_distance: int = 30,
        time_window: int = 5,
        max_split_distance: int = 10,  # essa aqui que separa os segmentos mto grudados (2024)
        max_gap_closing_distance: int = 30,
) -> None:

    df = run_laptracker(
        path_to_table,
        image_col=None,
        max_distance=max_distance,
        time_window=time_window,
        max_split_distance=max_split_distance,
        max_gap_closing_distance=max_gap_closing_distance,
    )
    min_frame = df['Frame'].min()
    df = find_family(df, min_frame, max_distance)
    df = create_tree_nomenclature(df, max_gap_closing_distance)
    results_df = pd.read_csv(path_to_table, index_col=0)
    img_col = [f for f in df.columns if f.startswith('Image_name')][0]
    df = df.merge(results_df, on=['Frame', 'Cell', 'X', 'Y', img_col])
    df.to_csv(os.path.join(saving_path, 'Tracked  Results.csv'))

    return None


def _family_color_map(family):
    # cor determinística por família (evita mudar a cada execução)
    random.seed(hash(family) & 0xffffffff)
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))  # BGR no OpenCV


def _to_display_bgr(img):
    """Contrast-stretch an image of any bit depth to 8-bit BGR so dim microscopy frames are readable."""
    arr = np.asarray(img, dtype=np.float32)
    if arr.ndim == 2:
        arr = arr[..., None]
    lo, hi = np.percentile(arr, (1, 99.8))
    if hi <= lo:
        hi = lo + 1.0
    out = (np.clip((arr - lo) / (hi - lo), 0.0, 1.0) * 255).astype(np.uint8)
    if out.shape[2] == 1:
        return cv.cvtColor(out, cv.COLOR_GRAY2BGR)
    return out[..., :3]


def draw_track(df, folder, save, img_col, trail_window=15, point_radius=2, point_thickness=2, font_scale=0.7, text_thickness=1,
               enhance_contrast=True):


    if not img_col:
        raise KeyError("Image column not found")

    # garante colunas necessárias
    required = {'Frame','X','Y','track_id','family','family_name','previous_x','previous_y', img_col}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing columns: {missing}")

    os.makedirs(save, exist_ok=True)

    df = df.sort_values(by='Frame').copy()
    df['family_color'] = df['family'].map(_family_color_map)

    # loop por frame
    for frame, df_frame in df.groupby("Frame"):
        # Resolve caminho da imagem
        image_to_open = df_frame[img_col].iloc[0]
        img_path = image_to_open if os.path.isabs(image_to_open) else os.path.join(folder, image_to_open)
        img = imread(img_path, cv.IMREAD_UNCHANGED if enhance_contrast else cv.IMREAD_COLOR)
        if img is None:
            # pula frames com problema de leitura de imagem
            continue
        if enhance_contrast:
            img = _to_display_bgr(img)

        # pontos do frame atual
        df_0 = df_frame  # já é o frame atual
        coordinates = list(zip(df_0['X'].round().astype(int), df_0['Y'].round().astype(int)))
        family_name = list(df_0['family_name'].astype(str))
        colors_now = list(df_0['family_color'])

        # desenha pontos e labels
        for (x, y), fam, color in zip(coordinates, family_name, colors_now):
            cv.circle(img, (x, y), point_radius, color, point_thickness)
            # Lineage names end with "." in the table ("8.", "8.1."); drop it on screen.
            cv.putText(img, fam.rstrip('.'), (x + 35, y), cv.FONT_HERSHEY_SIMPLEX, font_scale, color, text_thickness, cv.LINE_AA)

        # desenha trilhas dos últimos N frames (inclui o atual)
        start = frame - trail_window
        tracks_df = df[(df["Frame"] >= start) & (df["Frame"] <= frame)].sort_values(by='Frame')
        # usa as mesmas cores por família
        for _, row in tracks_df.iterrows():
            x, y = row['X'], row['Y']
            px, py = row['previous_x'], row['previous_y']
            if np.isfinite(x) and np.isfinite(y) and np.isfinite(px) and np.isfinite(py):
                p1 = (int(round(x)), int(round(y)))
                p0 = (int(round(px)), int(round(py)))
                color = row['family_color']
                cv.line(img, p0, p1, color, thickness=1)

        # salva com zero-padding no frame (opcional)
        out_path = os.path.join(save, f"{int(frame):05d}.tiff")
        imwrite(out_path, img)


#path_to_table = '/media/luiza/DATA/Doutorado/forNMA/experimentos/exp_kaka/populacional 1/exp kaka populacional 1/results/dados para tracking/results/GREEN_D9_2 Registered/Results_NMA_para_tracking.csv'
#df = tracking(path_to_table,30, 5, 10,  10 )

#df.to_csv('/media/luiza/DATA/Doutorado/forNMA/experimentos/exp_kaka/populacional 1/exp kaka populacional 1/results/dados para tracking/results/GREEN_D9_2 Registered/tracked.csv')
