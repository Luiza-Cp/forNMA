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
from src.fornma.NMA.NMA_draggable_line import draggable_lines
matplotlib.use('TkAgg')


# essa classe pode ser usada para plotar foci individual
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

    def gate(self,
             x: str,
             y: str):
        """If gate is true, plots all the df info for user to select a piece of data to work with."""
        x0 = self.subset[x].quantile(.05)
        xf = self.subset[x].quantile(.95)
        y0 = self.subset[y].quantile(.05)
        yf = self.subset[y].quantile(.95)

        x_quantile = self.subset[x].quantile(.2)
        y_quantile = self.subset[y].quantile(.2)

        fig = plt.figure()
        ax = fig.add_subplot(sns.scatterplot(data=self.subset, x=x, y=y, palette='rainbow'))
        ax.set_title('Click once to move the lines. Click again to release')

        upper_line = draggable_lines(ax, 'h', int(yf), [int(self.subset[x].min() - x_quantile),
                                                        int(self.subset[x].max() + x_quantile)])
        bottom_line = draggable_lines(ax, 'h', y0, [int(self.subset[x].min() - x_quantile),
                                                    int(self.subset[x].max() + x_quantile)])
        left_line = draggable_lines(ax, 'v', x0, [int(self.subset[y].min() - y_quantile),
                                                  int(self.subset[y].max() + y_quantile)])
        right_line = draggable_lines(ax, 'v', xf, [int(self.subset[y].min() - y_quantile),
                                                   int(self.subset[y].max() + y_quantile)])

        plt.show(block=True)

        upper = self.df[y].max() if upper_line.x is None else upper_line.x
        bottom = self.df[y].min() if bottom_line.x is None else bottom_line.x
        left = self.df[x].min() if left_line.x is None else left_line.x
        right = self.df[x].max() if right_line.x is None else right_line.x

        plt.close('all')

        df2 = self.subset.loc[(self.subset[y] < upper) & (self.subset[y] > bottom)]
        df2 = df2.loc[(df2[x] < right) & (df2[x] > left)]
        self.subset = df2
        df2.to_csv(os.path.join(self.path_save, "Gated results.csv"))

        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        info = f'\n\n{dt} - Gate applied:\n' \
               f'{x} minimum: {left}\n' \
               f'{x} minimum: {right}\n' \
               f'{y} minimum: {bottom}\n' \
               f'{y} minimum: {upper}\n'

        with open(os.path.join(self.path_save, "logs-fornma.txt"), "a") as logs:
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
        ax = sns.swarmplot(x=x, y=y, data=self.subset, color="gray", edgecolor="gray", size=3)

        return fig

    def violin_dot(self,
                   y: str,
                   hue: Optional[str] = None):

        sns.set_theme()
        x = "Frame" if self.overtime else "Condition"
        fig = plt.figure(figsize=(self.fig_width, 6))
        ax = sns.violinplot(x=x, y=y, data=self.subset, inner=None, palette="rainbow")
        ax = sns.swarmplot(x=x, y=y, data=self.subset, color="gray", edgecolor="gray", size=3)

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
                          size=size, ci=ci, legend="full", units=units,
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
        conditions = sorted(set(list(self.subset["Condition"])))
        if control:
            conditions.remove(control)
            conditions.insert(0, control)
        if frames is None:
            frames = list(set(self.subset["Frame"]))

        df = self.subset[self.subset["Frame"].isin(frames)]
        # esse função temque ser ao contrario. Tem que ser oprimeiro frame e depois condição
        # ou tenhoq ue alterar alfo pra incluir uma contagem nos frames que não tem nada em uma dada condição
        for c in conditions:
            df_plot = df[df["Condition"] == c]  # subsets each condition
            num_cell = df_plot["Frame"].value_counts()  # counts number at each time
            num_cell = list(num_cell.sort_index())
            n_cell = [num_cell[n] for n in range(len(frames))]  # list with cell number

            pd_list = []

            for n in range(len(n_cell) - 1):
                fim = math.log(n_cell[n + 1])
                ini = math.log(n_cell[n])
                doubling = (fim - ini) / math.log(2)
                if n > 0:
                    doubling = doubling + pd_list[n - 1]
                pd_list.append(doubling)
            pd_list.insert(0, 0)
            dict_of_pd_lists[c] = pd_list

        fig = plt.figure(figsize=(self.fig_width, 6))
        sns.set_theme()
        sns.set_palette('rainbow', 8)
        x = list(range(len(frames)))
        for key, value in dict_of_pd_lists.items():
            ax = sns.lineplot(y=value, x=x, marker='s', sort=False)
        plt.legend(dict_of_pd_lists.keys())
        ax.set_title("Cumulative Population Doubling")
        plt.xlabel('Days')
        plt.ylabel('CPD')
        print (dict_of_pd_lists) # melhorar esse return aqui

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

#
# def check_column_names(df: pd.DataFrame,
#                        name: str):
#     """ Checks if DataFrame columns are the ones expected by forNMA. If not, raises an error."""
#
#     columns = ['Frame', 'Cell', 'X', 'Y', 'Area', 'Perimeter', 'Aspect', 'Extent', 'Roundness', 'Radius_ratio', 'NII',
#                'FitEllipse_X', 'FitEllipse_Y', 'FitEllipse_a', 'FitEllipse_b', 'FitEllipse_angle', 'Condition',
#                'Overtime']
#
#     if not all(item in df.columns for item in columns):
#         raise ValueError(
#             f"The table {name} does not have forNMA output column names. Rename your columns according to forNMA's "
#             f"standard outputs and try again.")
#
#     return None


def plot(path: str,
         path_save: str,
         conditions: Optional[List],
         frames: Optional[List],
         graph_type: str,
         gate: bool,
         **kwargs):
    df = pd.read_csv(path)
    # check_column_names(df, os.path.basename(path).replace('Results.csv', ''))
    ot = True if "Overtime" in df.columns and df['Overtime'].iloc[0] == True else False
    graphs = Graphs(df, ot, conditions, frames, path_save)
    graphs.is_in_df([kwargs.get('x'), kwargs.get('y'), kwargs.get('hue'), kwargs.get('size')])

    if gate:
        graphs.gate(kwargs.get('x'), kwargs.get('y'))

    dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(os.path.join(path_save, "logs-fornma.txt"), "a") as logs:
        logs.write(f'\n\n{dt} - {graph_type} plot')

    if graph_type == 'violin':
        if kwargs.get('dot'):
            print('violin-if')
            graphs.save_figs(graphs.violin_dot(kwargs.get('y'), kwargs.get('hue')), 'violin-dot-plot')
        else:
            graphs.save_figs(graphs.violinplot(kwargs.get('y'), kwargs.get('hue')), 'violin-plot')

    elif graph_type == 'box':
        if kwargs.get('dot'):
            graphs.save_figs(graphs.box_dot(kwargs.get('y'), kwargs.get('hue')), 'box-dot-plot')
        else:
            graphs.save_figs(graphs.boxplot(kwargs.get('y'), kwargs.get('hue')), 'box-plot')

    elif graph_type == 'dot':
        print('dot')
        graphs.save_figs(graphs.stripplot(kwargs.get('y'), kwargs.get('hue')), 'dot-plot')

    elif graph_type == 'bar':
        graphs.save_figs(graphs.barplot(kwargs.get('y'), kwargs.get('hue')), 'bar-plot')

    elif graph_type == 'scatter':
        figs, titles = graphs.scatterplot(kwargs.get('x'), kwargs.get('y'), kwargs.get('hue'), kwargs.get('size'))
        [graphs.save_figs(f, t) for f, t in zip(figs, titles)]

    elif graph_type == 'line':
        print(ot)
        if not ot:
            raise Exception(f'The Line plot is only available for data that has a time sequence. If this is your case,'
                            f' you mighthave to change the column "Overtime" values for "True" in order to proceed.')
        else:
            graphs.save_figs(graphs.lineplot(**kwargs), 'line-plot')

    elif graph_type == 'rolling-average':
        if not ot:
            raise Exception(f'The Rolling Average e plot is only available for data that has a time sequence. '
                            f'If this is your case, you might have to change the column "Overtime" values for '
                            f'"True" in order to proceed.')
        else:
            graphs.save_figs(graphs.rolling_average(kwargs.get('y'), kwargs.get('n')), 'rolling-average-plot')

    elif graph_type == 'cpd':
        if not ot:
            raise Exception(f'The Cumulative Population Doubling plot is only available for data that has a time '
                            f'sequence. If this is your case, you might have to change the column "Overtime"'
                            f' values for "True" in order to proceed.')
        else:
            graphs.save_figs(graphs.cpd(kwargs.get('frames'), kwargs.get('control')), 'cumulative-population-doubling')

    return f' Files were saved at {path_save}'

#
# p = '/home/luiza/Área de Trabalho/teste NMA/lap_lnc_tras1 Results.csv'
# ps = '/home/luiza/Área de Trabalho/teste NMA'
# cond = None
# frames = None
# gt = 'cpd'
# g = False
# x = 'Area'
# y = 'NII'
# hue = "Condition"
# size = None
# style = None
# ci = 0.95
# dot = False
# control = 'lnc1'
# n = 3

# plot(p, ps, cond, frames, gt, g, x=x, y=y, hue=hue, size=size, control=control, n=n, style=style, ci=ci, dot=dot)
