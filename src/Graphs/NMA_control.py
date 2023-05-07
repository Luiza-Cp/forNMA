"""
Created on Tue Aug  9 09:47:14 2022

@author: luiza
"""

import os
from math import pi
from typing import Optional, List, Tuple
import pickle
import matplotlib.patches as mp
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.widgets import Slider
import matplotlib
matplotlib.use('TkAgg')
# as infos disso estção anotadas no caderno, conferir ali
from scipy import stats
from .NMA_draggable_line import draggable_lines


class NMA:
    """ Class for NMA graph plotting"""

    def __init__(self, df, sd_area, sd_NII, headless):
        """
        Atributes:

        self.df: pandas DataFrame with all value information
        self.sd_area: float representing the number of standard deviations from the mean to use for NMA area threshold
        self.sd_NII: float representing the number of standard deviations from the mean to use for NMA NII threshold
        self.headless: boolean indicating if execution muts use GUI or not. If True does not use it.
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
        """
        self.df = df
        self.sd_area = sd_area
        self.sd_NII = sd_NII
        self.headless = headless
        self.mean_NII, self.mean_a, self.std_NII, self.std_a, self.circle = self.calc_threshold_NMA()
        self.graph_limits = self.calc_area_NII_lims()
        self.ellipse = self.get_ellipse()
        self.adjust_ellipse() if self.headless is False else None
        self.h_x, self.h_y_up, self.h_y_down = self.calc_lines()
        self.graph_box = dict(boxstyle="round,pad=0.3", fc="#dedcdc", alpha=0.7, ec="#bdbbbb", lw=1)
        self.v_upx, self.v_upy, self.v_midx, self.v_midy, self.v_downx, self.v_downy, self.v_downx2 = self.get_vertical_lines()
        self.v_upx, self.v_midx, self.v_downx, self.v_downx2 = self.adjust_vertical_lines() if self.headless is False else None

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

    def calc_threshold_NMA(self):
        """
          Gets the control group from self.control_df and returns the values for
        NMA threshold - area mean and standard deviation and NII mean and standard
        deviation removig 2 z-score outliers - and the linespace for ellipse.
          If overtime, it will use all time frames for control gorup.
        """

        df = self.df
        df = df.loc[(np.abs(stats.zscore(df["Area"])) < 2)]  # removes 2 z-scores
        df = df.loc[(np.abs(stats.zscore(df["NII"])) < 2)]
        mean_NII = df['NII'].mean()
        mean_a = df["Area"].mean()
        std_NII = df['NII'].std()
        std_a = df["Area"].std()

        circle = np.linspace(0, 2 * pi, 100)

        return mean_NII, mean_a, std_NII, std_a, circle

    def calc_lines(self):
        """
        Given mean and standard deviation values, it returns lines coordinates
        self.sd: number of standard deviations from mean that user has to provide
        for thresholding.
        """

        rx = self.sd_NII * self.std_NII  # number of stantadard deviations * standard deviation
        ry = self.sd_area * self.std_a
        horizontal_x = [self.mean_NII - rx, self.mean_NII + 3 * rx]
        horizontal_y_up = [self.mean_a + ry, self.mean_a + ry]
        horizontal_y_down = [self.mean_a - ry, self.mean_a - ry]

        return horizontal_x, horizontal_y_up, horizontal_y_down

    def calc_area_NII_lims(self):

        """ Given a dataframe, establishes NMA graph limits"""

        df = self.df[(np.abs(stats.zscore(self.df["Area"])) < 3)]
        df = df[(np.abs(stats.zscore(df["NII"])) < 3)]
        max_a = df['Area'].max()
        min_a = df['Area'].min() - df['Area'].min() / 3
        max_NII = df['NII'].max()
        min_NII = df['NII'].min() - df['NII'].min() / 3

        return min_a, max_a, min_NII, max_NII

    def get_ellipse(self):
        ellipse = mp.Ellipse((self.mean_NII, self.mean_a),
                             2 * self.sd_NII * self.std_NII,
                             2 * self.sd_area * self.std_a,
                             ec='black', fc=None, fill=False)
        return ellipse

    def adjust_ellipse(self):
        """
        Plots a control sample of 500 units (or all control if smaller) with the
        calculated ellipse for user adjustments.
        """

        df = self.df
        df = df.loc[(np.abs(stats.zscore(df["Area"])) < 3)]  # removes 3 z-scores
        df = df.loc[(np.abs(stats.zscore(df["NII"])) < 3)]

        sns.set_theme()
        sns.set_palette('rainbow', 9)
        df_sample, boolean = self.get_sample(df, None, None)

        while not boolean:  # if any of variances is not preserved, repeat
            df_sample, boolean = self.get_sample(df, None, None)

        fig, ax = plt.subplots()
        sns.scatterplot(data=df_sample, x="NII", y="Area", ax=ax)

        ellipse = self.ellipse
        ax.add_patch(ellipse)
        ax.set_title('Adjust here the threshold ellipse.\nClose the window when you are done.')
        plt.subplots_adjust(left=0.25, bottom=0.25)

        axsv = plt.axes([0.1, 0.25, 0.0225, 0.63])
        axsv_slider = Slider(
            ax=axsv,
            label="Area SD",
            valmin=0,
            valmax=5,
            valinit=self.sd_area,
            orientation="vertical"
        )

        axsh = plt.axes([0.25, 0.1, 0.63, 0.0225])
        axsh_slider = Slider(
            ax=axsh,
            label="NII SD",
            valmin=0,
            valmax=5,
            valinit=self.sd_NII,
            orientation="horizontal"
        )

        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])

        def update(val):
            self.sd_area = axsv_slider.val
            self.sd_NII = axsh_slider.val
            ellipse.set_height(2 * self.sd_area * self.std_a)
            ellipse.set_width(2 * self.sd_NII * self.std_NII)
            fig.canvas.draw_idle()

        axsv_slider.on_changed(update)
        axsh_slider.on_changed(update)
        plt.show(block=True)

        return None

    def get_vertical_lines(self):
        """ Calculates vertical lines based on self.sd values"""

        upper_line_x = self.mean_NII + 1.5 * self.sd_NII * self.std_NII
        # Vertical Upper line X coordinates:
        v_upx = [upper_line_x, upper_line_x]

        # Vertical Upper line Y coordinates:
        v_upy = [int(self.mean_a + self.sd_area * self.std_a), int(self.mean_a + (2 + self.sd_area) * self.std_a)]

        # Vertical MIDdle line X coordinates:
        v_midx = v_upx

        # Vertical MIDdle line Y coordinates:
        v_midy = [int(self.mean_a - self.sd_area * self.std_a), v_upy[0]]

        # Vertical BOTTOM line 1 X coordinates:
        v_downx = [self.mean_NII, self.mean_NII]

        # Vertical BOTTOM line 2 X coordinates:
        v_downx2 = v_upx

        # Vertical BOTTOM lines Y coordinates (both bottom lines):
        v_downy = [int(self.mean_a - (1 + self.sd_area) * self.std_a), v_midy[0]]

        return v_upx, v_upy, v_midx, v_midy, v_downx, v_downy, v_downx2

    def adjust_vertical_lines(self):
        """
        Plots the control df with ellipse and horizontal lines for user to adjust the NMA threshold.
        Returns the new values.
        """

        sns.set_theme()
        sns.set_palette('rainbow', 9)
        fig = plt.figure()
        df_sample, boolean = self.get_sample(self.df, None, None)
        while not boolean:
            df_sample, boolean = self.get_sample(self.df, None, None)

        ax = fig.add_subplot(sns.scatterplot(data=df_sample, x="NII", y="Area", ))

        ax.plot(self.h_x, self.h_y_up, self.h_x, self.h_y_down, color='black')
        ax.plot(self.mean_NII + (self.sd_NII * self.std_NII) * np.cos(self.circle),
                self.mean_a + (self.sd_area * self.std_a) * np.sin(self.circle), color='black')
        ax.set_title('Click to move the blue lines and click again to release.\nClose the window when you are done.')

        # ax.text(x, y, text, size, bbox)
        ax.text(self.v_upx[0] - 1, self.h_y_up[0] + 0.1 * self.sd_area * self.mean_a, 'LR',
                size=10, bbox=self.graph_box)
        ax.text(self.v_upx[0] + 1, self.h_y_up[0] + 0.1 * self.sd_area * self.mean_a, 'LI',
                size=10, bbox=self.graph_box)
        ax.text(self.mean_NII, self.mean_a, 'N', size=10, bbox=self.graph_box)
        ax.text(self.v_midx[0] + 1, self.mean_a, 'I', size=10, bbox=self.graph_box)
        ax.text(self.v_downx[0] - 0.5, self.h_y_down[0] - 0.1 * self.sd_area * self.mean_a,
                'SR', size=10, bbox=self.graph_box)
        mid_point = self.v_downx[0] + (self.v_downx2[0] - self.v_downx[0])/2
        ax.text(mid_point, self.h_y_down[0] - 0.1 * self.sd_area * self.mean_a, 'S',
                size=10, bbox=self.graph_box)
        ax.text(self.v_downx2[0] + 0.5, self.h_y_down[0] - 0.1 * self.sd_area * self.mean_a,
                'SI', size=10, bbox=self.graph_box)

        ax.set_ylim(self.graph_limits[0], self.graph_limits[1])
        ax.set_xlim(self.graph_limits[2], self.graph_limits[3])

        upper_line = draggable_lines(ax, 'v', self.v_upx[0], self.v_upy)
        middle_line = draggable_lines(ax, 'v', self.v_midx[0], self.v_midy)
        bottom_line = draggable_lines(ax, 'v', self.v_downx[0], self.v_downy)
        bottom_line2 = draggable_lines(ax, 'v', self.v_downx2[0], self.v_downy)

        plt.show(block=True)

        v_upx = [upper_line.x, upper_line.x]
        v_midx = [middle_line.x, middle_line.x]
        v_downx = [bottom_line.x, bottom_line.x]
        v_downx2 = [bottom_line2.x, bottom_line2.x]

        plt.close('all')

        return v_upx, v_midx, v_downx, v_downx2

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
        Finds statistcally significant samples from a population based on Area,
        NII and other specified column values.
        """

        if df.shape[0] < n:
            return df, True

        df_sample = df.sample(n=n)
        p_NII_var = self.f_test(df['NII'].values, df_sample['NII'].values)
        p_a_var = self.f_test(df['Area'].values, df_sample['Area'].values)

        p_NII_mean = stats.ttest_ind(df['NII'].values, df_sample['NII'].values)[1]
        p_a_mean = stats.ttest_ind(df['Area'].values, df_sample['Area'].values)[1]

        if hue != None:
            p_hue_var = self.f_test(df[hue].values, df_sample[hue].values)
            p_hue_mean = stats.ttest_ind(df[hue].values, df_sample[hue].values)[1]
        if size != None:
            p_size_var = self.f_test(df[size].values, df_sample[size].values)
            p_size_mean = stats.ttest_ind(df[size].values, df_sample[size].values)[1]
        if hue == None and size == None:
            p_hue_var = None
            p_hue_mean = None
            p_size_var = None
            p_size_mean = None

        p_values = [p_NII_var, p_NII_mean, p_a_var, p_a_mean, p_hue_var, p_hue_mean, p_size_var, p_size_mean]
        p_values = [f for f in p_values if f is not None]

        if np.any(np.array(p_values) < 0.05):
            boolean = False
        else:
            boolean = True

        return df_sample, boolean


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


def NMA_control(path: str,
                sd_area: Optional[float] = 2.0,
                sd_nii: Optional[float] = 2.0,
                headless: bool = False):
    """Create NMA settings for further plot"""
    df = pd.read_csv(path)
    name = os.path.basename(path)
    check_column_names(df, name)
    nma = NMA(df, sd_area, sd_nii, headless)

    nma_parameters = {"name": name,
                      "sd_area": nma.sd_area,
                      "sd_NII": nma.sd_NII,
                      "mean_NII": nma.mean_NII,
                      "std_NII": nma.std_NII,
                      "mean_a": nma.mean_a,
                      "std_a": nma.std_a,
                      "circle": nma.circle,
                      "graph_limits": nma.graph_limits,
                      "ellipse": nma.ellipse,
                      "h_x": nma.h_x,
                      "h_y_up": nma.h_y_up,
                      "h_y_down": nma.h_y_down,
                      "graph_box": nma.graph_box,
                      "v_upx": nma.v_upx,
                      "v_upy": nma.v_upy,
                      "v_midx": nma.v_midx,
                      "v_midy": nma.v_midy,
                      "v_downx": nma.v_downx,
                      "v_downy": nma.v_downy,
                      "v_downx2": nma.v_downx2
                      }

    with open('control_parameters.pickle', 'wb') as handle:
        pickle.dump(nma_parameters, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return print("NMA control setting complete")


#NMA_control('/media/luiza/DATA/Doutorado/Dani/results/24h/lap_lnc_tras1 Results.csv')
