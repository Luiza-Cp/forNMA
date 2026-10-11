import os
from typing import Optional, List, Tuple
import pickle
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
import seaborn as sns
from matplotlib import pyplot as plt
from datetime import datetime
from scipy import stats
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')
import matplotlib

if not os.environ.get('MPLBACKEND'):
    try:
        matplotlib.use('TkAgg')
    except ImportError:
        matplotlib.use('Agg')

from fornma.runtime import nma_settings_path
CONFIG_PATH = nma_settings_path()

class NMA:
    """ Class for NMA graph plotting"""

    def __init__(self, df, parameters, graph_type, single, overtime, path_save, sample, sample_size, hue, size, palette,
                 hue_norm, size_norm):
        """
        Atributes:

        self.df: pandas DataFrame with all value information
        self.sd_area: float representing the number of standard deviations from the mean to use for NMA area threshold
        self.sd_NII: float representing the number of standard deviations from the mean to use for NMA NII threshold
        self.mean_NII: mean NII value of control group
        self.mean_a: mean area value of control group
        self.std_NII: distance from mean NII of the max or min value (the smallest is chosen)
        self.std_a: distance from mean area of the max or min value (the smallest is chosen)
        self.circle: numpy linespace for ellipse
        self.h_x: horizontal line x value
        self.h_y_up: horizontal upper line y coordinates
        self.h_y_down: horizontal lower line y coordinates
        self.v_upx: vertical upper line X coordinates
        self.v_upy: vertical upper line y coordinates
        self.v_midx: vertical middle line x coordinates
        self.v_midy: vertical middle line y coordinates
        self.v_downx: vertical bottom left line x coordinates
        self.v_downy: vertical bottom lines y coordinates
        self.v_downx2: vertical bottom right line x coordinates
        self.graph_limits: tuple with min and maximum area and NII values within 3 standard deviations
        self.percentages: dataframe with cell percentages at each NMA group
        self.palette: name of matplotlib or seaborn color palette
        self.hue_norm: tuple with min and max hue values
        self.size_norm: tuple with min and max size values
        """
        self.df = df
        self.sample_size = sample_size
        self.hue = hue
        self.size = size
        self.palette = palette
        self.hue_norm = hue_norm
        self.size_norm = size_norm
        self.sd_area = parameters['sd_area']
        self.sd_NII = parameters['sd_NII']
        self.mean_NII = parameters['mean_NII']
        self.mean_a = parameters["mean_a"]
        self.std_NII = parameters['std_NII']
        self.std_a = parameters['std_a']
        self.circle = parameters['circle']
        self.graph_limits = self.calc_area_NII_lims()
        self.ellipse = parameters['ellipse']
        self.h_x = parameters['h_x']
        self.h_y_up = parameters['h_y_up']
        self.h_y_down = parameters['h_y_down']
        self.graph_box = parameters['graph_box']
        self.v_upx = parameters['v_upx']
        self.v_upy = parameters['v_upy']
        self.v_midx = parameters['v_midx']
        self.v_midy = parameters['v_midy']
        self.v_downx = parameters['v_downx']
        self.v_downy = parameters['v_downy']
        self.v_downx2 = parameters['v_downx2']
        self.single = single
        self.graph_type = graph_type
        self.overtime = overtime
        self.percentages = self.calc_all_percentages(self.df)
        self.path_save = path_save
        self.sample = sample  # int or None
        self.sample_percentages = None
        self.plot()

    def heatmap_background_color(self):
        """Return the lowest-density color from the selected heatmap palette."""
        try:
            cmap = plt.get_cmap(self.palette or 'viridis')
            return cmap(0.0)
        except Exception:
            try:
                return sns.color_palette(self.palette or 'viridis', as_cmap=True)(0.0)
            except Exception:
                return plt.get_cmap('viridis')(0.0)

    def subset_df(self, condition_time_tuple):
        """ Subsets the self dataframe based in a condition or time frame or both."""

        if all(item is None for item in condition_time_tuple):
            df = self.df
        elif condition_time_tuple[1] is None:
            df = self.df.loc[self.df['Condition'] == condition_time_tuple[0]]
        elif condition_time_tuple[0] is None:
            df = self.df.loc[self.df['Frame'] == condition_time_tuple[1]]
        else:
            df = self.df.loc[self.df['Condition'] == condition_time_tuple[0]]
            df = df.loc[df['Frame'] == condition_time_tuple[1]]

        return df

    def calc_area_NII_lims(self):
        """ Given a dataframe, establishes NMA graph limits"""

        df = self.df[(np.abs(stats.zscore(self.df["Area"])) < 3)]
        df = df[(np.abs(stats.zscore(df["NII"])) < 3)]
        max_a = df['Area'].max()
        min_a = df['Area'].min() - df['Area'].min() / 3
        max_NII = df['NII'].max()
        min_NII = df['NII'].min() - df['NII'].min() / 3

        return min_a, max_a, min_NII, max_NII

    def get_NMA_classification_from_df(self, df):
        """Gets a dataframe and measures the percentage of nuclei in each NMA category."""

        total = df.shape[0]
        t = 100 / total
        lr = df.loc[(df['Area'] >= self.h_y_up[0]) & (df['NII'] < self.v_upx[0])].shape[0]
        li = df[(df['Area'] > self.h_y_up[0]) & (df['NII'] >= self.v_upx[0])].shape[0]
        n = df[(df['Area'] < self.h_y_up[0]) & (df['Area'] >= self.h_y_down[0]) &
               (df['NII'] < self.v_midx[0])].shape[0]
        i = df[(df['Area'] < self.h_y_up[0]) & (df['Area'] >= self.h_y_down[0]) &
               (df['NII'] > self.v_midx[0])].shape[0]
        sr = df[(df['Area'] < self.h_y_down[0]) & (df['NII'] < self.v_downx[0])].shape[0]
        s = df[(df['Area'] < self.h_y_down[0]) & (df['NII'] >= self.v_downx[0])
               & (df['NII'] < self.v_downx2[0])].shape[0]
        si = df[(df['Area'] < self.h_y_down[0]) & (df['NII'] >= self.v_downx2[0])].shape[0]

        return lr * t, li * t, n * t, i * t, sr * t, s * t, si * t

    def calc_all_percentages(self, df):
        """ Generates a dataframe containing the percentage relation of all NMA groups. """

        has_controls = df['Condition'].iloc[0] != False and len(set(list(df['Condition']))) > 0

        df_percent_rows = []

        if has_controls and df['Overtime'].iloc[0] == True:
            # tem controles E tempo
            conditions = df.groupby('Condition')
            for name, group in conditions:
                frames = group.groupby("Frame")
                for frame_name, frame in frames:
                    lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(frame)
                    new_row = [name, frame_name, frame.shape[0], lr, li, n, i, sr, s, si]
                    df_percent_rows.append(new_row)

        elif has_controls:
            conditions = df.groupby('Condition')
            for name, group in conditions:
                lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(group)
                new_row = [name, False, group.shape[0], lr, li, n, i, sr, s, si]
                df_percent_rows.append(new_row)

        elif df['Overtime'].iloc[0]:
            frames = df.groupby('Frame')
            for name, group in frames:
                lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(group)
                new_row = [False, name, group.shape[0], lr, li, n, i, sr, s, si]
                df_percent_rows.append(new_row)

        else:
            lr, li, n, i, sr, s, si = self.get_NMA_classification_from_df(df)
            new_row = [df['Condition'].iloc[0], False, df.shape[0], lr, li, n, i, sr, s, si]
            df_percent_rows.append(new_row)

        percent_df = pd.DataFrame(df_percent_rows,
                                  columns=["Condition", "Frame", 'Total Cells', 'LR', 'LI', 'N', 'I', 'SR', 'S', 'SI'])

        return percent_df


    def f_test(self,
               x: List[float],
               y: List[float]):
        """ Given two lists, performs the f statistic teste and returns the p value. """
        x = np.array(x)
        y = np.array(y)
        f = np.var(x, ddof=1) / np.var(y, ddof=1)  # calculate F test statistic
        dfn = x.size - 1  # define degrees of freedom numerator
        dfd = y.size - 1  # define degrees of freedom denominator
        p = 1 - stats.f.cdf(f, dfn, dfd)  # find p-value of F test statistic

        return p


    def get_sample(self,
                   df: pd.DataFrame,
                   hue: Optional[str],
                   size: Optional[str],
                   n: int = 500
                   ) -> Tuple[pd.DataFrame, bool]:
        """
        Finds statistically equal samples from a population based on Area,
        NII and other specified column values.
        """

        if df.shape[0] < n:
            return df, True

        df_sample = df.sample(n=n)
        p_NII_var = self.f_test(df['NII'].values, df_sample['NII'].values)
        p_a_var = self.f_test(df['Area'].values, df_sample['Area'].values)

        p_NII_mean = stats.ttest_ind(df['NII'].values, df_sample['NII'].values)[1]
        p_a_mean = stats.ttest_ind(df['Area'].values, df_sample['Area'].values)[1]

        p_hue_var = None if hue is None or not is_numeric_dtype(df_sample[hue]) \
            else self.f_test(df[hue].values, df_sample[hue].values)
        p_hue_mean = None if hue is None or not is_numeric_dtype(df_sample[hue]) \
            else stats.ttest_ind(df[hue].values, df_sample[hue].values)[1]
        p_size_var = None if size is None or not is_numeric_dtype(df_sample[size]) \
            else self.f_test(df[size].values, df_sample[size].values)
        p_size_mean = None if size is None or not is_numeric_dtype(df_sample[size]) \
            else stats.ttest_ind(df[size].values, df_sample[size].values)[1]

        p_values = [p_NII_var, p_NII_mean, p_a_var, p_a_mean, p_hue_var, p_hue_mean,
                    p_size_var, p_size_mean]

        p_values = [f for f in p_values if f is not None]

        if np.any(np.array(p_values) < 0.05):
            boolean = False
        else:
            boolean = True

        return df_sample, boolean

    def plot_NMA_heatmap(self,
                         condition_time_tuple: Tuple[Optional[str], Optional[int]],
                         title: str):
        """  Plots ONE heatmap NMA ignoring values passed as hue and size."""

        subset_of_df = self.subset_df(condition_time_tuple)
        background_color = self.heatmap_background_color()
        fig, ax = plt.subplots()
        ax.set_facecolor(background_color)
        sns.kdeplot(data=subset_of_df, x="NII", y="Area", cmap=self.palette,
                    fill=True, thresh=None, levels=60, ax=ax)
        ax.plot(self.h_x, self.h_y_up, self.h_x, self.h_y_down,
                self.v_upx, self.v_upy, self.v_midx, self.v_midy,
                self.v_downx, self.v_downy, self.v_downx2, self.v_downy,
                color='white', linewidth=0.75)

        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        ax.set_title(title)

        return fig


    def plot_NMA_jointplot(self,
                           condition_time_tuple: Tuple[Optional[str], Optional[int]],
                           title: str):
        """  Plots ONE jointplot NMA ignoring values passed as hue and size."""

        subset_of_df = self.subset_df(condition_time_tuple)
        background_color = self.heatmap_background_color()

        fig = sns.jointplot(data=subset_of_df, x="NII", y="Area", kind='kde', space=0, fill=True, thresh=0,
                            cmap=self.palette)
        fig.ax_joint.set_facecolor(background_color)
        fig.ax_marg_x.set_facecolor(background_color)
        fig.ax_marg_y.set_facecolor(background_color)
        fig.ax_marg_x.set_xlim(self.graph_limits[2], self.graph_limits[3])
        fig.ax_marg_y.set_ylim(self.graph_limits[0], self.graph_limits[1])
        #.plot(self.h_x, self.h_y_up, self.h_x, self.h_y_down,
        #        self.v_upx, self.v_upy, self.v_midx, self.v_midy,
        #        self.v_downx, self.v_downy, self.v_downx2, self.v_downy,
        #        color='white', linewidth=0.75)

        # ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        # ax.set_xlim(self.graph_limits[2], self.graph_limits[3])
        # ax.set_title(title)

        return fig

    def plot_NMA_dot(self,
                     condition_time_tuple: Tuple[Optional[str], Optional[int]],
                     hue: Optional[str] = None,
                     size: Optional[str] = None,
                     sample: bool = False,
                     title: str = 'NMA plot',
                     ):
        """
        Plots the NMA graph(scatterplot) with hue and size chosen by user. Same graph
        as the one defined by plot_NMA_200, but without performing sampling.
        When sample is enabled, it performs t test Statistics to get representative
        means of the population and f test for variances, for each measure to be plotted.
        It also does not plot the percentages in each graph group.
        """

        subset_of_df = self.subset_df(condition_time_tuple)
        percent = self.percentages
        df_sample = None
        if sample:
            df_sample, boolean = self.get_sample(subset_of_df, hue, size, self.sample_size)
            while not boolean:
                df_sample, boolean = self.get_sample(subset_of_df, hue, size, self.sample_size)

            subset_of_df = df_sample
            sample_percentages = self.calc_all_percentages(df_sample)
            percent = sample_percentages
            if self.sample_percentages is None:
                self.sample_percentages = sample_percentages
            else:
                self.sample_percentages = pd.concat([self.sample_percentages, sample_percentages])

        if all(item is None for item in condition_time_tuple):
            percentages = None
        if condition_time_tuple[0] is None:
            percentages = percent.loc[percent['Frame'] == condition_time_tuple[1]]
        elif condition_time_tuple[1] is None:
            percentages = percent.loc[percent['Condition'] == condition_time_tuple[0]]
        else:
            percentages = percent.loc[(percent['Condition'] == condition_time_tuple[0])]
            percentages = percentages.loc[percentages['Frame'] == condition_time_tuple[1]]

        # make the values out of graph limits group at the limit (cytometry-like)
        subset_of_df.loc[subset_of_df['NII'] >= self.graph_limits[3], 'NII'] = self.graph_limits[3] - 0.1
        subset_of_df.loc[subset_of_df['Area'] >= self.graph_limits[1], 'Area'] = self.graph_limits[1] - 10
        plt.rcParams['axes.facecolor'] = 'white'

        fig, ax = plt.subplots(1, figsize=(10, 6))

        if hue is not None and is_numeric_dtype(self.df[hue]) and self.hue_norm is None:
            df_hue = self.df[(np.abs(stats.zscore(self.df[hue].fillna(self.df[hue].mean()))) < 3)]
            self.hue_norm = (df_hue[hue].min(), df_hue[hue].max())


        if size is not None and is_numeric_dtype(self.df[size]) and self.size_norm is None:
            df_size = self.df[(np.abs(stats.zscore(self.df[size].fillna(self.df[size].mean()))) < 3)]
            self.size_norm = (df_size[size].min(), df_size[size].max())

        sns.scatterplot(data=subset_of_df, x="NII", y="Area", size=size, hue=hue,
                        hue_norm=self.hue_norm, size_norm=self.size_norm, ax=ax, palette=self.palette )
        ax.plot(self.mean_NII + (self.sd_NII * self.std_NII) * np.cos(self.circle),
                self.mean_a + (self.sd_area * self.std_a) * np.sin(self.circle), color='black')

        ax.plot(self.h_x, self.h_y_up, self.h_x, self.h_y_down,
                self.v_upx, self.v_upy, self.v_midx, self.v_midy,
                self.v_downx, self.v_downy,
                self.v_downx2, self.v_downy, color='black')

        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        plt.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)

        # ax.set_title(title)
        if isinstance(percentages, pd.DataFrame) or isinstance(percentages, pd.DataFrame) and sample:
            # checar se não e empty
            if percentages.shape[0] > 1:
                percentages = percentages.drop(columns=['Condition', 'Frame', 'Total Cells'])
                n = percentages.shape[0]
                percentages = (percentages.sum() / n).to_frame()
                percentages = percentages.transpose()

                ax.text(self.v_upx[0] - 1, self.h_y_up[0] + 0.1 * self.sd_area * self.mean_a,
                        str(round(percentages['LR'].iloc[0], 2)) + '%', size=10, bbox=self.graph_box)
                ax.text(self.v_upx[0] + 1, self.h_y_up[0] + 0.1 * self.sd_area * self.mean_a,
                        str(round(percentages['LI'].iloc[0], 2)) + '%', size=10, bbox=self.graph_box)
                ax.text(self.mean_NII, self.mean_a, str(round(percentages['N'].iloc[0], 2)) + '%',
                        size=10, bbox=self.graph_box)
                ax.text(self.v_midx[0] + 1, self.mean_a, str(round(percentages['I'].iloc[0], 2)) + '%',
                        size=10, bbox=self.graph_box)
                ax.text(self.v_downx[0] - 0.7, self.h_y_down[0] - 0.1 * self.sd_area * self.mean_a,
                        str(round(percentages['SR'].iloc[0], 2)) + '%', size=10, bbox=self.graph_box)
                mid_point = self.v_downx[0] + (self.v_downx2[0] - self.v_downx[0]) / 2
                ax.text(mid_point, self.h_y_down[0] - 0.1 * self.sd_area * self.mean_a,
                        str(round(percentages['S'].iloc[0], 2)) + '%', size=10, bbox=self.graph_box)
                ax.text(self.v_downx2[0] + 0.5, self.h_y_down[0] - 0.1 * self.sd_area * self.mean_a,
                        str(round(percentages['SI'].iloc[0], 2)) + '%', size=10, bbox=self.graph_box)

        ax.set_title(title)

        return fig, df_sample


    def percentages_overtime(self,
                             group: str,
                             frames: Optional[List[int]] = None):

        """ Given a group and an optional list of frames, plots the
        NMA groups percentage overtime"""

        df = self.percentages[self.percentages['Frame'].isin(frames)] if frames is not None else self.percentages
        df.drop(columns=['Total Cells'], inplace=True)
        df = df.loc[df['Condition'] == group]
        df.set_index('Frame', inplace=True)
        sns.set_palette(self.palette, 7)
        fig, ax = plt.subplots()
        df.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title('NMA groups')

        return fig


    def save_figs(self,
                  fig: plt.figure,
                  title: str):
        png = f'{title.lstrip()} {self.graph_type}.png'
        svg = f'{title.lstrip()} {self.graph_type}.svg'

        try:
            save_kwargs = {}
            if self.graph_type in {'heatmap', 'jointplot'}:
                save_kwargs['facecolor'] = 'auto'
            fig.savefig(os.path.join(self.path_save, png), **save_kwargs)
            fig.savefig(os.path.join(self.path_save, svg), **save_kwargs)
            dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            with open(os.path.join(self.path_save, "logs-fornma.txt"), "a+") as logs:
                logs.write(f'\n{dt} - Save {title} plot')
        except:
            print(f'Error while saving figure {title}. Check your saving path and try again.')
        return None


    def plot(self):

        conditions = [None] if self.single else list(set(self.df["Condition"]))
        times = list(set(self.df["Frame"])) if self.overtime else [None]
        sample_dfs = []
        palette = self.palette
        if self.hue is not None and not is_numeric_dtype(self.df[self.hue]):
            all_hue_categories = list(set(self.df[self.hue]))
            #categories_colors = np.random.rand(len(all_hue_categories), 3)
            categories_colors = sns.color_palette(self.palette, len(all_hue_categories))
            self.palette = dict(zip(all_hue_categories, categories_colors))
            # palette['Family: -1'] = (0.8, 0.8, 0.8)  # apagar

        for c in conditions:
            for t in times:
                title_c = '' if c is None else c
                title_t = '' if t is None else f'Frame {t}'
                title = f' {title_c} NMA plot {title_t}'

                if self.graph_type == 'heatmap':
                    fig = self.plot_NMA_heatmap((c, t), title)
                elif self.graph_type == 'jointplot':
                    fig = self.plot_NMA_jointplot((c, t), title)
                else:
                    fig, df_sample = self.plot_NMA_dot((c, t), self.hue, self.size, self.sample, title)
                    sample_dfs.append(df_sample)
                self.save_figs(fig, title)

        self.percentages.to_csv(os.path.join(self.path_save, "Categories.csv"))
        if self.sample:
            self.sample_percentages.to_csv(os.path.join(self.path_save, "Sample Categories.csv"))
            sample_df = pd.concat(sample_dfs)
            sample_df.to_csv(os.path.join(self.path_save, "Sampled Cells.csv"))

        return print(f'Files were saved at: {self.path_save}')


def add_NMA_category_to_tables(df:pd.DataFrame,
                               parameters: dict ):
    """ Given a dataframe and NMA parameters, returns an annotated dataframe with a NMA category for each cell"""
    df.loc[
        (df['Area'] >= parameters['h_y_up'][0]) &
        (df['NII'] < parameters['v_upx'][0]),
        'NMA_category'
    ] = 'LR'
    df.loc[
        (df['Area'] > parameters['h_y_up'][0]) &
        (df['NII'] >=  parameters['v_upx'][0]),
        'NMA_category'
    ] = 'LI'
    df.loc[
        (df['Area'] < parameters['h_y_up'][0]) &
        (df['Area'] >= parameters['h_y_down'][0]) &
        (df['NII'] < parameters['v_midx'][0]),
        'NMA_category'
    ] = 'N'
    df.loc[
        (df['Area'] < parameters['h_y_up'][0]) &
        (df['Area'] >= parameters['h_y_down'][0]) &
        (df['NII'] > parameters['v_midx'][0]),
        'NMA_category'
    ] = 'I'
    df.loc[
        (df['Area'] < parameters['h_y_down'][0]) &
        (df['NII'] <parameters['v_downx'][0]),
        'NMA_category'
    ] = 'SR'
    df.loc[
        (df['Area'] < parameters['h_y_down'][0]) &
        (df['NII'] >= parameters['v_downx'][0]) &
        (df['NII'] < parameters['v_downx2'][0]),
        'NMA_category'
    ] = 'S'
    df.loc[
        (df['Area'] < parameters['h_y_down'][0]) &
        (df['NII'] >= parameters['v_downx2'][0]),
        'NMA_category'
    ] = 'SI'

    return df



def check_column_names(df: pd.DataFrame,
                       name: str):
    """ Checks if DataFrame columns rare the ones expected by forNMA. If not, raises an error."""

    columns = ['Frame', 'Cell', 'X', 'Y', 'Area', 'Perimeter', 'Aspect', 'Extent', 'Roundness', 'Radius_ratio', 'NII',
               'FitEllipse_X', 'FitEllipse_Y', 'FitEllipse_a', 'FitEllipse_b', 'FitEllipse_angle', 'Condition',
               'Overtime']

    if not all(item in df.columns for item in columns):
        raise ValueError(
            f'The table {name} does not have forNMA output column names. Rename your columns according to forNMA '
            f'standard outputs and try again.')

    return None


def plot_NMA(path_list: List[str],
             saving_path: str,
             graph_type: str = 'dot',
             col1: Optional[str] = None,
             col2: Optional[str] = None,
             sample_size: Optional[int] = None,
             single: Optional[bool] = None,
             overtime: bool = False,
             palette = 'rainbow',
             hue_norm=None,
             size_norm=None
             ):

    """ From a list of paths corresponding to csv files, plots NMA graphs. Graph_tupe can be dot, jointplot or heatmap"""

    hue_norm = tuple(hue_norm) if hue_norm is not None else None
    size_norm = tuple(size_norm) if size_norm is not None else None

    if not os.path.isfile(CONFIG_PATH ):
        raise Exception("The NMA settings were not defined. Run 'NMA settings' command before plotting")

    with open(CONFIG_PATH , 'rb') as f:
        parameters = pickle.load(f)
        control_name = parameters['name']
        sd_area = parameters['sd_area']
        sd_NII = parameters['sd_NII']
        print(
            f'Your current configuration was defined with table named {control_name} with an area standard '
            f'deviation of {sd_area} and NII standard deviation of {sd_NII}.\nIf you need other settings, '
            f'please run "NMA settings" command again.')

        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(os.path.join(saving_path, "logs-fornma.txt"), "a") as logs:
            logs.write(f'\n\n{dt} - NMA plot\nYour current configuration was defined with table named '
                       f'{control_name} with an area standard deviation of {sd_area} and NII standard deviation of '
                       f'{sd_NII}.')

    print(os.path.join(saving_path, "logs-fornma.txt"))
    df_list = [pd.read_csv(f) for f in path_list]
    names = [os.path.basename(f).replace('Results.csv', '') for f in path_list]
    # [check_column_names(df, name) for df, name in zip(df_list, names)]
    for i in range(len(df_list)):
        if not df_list[i]['Condition'].iloc[0]:
            df_list['Condition'] = names[i]

    df = pd.concat(df_list, ignore_index=True) if len(df_list) > 1 else df_list[0]
    sample = True if sample_size is not None else False
    NMA(df, parameters, graph_type, single, overtime, saving_path, sample, sample_size, col1, col2, palette,
        hue_norm, size_norm)

    df_list_with_NMA = [add_NMA_category_to_tables(f, parameters) for f in df_list]
    df_names = [f['Condition'].iloc[0] for f in df_list]
    dest = os.path.join(saving_path, 'Tables with NMA annotation')
    os.makedirs(dest, exist_ok=True)
    [f.to_csv(os.path.join(dest, f'{g}.csv')) for f, g in zip(df_list_with_NMA, df_names) ]

    return print("Complete")


def plot_area_vs_feat(df, col, palette, path_save):
    sns.set_theme()

    grouped = df.groupby('Condition')
    for name, group in grouped:
        plt.figure()
        sns.boxplot(data=group, y="Area", x=col, palette='rainbow')
        plt.title(name)
        plt.savefig(f'{path_save}/{col} {name}.png')
        plt.figure()
        sns.displot(data=df, x='Area', hue=col, kind='kde', fill='true', palette='rainbow')
        plt.xlim(0, 10000)
        plt.title(name)
        plt.savefig(f'{path_save}/{col} {name} histogram.png')
    return
