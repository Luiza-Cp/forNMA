#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 08:58:39 2022

@author: luiza
"""

import pandas as pd
import seaborn as sns
import matplotlib
from matplotlib import pyplot as plt
from .NMA_draggable_line import draggable_lines
import os
matplotlib.use('TkAgg')


def gating(path: str,
           x: str,
           y: str,
           path_save: str,
           ) -> pd.DataFrame:
    """
    Gets a dataframe and plots a scatterplot for region selection by user.
    Returns a dataframe with user-defined subset.
    """
    df = pd.read_csv(path)

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
    df2.to_csv(os.path.join(path_save, 'Gated results table.csv'))

    return os.path.join(path_save, 'Gated results table.csv')
