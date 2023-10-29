#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 17:49:36 2022

@author: luiza
"""
import warnings
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use('TkAgg')
import pandas as pd
import cv2 as cv
import numpy as np
from typing import List, Tuple, Optional
import math
import os
from matplotlib import pyplot as plt
import seaborn as sns
from rich.progress import track

def draw_foci_ch(group: pd.DataFrame,
                 channel_list: List[str],
                 shape: Tuple[int],
                 color_list: List[Tuple[int]],
                 monocolor: bool,
                 ):
    """
        Creates an array (black image) with a given shape and draws all foci at
    the specified image. If monocolor is True, it will create a three-dimensional
    array and selects BGR colors from a given list to draw.
    After the drawing, it generates a image overlay and add it to ch_image_dict.
    """
    ch_image_dict = {}
    image_list = []
    for i in range(len(channel_list)):
        image = np.zeros((shape[0], shape[1], 3)) if not monocolor else np.zeros(shape)
        cnt_list = list(group['Foci_cnt_' + channel_list[i]])
        cnt_list = [item for sublist in cnt_list for item in sublist]
        image2 = cv.drawContours(image, cnt_list, -1, color_list[i], cv.FILLED) if not monocolor else \
            cv.drawContours(image, cnt_list, -1, (255, 255,255), cv.FILLED)
        ch_image_dict[channel_list[i]] = image2
        image_list.append(image2)

    overlay = cv.bitwise_and(image_list[0], image_list[1])

    for i in range(2, len(image_list)):
        overlay = cv.bitwise_and(overlay, image_list[i])
    ch_image_dict['overlay'] = overlay

    return ch_image_dict, image_list


def crop_image(image: np.ndarray,
               bbox_list: List[Tuple[int]]
               ) -> List[np.ndarray]:
    """
        Given a list of bounding box coordinates, crops an image in a list
    of smaller images (np arrays).
    """
    img_list = []

    for bbox in bbox_list:  # x, y , w ,h #x0, y1, w2, h3
        img = image[bbox[1] - 2:bbox[1] + bbox[3] + 4,
              bbox[0] - 2:bbox[0] + bbox[2] + 4]
        img_list.append(img)

    return img_list


def measure_pixels(ch_img_dict: dict,
                   df: pd.DataFrame,
                   ) -> pd.DataFrame:
    """
       Calls functions do draw the foci and crop images is smaller arrays to
    then count the number of white pixels (corresponding to foci) in each image
    and at the overlay image. Returns a dataframe with the measured values.
    """

    bbox_list = list(df['bbox'])
    cell_list = list(df['Cell'])
    cropped_images_dict = {}
    for key, value in ch_img_dict.items():
        cropped_list = crop_image(value, bbox_list)
        cropped_images_dict[key] = cropped_list

    pixel_count_dict = {'Cell': cell_list}
    for key, value in cropped_images_dict.items():
        pixel_count_dict['Total_pixel_' + key] = [np.count_nonzero(f) for f in value]

    df_pixel_number = pd.DataFrame(pixel_count_dict)

    return df_pixel_number


def save_images_ch(group: pd.DataFrame,
                   channel_list: List[str],
                   shape: Tuple[int],
                   color_list: List[Tuple[int]],
                   cnt_col: str,
                   path_to_save: str,
                   name: str
                   ):
    ch_image_dict_color, image_list_color = draw_foci_ch(group, channel_list, shape, color_list, False)
    overlay = image_list_color[0]
    for f in image_list_color[1:]:
        overlay = overlay + f
    cv.drawContours(overlay, list(group[cnt_col]), -1, (170, 170, 170), 2)
    images_to_save = crop_image(overlay, list(group['bbox']))
    direc = os.path.join(path_to_save, 'Overlay Images')
    os.makedirs(direc, exist_ok=True)
    image_names = [os.path.join(direc, name + ' - Cell ' + str(f) + '.png') for f in list(group['Cell'])]
    if len(images_to_save) > 1:
        save = [cv.imwrite(f, j) for f, j in zip(image_names, images_to_save) if j.size != 0]

    return


def foci_overlay(dfs: List[pd.DataFrame],
                 df_names: List[str],
                 save_images: bool,
                 path_save: str,
                 ):
    channel_list = [f.replace('Image_name_', '') for f in dfs[0].columns if 'Image_name_' in f]
    color_list = [(0, 0, 255), (255, 0, 0), (0, 255, 0), (0, 128, 255),
                  (0, 255, 255), (255, 255, 0), (255, 0, 255), (127, 0, 255),
                  (128, 128, 0), (0, 128, 128), (128, 0, 128)]
    color_list = color_list * int(math.ceil(len(channel_list) / len(color_list)))

    cnt_col = [f for f in dfs[0].columns if 'Nuc_cnt' in f][0]
    shape = dfs[0]['Image_' + channel_list[0]].iloc[0].shape

    all_pixel_count_dfs = []
    for name, df in zip(df_names, dfs):
        df['bbox'] = df.apply(lambda x: cv.boundingRect(x[cnt_col]), axis=1)
        df.reset_index(inplace=True)
        ch_image_dict, image_list = draw_foci_ch(df, channel_list, shape, color_list, True)
        df_pixel_count = measure_pixels(ch_image_dict, df)
        df_pixel_count['Image'] = name
        all_pixel_count_dfs.append(df_pixel_count)
        save_images_ch(df, channel_list, shape, color_list, cnt_col, path_save, name) if save_images else None
    final_df = pd.concat(all_pixel_count_dfs)
    final_df.to_csv(os.path.join(path_save, 'Overlay Pixel Counts.csv'))
    return


def test_channel_list(df: pd.DataFrame,
                      channel_list: List[str],
                      channels_on_df: List[str],
                      ):
    """ Tests if the channel names given by users are correct and present on dataframe columns. Returns False if
    the columns given by user are wrong, and true if they are correct"""
    test_channel_names = [f for f in df.columns if f.replace('Image_name_', '') in channel_list]
    if len(channels_on_df) <= 1:
        raise Exception('There are not enough channels in your data to perform foci overlay. Did you mean frame'
                        'overlay instead?')
    elif len(channel_list) <= 1:
        print(f'You did not provide enough channels for channel foci overlay. The foci overlay will be performed in '
              f'the following channels:  {", ".join(channels_on_df)}.')
        return False

    elif len(test_channel_names) == 0:
        print(f'The channels {", ".join(channel_list)} were not found. Foci overlay will be performed on '
              f'channels {", ".join(channels_on_df)}.')
        return False
    else:
        return True


def overlapping_foci(pkl_results_folder_path: str,
                     path_to_save: str,
                     channel_list: Optional[List[str]] = None,
                     ):

    if not os.path.exists(pkl_results_folder_path):
        raise FileNotFoundError(f'The path "{pkl_results_folder_path}" does not exist. Did you type it right?')
    if not os.path.exists(path_to_save):
        raise FileNotFoundError(f'The path "{path_to_save}" does not exist. Did you type it right?')

    paths_to_dfs = [os.path.join(pkl_results_folder_path, f) for f in os.listdir(pkl_results_folder_path)]
    dfs = [pd.read_pickle(f) for f in paths_to_dfs if f.endswith('.pkl')]
    df_names = [f.replace('.pkl', '') for f in os.listdir(pkl_results_folder_path)]
    channels_on_df = [f.replace('Image_name_', '') for f in dfs[0].columns if 'Image_name_' in f]

    if channel_list is not None:
        # If user passes a list of channels, tests it if channels exist
        # if they exist: uses channels given by user
        # Else: use channels that are already on the give dataframes
        channels = channel_list if test_channel_list(dfs[0], channel_list, channels_on_df) else channels_on_df
    else:
        channels = channels_on_df

    channels_to_remove = [f for f in channels_on_df if f not in channels]
    cols_to_remove = []
    for ch in channels_to_remove:
        ctr = [f for f in dfs[0].columns if ch in f]
        cols_to_remove.extend(ctr)

    for col in cols_to_remove:
        [f.drop(col, axis=1, inplace=True) for f in dfs]

    foci_overlay(dfs, df_names, True, path_to_save)

    return print('complete!')


def get_nuc_profile(channels, shape, df, i):
    y_dict = {}
    x_dict = {}
    for ch in channels:
        image = np.zeros(shape)
        image2 = cv.drawContours(image, [df['Nuc_cnt_' + ch].iloc[i]], -1, (1, 1, 1), cv.FILLED)
        masked = np.ma.masked_where(image2 < 1, df['Image_' + ch].iloc[i])

        mean_y = masked.mean(axis=0)
        mean_y = mean_y[~mean_y.mask]
        y_dict[ch] = mean_y

        mean_x = masked.mean(axis=1)
        mean_x = mean_x[~mean_x.mask]
        x_dict[ch] = mean_x

    x_profile = pd.DataFrame(x_dict)
    y_profile = pd.DataFrame(y_dict)

    return x_profile, y_profile


def plot_and_save_profile(x_df: List[pd.DataFrame],
                          y_df: List[pd.DataFrame],
                          name: str,
                          path_save: str,
                          list_number: int):

    x_df = [f.reset_index(drop=True) for f in x_df]
    y_df = [f.reset_index(drop=True) for f in y_df]
    sns.set_theme()
    sns.set_palette('Set2')
    fig, axs = plt.subplots(8, 8, figsize=(24, 20))

    idx = 0
    # Iterates over subplots adding pair graphs
    for i in range(8):
        for j in range(8):
            if idx == len(x_df): # no more graphs to plot
                break
            if i % 2 == 0:
                ax = axs[j, i]

                # First Graph (x profile)
                nuc = x_df[idx]['nuc'].iloc[0]
                sns.lineplot(data=x_df[idx].drop(columns=['nuc']), ax=ax)
                ax.set_title(f'X profile of nucleus {nuc}')
                ax.set(xticklabels=[])  # remove the tick labels
                ax.tick_params(bottom=False)  # remove the ticks
                ax.set(yticklabels=[])  # remove the tick labels
                ax.tick_params(left=False)  # remove the ticks
                plt.setp(ax.get_legend().get_texts(), fontsize='8')  # for legend text

                # Second Graph (y profile)
                ax2 = axs[j, i + 1]
                sns.lineplot(data=y_df[idx].drop(columns=['nuc']), ax=ax2)
                ax2.set_title(f'Y profile of nucleus {nuc}')
                ax2.set(xticklabels=[])  # remove the tick labels
                ax2.tick_params(bottom=False)  # remove the ticks
                ax2.set(yticklabels=[])  # remove the tick labels
                ax2.tick_params(left=False)  # remove the ticks

                ax.legend_.remove()
                ax2.legend_.remove()

                idx += 1
    if idx == len(x_df):  # no more graphs to plot
        for i in range(8):
            for j in range(8):
                ax = axs[j, i]
                ax.set(xticklabels=[])  # remove the tick labels
                ax.tick_params(bottom=False)  # remove the ticks
                ax.set(yticklabels=[])  # remove the tick labels
                ax.tick_params(left=False)  # remove the ticks


    # New axis for legend
    legend_ax = fig.add_axes([0.92, .35, .075, 0.2])
    legend_ax.set(xticklabels=[])  # remove the tick labels
    legend_ax.tick_params(bottom=False)  # remove the ticks
    legend_ax.set(yticklabels=[])  # remove the tick labels
    legend_ax.tick_params(left=False)  # remove the ticks
    legend_ax.grid(False)
    handles, labels = axs[0,0].get_legend_handles_labels()
    legend_ax.legend(handles, labels, loc='center', frameon=False)

    plt.suptitle(f'X and Y intensity profiles of {name}')
    plt.tight_layout(rect=[0, 0, .92, 0.98])

    # save
    plt.savefig(os.path.join(path_save, 'Profile-plots', f'{name} {list_number}.png'))
    plt.savefig(os.path.join(path_save, 'Profile-plots', f'{name} {list_number}.svg'))
    plt.close(fig)

    return


def plot_profile(path_pickle_data: str,
                 path_save: str,
                 columns: List[str] = None,
                 ):
    """
    From a folder that contains pickle files, plots the profile of all nucleus intensity in all channels.
     The x  profile is given by mean of y pixels in the x axis and the y profile is the mean of x pixels in the y axis.
     """

    paths = [os.path.join(path_pickle_data, f) for f in os.listdir(path_pickle_data)]
    dfs = [pd.read_pickle(f) for f in paths]
    names = [f.replace('.pkl', '')for f in os.listdir(path_pickle_data)]

    if columns is None:
        channel_list = [f.replace('Image_name_', '') for f in dfs[0].columns if 'Image_name' in f]
    else:
        channel_list = columns
    print(columns, dfs[0].columns, channel_list)
    print('Image_' + channel_list[0])
    shape = dfs[0]['Image_' + channel_list[0]].iloc[0].shape
    os.makedirs(os.path.join(path_save, 'Profile-plots'), exist_ok=True)

    for name, df in track(zip(names, dfs), description=f'This might take a while...'):
        x_df_list = []
        y_df_list = []
        for i in range(df.shape[0]):
            x_nuc_df, y_nuc_df = get_nuc_profile(channel_list, shape, df, i)
            x_nuc_df['nuc'] = df['Cell'].iloc[i]
            y_nuc_df['nuc'] = df['Cell'].iloc[i]
            x_df_list.append(x_nuc_df)
            y_df_list.append(y_nuc_df)
        splitted_x_df_list = [x_df_list[f:f + 32] for f in range(0, len(x_df_list), 32)]
        splitted_y_df_list = [y_df_list[f:f + 32] for f in range(0, len(y_df_list), 32)]

        for sublist in range(len(splitted_y_df_list)):
            plot_and_save_profile(splitted_x_df_list[sublist], splitted_y_df_list[sublist], name, path_save, sublist)

    return

#plot_profile('/media/luiza/DATA/Doutorado/Nicolas/RPE ETOPO/2023/novas analises/5.Pkl individuais/pkl',
#                 '/media/luiza/DATA/Doutorado/Nicolas/RPE ETOPO/2023/novas analises/6. Foci overlay',
#                 ['53BP1', 'gH2AX'])
