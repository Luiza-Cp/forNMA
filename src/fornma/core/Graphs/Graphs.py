#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 09:04:52 2022

@author: luiza
"""
import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib
import pandas as pd
from typing import Optional, List
import math
import os
from datetime import datetime
from ..NMA.NMA_draggable_line import draggable_lines
import matplotlib.patches as patches
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
if not os.environ.get('MPLBACKEND'):
    try:
        matplotlib.use('TkAgg')
    except ImportError:
        matplotlib.use('Agg')


class Graphs:
    """ Class containing graph plotting functions. """

    def __init__(self, df, overtime, groups, times, path_save):
        """
        Attributes:
        
        self.df = dataframe containing all population information
        self.overtime: boolean indicating if data is a time sequence
        self.conditions: conditions to be plotted
        self.times: frames to be plotted
        self.fig_width: width of generated figure
        self.subset: filtered dataframe with only frames and conditions specified by user
        self.path_save: string referring to path to save results
        """

        self.df = df
        self.overtime = overtime
        self.conditions = groups
        self.times = times
        self.fig_width = self.calc_fig_width()
        self.subset = self.subset_df()
        self.path_save = path_save

    def is_in_df(self,
                 values: List[str]):
        """Checks if a column is in dataframe and throw an exception if not"""

        for val in values:
            if val is not None and val not in self.df.columns:
                raise Exception(f'Can not find the column {val} in the table. Did you type it right? '
                                f'Check your column names and try again')

        return

    def subset_df(self):

        """ Subsets the self dataframe based on given groups and/or frames"""

        if not self.overtime:
            df = self.df if self.conditions is None else self.df[self.df['Condition'].isin(self.conditions)]
            if self.times is not None and len(self.times) > 1:
                df = df[df['Frame'].isin(self.times)]

        elif self.overtime:
            df = self.df if self.times is None else self.df[self.df['Frame'].isin(self.times)]
            if self.times is not None and self.conditions is not None and len(self.conditions) > 1:
                df = df[df['Condition'].isin(self.conditions)]

        else:
            df = self.df

        return df


    def _raster_scatter_to_array(self, df, x, y, hue=None, size=None, dpi=300, xlim=None, ylim=None):
        """Renderiza um scatter em memória e retorna (img[numpy], xlim, ylim)."""
        sns.set_theme(style="white")  # sem grid

        fig, ax = plt.subplots(figsize=(7, 5), dpi=dpi)

        if xlim is None:
            xr = df[x].to_numpy()
            pad = (np.nanmax(xr) - np.nanmin(xr)) * 0.03 or 1.0
            xlim = (float(np.nanmin(xr) - pad), float(np.nanmax(xr) + pad))
        if ylim is None:
            yr = df[y].to_numpy()
            pad = (np.nanmax(yr) - np.nanmin(yr)) * 0.03 or 1.0
            ylim = (float(np.nanmin(yr) - pad), float(np.nanmax(yr) + pad))

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_facecolor('#E5E5E5')
        # Scatter sempre com Seaborn e paleta rainbow
        sns.scatterplot(data=df, x=x, y=y, hue=hue, size=size, palette="rainbow", ax=ax, rasterized=True)

        # limpar ruído visual
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis("off")

        for sp in ax.spines.values():
            sp.set_visible(False)
        fig.tight_layout(pad=0)

        # Canvas Agg -> numpy
        canvas = FigureCanvas(fig)
        canvas.draw()
        buf = np.asarray(canvas.buffer_rgba())[:, :, :3].copy()

        plt.close(fig)
        return buf, xlim, ylim


    def gate(self, x, y, hue=None, size=None, log_file="logs-fornma.txt"):
        sns.set_theme(style="white")  # sem grid


        df = self.subset

        img, xlim, ylim = self._raster_scatter_to_array(df, x, y, hue=hue, size=size, dpi=300)

        # Posições iniciais
        x0, xf = df[x].quantile(.05), df[x].quantile(.95)
        y0, yf = df[y].quantile(.05), df[y].quantile(.95)

        # Mostrar imagem
        fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
        ax.imshow(img, origin='upper', extent=[*xlim, *ylim], aspect='auto')
        ax.set_facecolor('#E5E5E5')

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.grid(False)

        ax.set_xlabel(x)
        ax.set_ylabel(y)

        ax.set_title('Click once to move the lines. Click again to release')

        # Linhas arrastáveis
        upper_line = draggable_lines(ax, 'h', yf, [xlim[0], xlim[1]])
        bottom_line = draggable_lines(ax, 'h', y0, [xlim[0], xlim[1]])
        left_line = draggable_lines(ax, 'v', x0, [ylim[0], ylim[1]])
        right_line = draggable_lines(ax, 'v', xf, [ylim[0], ylim[1]])

        plt.show(block=True)
        plt.close('all')

        # Limites finais
        upper = float(df[y].max()) if upper_line.x is None else float(upper_line.x)
        bottom = float(df[y].min()) if bottom_line.x is None else float(bottom_line.x)
        left = float(df[x].min()) if left_line.x is None else float(left_line.x)
        right = float(df[x].max()) if right_line.x is None else float(right_line.x)

        if left > right:
            left, right = right, left
        if bottom > upper:
            bottom, upper = upper, bottom

        # Filtra DF
        df_gated = df.loc[(df[y] < upper) & (df[y] > bottom) & (df[x] < right) & (df[x] > left)]
        self.subset = df_gated

        # Salva CSV
        out_csv = os.path.join(self.path_save, "Gated results.csv")
        df_gated.to_csv(out_csv, index=False)

        # Snapshot com retângulo
        fig2, ax2 = plt.subplots(figsize=(7, 5), dpi=150)
        ax2.imshow(img, origin='upper', extent=[*xlim, *ylim], aspect='auto')
        ax2.set_xlim(*xlim)
        ax2.set_ylim(*ylim)
        rect = patches.Rectangle((left, bottom), right - left, upper - bottom,
                                 linewidth=1, edgecolor='r')
        ax2.add_patch(rect)
        fig2.tight_layout(pad=0)
        out_png = os.path.join(self.path_save, "Gate.png")
        fig2.savefig(out_png, dpi=300)
        plt.close(fig2)

        # Log
        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        info = (f"\n\n{dt} - Gate applied:\n"
                f"{x} min: {left}\n"
                f"{x} max: {right}\n"
                f"{y} min: {bottom}\n"
                f"{y} max: {upper}\n")
        with open(os.path.join(self.path_save, log_file), "a") as logs:
            logs.write(info)

        return None

    def calc_fig_width(self):
        """ based on s_o and in the amount of data to be plotted, finds the best figure width"""

        if not self.overtime and self.conditions is not None:
            if len(self.conditions) <= 5:
                size = 2 * len(self.conditions)
            elif len(self.conditions) <= 20:
                size = 10  # checar se 10 é um número ok ou se tem que ser mais
            else:
                size = 1 / 3 * len(self.conditions)  # checar se não fica ridículo 1/3

        elif self.overtime and self.times is not None:
            if len(self.times) <= 5:
                size = 2 * len(self.times)
            elif len(self.times) <= 20:
                size = 10  # checar se 10 é um número ok ou se tem que ser mais
            else:
                size = 1 / 3 * len(self.times)  # checar se não f
        else:
            size = 10

        return size

    def violinplot(self,
                   y: str,
                   hue: Optional[str] = None):
        """  Plots a violin plot with all conditions in a frame or all frames in a condition"""

        sns.set_theme()
        x = "Frame" if self.overtime else "Condition"
        fig = plt.figure(figsize=(self.fig_width, 6))
        ax = sns.violinplot(x=x, hue=hue, y=y, data=self.subset, inner=None, palette="rainbow")

        return fig

    def boxplot(self,
                y: str,
                hue: Optional[str] = None,
                log: Optional[bool] = False):

        sns.set_theme()
        x = "Frame" if self.overtime else "Condition"
        fig = plt.figure(figsize=(self.fig_width, 6))
        ax = sns.boxplot(x=x, hue=hue, y=y, data=self.subset, palette="rainbow")
        if log:
            plt.yscale('log')
        return fig

    def stripplot(self,
                  y: str,
                  hue: Optional[str] = None):

        sns.set_theme()
        x = "Frame" if self.overtime else "Condition"
        fig = plt.figure(figsize=(self.fig_width, 6))
        ax = sns.stripplot(x=x, hue=hue, y=y, data=self.subset, palette="rainbow")

        return fig

    def barplot(self,
                y: str,
                hue: Optional[str] = None):

        if hue is not None:
            l = len(list(set(self.subset[hue])))
            width = self.fig_width * l / 2
        else:
            width = self.fig_width

        sns.set_theme()
        x = "Frame" if self.overtime else "Condition"
        fig = plt.figure(figsize=(width, 6))
        ax = sns.barplot(x=x, hue=hue, y=y, data=self.subset, palette="rainbow")

        return fig

    def box_dot(self,
                y: str,
                hue: Optional[str] = None):

        if hue is not None:
            l = len(list(set(self.subset[hue])))
            width = self.fig_width * l / 2
        else:
            width = self.fig_width

        sns.set_theme()
        x = "Frame" if self.overtime else "Condition"
        fig = plt.figure(figsize=(width, 6))
        ax = sns.boxplot(x=x, y=y, hue=hue, data=self.subset, palette="rainbow")
        ax = sns.stripplot(x=x, y=y, data=self.subset, color="gray", edgecolor="gray", size=3)

        return fig

    def violin_dot(self,
                   y: str,
                   hue: Optional[str] = None):

        sns.set_theme()
        x = "Frame" if self.overtime else "Condition"
        fig = plt.figure(figsize=(self.fig_width, 6))
        ax = sns.violinplot(x=x, y=y, data=self.subset, inner=None, palette="rainbow")
        ax = sns.stripplot(x=x, y=y, data=self.subset, color="gray", edgecolor="gray", size=3)

        return fig

    def scatterplot(self,
                    x: str,  # add hue_norm and size_norm? e xy limits?
                    y: str,
                    hue: Optional[str] = None,
                    size: Optional[str] = None):

        """ 
        Groups the subset dataframe in conditions or frames or both and sends 
        each group to scatterplot functon. Returns a list of figures from all
        scatter plots generated.
        """
        plots = []
        titles = []

        if self.conditions is not None and len(self.conditions) > 1 and self.times is not None and len(self.times) > 1:
            df_cond = self.subset.groupby('Condition')
            for cond_name, cond_group in df_cond:
                df_time = cond_group.groupby('Frame')
                for frame_name, frame_group in df_time:
                    txt = 'Scatterplot ' + str(cond_name) + ' frame ' + str(frame_name)
                    fig = self.plot_scatterplot(txt, frame_name, x, y, hue, size)
                    plots.append(fig)
                    titles.append(txt)

        elif self.conditions is not None and len(self.conditions) > 1:
            df_cond = self.subset.groupby('Condition')
            for cond_name, cond_group in df_cond:
                txt = 'Scatterplot ' + str(cond_name)
                fig = self.plot_scatterplot(txt, cond_group, x, y, hue, size)
                plots.append(fig)
                titles.append(txt)

        elif self.times is not None and len(self.times) > 1:
            df_time = self.subset.groupby('Frame')
            for frame_name, frame_group in df_time:
                txt = 'Scatterplot Frame ' + str(frame_name)
                fig = self.plot_scatterplot(txt, df_time, x, y, hue, size)
                plots.append(fig)
                titles.append(txt)

        else:
            fig = self.plot_scatterplot("Scatterplot", self.subset, x, y, hue, size)
            plots.append(fig)
            titles.append("Scatterplot")

        return plots, titles

    def plot_scatterplot(self,
                         name: str,
                         group: pd.DataFrame,
                         x: str,
                         y: str,
                         hue: Optional[str] = None,
                         size: Optional[str] = None):

        """ Plots scatter plots and returns a figure containing the plot """
        fig = plt.figure(figsize=(self.fig_width, 6))
        sns.set_theme()
        group = group.apply(lambda x: x)

        ax = sns.scatterplot(data=group, x=x, y=y, size=size, hue=hue, palette='rainbow')
        sns.regplot(data=group, x=x, y=y, scatter=False, color='gray')
        ax.set_title(name)
        plt.xticks(rotation=70)

        return fig

    # lineplot só aparace pro overime
    def lineplot(self,
                 y: str,
                 frames: Optional[List[int]] = None,
                 size: Optional[str] = None,
                 ci: Optional[int] = None,  # confidence interval
                 style: Optional[str] = None,  # tipo da linha de acordo comn o plot -> indica feature
                 hue: Optional[str] = None,
                 individual: bool = False,
                 x: str = None,
                 control: str = None,
                 n: int = None,
                 dot: bool = None):  # plotar cada
        # item (se tem tracking) como uma linha -> Usar segment_ID

        df = self.subset
        if frames is not None:
            df = df[df['Frame'].isin(frames)]

        x = 'Frame'
        units = "segment_ID" if individual is True else None
        fig = plt.figure(figsize=(self.fig_width, 6))
        sns.set_theme()
        ax = sns.lineplot(data=df, x=x, y=y, hue=hue, style=style,
                          size=size, errorbar=ci, legend="full", units=units,
                          palette='rainbow')
        plt.xticks(rotation=70)

        return fig

    def rolling_average(self,
                        y: str,
                        n: str):  # number to group for moving average

        fig = plt.figure(figsize=(self.fig_width, 6))
        conditions = list(set(list(self.subset["Condition"])))
        sns.set_theme()

        for c in conditions:
            df_plot = self.subset.loc[self.subset["Condition"] == c]
            mean = df_plot.groupby("Frame")[y].mean()
            moving_df = mean.to_frame()
            moving_df["Frame"] = moving_df.index
            moving_df["Condition"] = [c] * moving_df.shape[0]
            moving_avg = moving_df[y].rolling(n).mean()
            moving_df[y] = moving_avg
            ax = sns.lineplot(data=moving_df, y=y, x="Frame")

        plt.title("Rolling average " + str(n) + " frames")
        plt.legend(conditions)

        return fig

    def cpd(self,
            frames: List[int],
            control: Optional[str] = False):

        """ Measures the Cumulative Population Doubling of a cell population, given
        a dataframe and a list of timepoints
        Each frame must correspond to a day"""

        dict_of_pd_lists = {}
        conditions = sorted(set(list(self.subset["Condition"].dropna().astype(str))))
        if control and control in conditions:
            conditions.remove(control)
            conditions.insert(0, control)
        if frames is None:
            frames = list(set(self.subset["Frame"]))
        frames = sorted(dict.fromkeys([int(frame) for frame in frames]))

        df = self.subset[self.subset["Frame"].isin(frames)]
        skipped_intervals = []
        for c in conditions:
            df_plot = df[df["Condition"].astype(str) == c]  # subsets each condition
            n_cell = df_plot["Frame"].value_counts().reindex(frames, fill_value=0).astype(float).tolist()

            cpd_values = [0.0]
            accumulated = 0.0
            for n in range(len(n_cell) - 1):
                n0 = n_cell[n]
                n1 = n_cell[n + 1]
                if n0 <= 0 or n1 <= 0:
                    skipped_intervals.append(f"{c}[{frames[n]}->{frames[n + 1]}]")
                    cpd_values.append(accumulated)
                    continue
                accumulated += math.log(n1 / n0, 2)
                cpd_values.append(accumulated)
            dict_of_pd_lists[c] = cpd_values

        fig = plt.figure(figsize=(self.fig_width, 6))
        sns.set_theme()
        sns.set_palette('rainbow', 8)
        x = frames
        for key, value in dict_of_pd_lists.items():
            ax = sns.lineplot(y=value, x=x, marker='s', sort=False)
        plt.legend(dict_of_pd_lists.keys())
        ax.set_title("Cumulative Population Doubling")
        plt.xlabel('Frame')
        plt.ylabel('CPD')
        if skipped_intervals:
            print("CPD skipped intervals with zero counts: " + ", ".join(skipped_intervals))
        print(dict_of_pd_lists) # melhorar esse return aqui

        return fig

    def save_figs(self,
                  fig: plt.figure,
                  title: str):
        png = title + '.png'
        svg = title + ".svg"
        try:
            fig.savefig(os.path.join(self.path_save, png))
            fig.savefig(os.path.join(self.path_save, svg))
            dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            with open(os.path.join(self.path_save, "logs-fornma.txt"), "a") as logs:
                logs.write(f'\n{dt} - Save {title} plot')
        except Exception:
            print(f'Error while saving figure {title}. Check your saving path and try again.')

        return None
