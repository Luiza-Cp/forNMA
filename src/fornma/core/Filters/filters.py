#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 08:58:39 2022

@author: luiza
"""

import os
import pickle
from typing import Optional
from datetime import datetime

import matplotlib
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

#from src.Graphs.Graph_class import check_column_names
from fornma.NMA.NMA_draggable_line import draggable_lines
from fornma.Segmentation.analyze import saving_images
from rich.progress import track

try:
    matplotlib.use('TkAgg')
except ImportError:
    matplotlib.use('Agg')


def filter_table(path_to_table: str,
                 x: str,
                 y: str,
                 path_save: str,
                 ) -> tuple[pd.DataFrame, tuple[float, float, float, float]]:
    """
    Gets a dataframe and plots a scatterplot for region selection by user.
    Returns a dataframe with user-defined subset.
    """
    df = pd.read_csv(path_to_table)

    sns.set_theme()

    x0 = df[x].quantile(.05)
    xf = df[x].quantile(.95)
    y0 = df[y].quantile(.05)
    yf = df[y].quantile(.95)

    x_quantile = df[x].quantile(.2)
    y_quantile = df[y].quantile(.2)

    fig = plt.figure()
    ax = fig.add_subplot(sns.scatterplot(data=df, x=x, y=y, palette='rainbow'))
    ax.set_title('Click once to move the lines. Click again to release')

    upper_line = draggable_lines(ax, 'h', int(yf), [int(df[x].min() - x_quantile), int(df[x].max() + x_quantile)])
    bottom_line = draggable_lines(ax, 'h', y0, [int(df[x].min() - x_quantile), int(df[x].max() + x_quantile)])
    left_line = draggable_lines(ax, 'v', x0, [int(df[y].min() - y_quantile), int(df[y].max() + y_quantile)])
    right_line = draggable_lines(ax, 'v', xf, [int(df[y].min() - y_quantile), int(df[y].max() + y_quantile)])

    plt.show(block=True)

    upper = upper_line.x
    bottom = bottom_line.x
    left = left_line.x
    right = right_line.x

    plt.close('all')

    df2 = df.loc[(df[y] < upper) & (df[y] > bottom)]
    df2 = df2.loc[(df2[x] < right) & (df2[x] > left)]
    df2.to_csv(os.path.join(path_save, 'Gated results.csv'))

    return df2, (bottom, upper, left, right)


def draw_images(df_results: pd.DataFrame,
                path_to_pickle_folder: str,
                path_to_save: str,
                ) -> None:
    pkls = os.listdir(path_to_pickle_folder)
    pkls = [os.path.join(path_to_pickle_folder, f) for f in pkls if f.endswith('.pkl')]
    save_pickle_path = os.path.join(path_to_save, 'pkl-data-filtered')
    os.makedirs(save_pickle_path, exist_ok= True)

    for pkl in track(pkls, description='Re-drawing images...'):
        with open(pkl, 'rb') as p:
            df_draw = pickle.load(p)

        df_results_image = df_results.loc[df_results['Frame'] == df_draw['Frame'].iloc[0]]
        cells_to_keep = list(df_results_image['Cell'])
        df_draw = df_draw[df_draw['Cell'].isin(cells_to_keep)]
        channel_names = [f.replace('Image_name_', '') for f in df_results if f.startswith('Image_name')]

        saving_images(df_draw, path_to_save, channel_names, df_draw['use_cellpose'].iloc[0])
        df_draw.to_pickle(os.path.join(save_pickle_path, os.path.basename(pkl)))

    return


def filters(path_to_table: str,
            path_to_save: str,
            draw: bool,
            column_x: str = 'Area',
            column_y: str = 'NII',
            path_to_piclke_folder: Optional[str] = None,
            ):
    filtered_df, info_filter = filter_table(path_to_table, column_x, column_y, path_to_save)
    draw_images(filtered_df, path_to_piclke_folder, path_to_save) if draw else None

    dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    info = f'\n\n{dt} - Filter applied:\n' \
           f'{column_x} minimum: {info_filter[2]}\n' \
           f'{column_x} minimum: {info_filter[3]}\n' \
           f'{column_y} minimum: {info_filter[0]}\n' \
           f'{column_y} minimum: {info_filter[1]}\n'
    with open(os.path.join(path_to_save, "logs-fornma.txt"), "a") as logs:
        logs.write(info)

    return print('Complete!')
