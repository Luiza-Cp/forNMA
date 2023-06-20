#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 17:49:36 2022

@author: luiza
"""

import pandas as pd
import cv2 as cv
import numpy as np
from typing import List, Tuple, Optional
import math
import os
from matplotlib import pyplot as plt
import seaborn as sns


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
        image = np.zeros((shape[0], shape[1], 3)) if monocolor == False else np.zeros(shape)
        cnt_list = list(group['Foci_cnt_' + channel_list[i]])
        cnt_list = [item for sublist in cnt_list for item in sublist]
        image2 = cv.drawContours(image, cnt_list, -1, color_list[i], cv.FILLED) if monocolor == False else \
            cv.drawContours(image, cnt_list, -1, (255, 255, 255), cv.FILLED)
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
                   frame: str):
    ch_image_dict_color, image_list_color = draw_foci_ch(group, channel_list,
                                                         shape, color_list, False)
    overlay = image_list_color[0]
    for f in image_list_color[1:]:
        overlay = overlay + f
    cv.drawContours(overlay, list(group[cnt_col]), -1, (170, 170, 170), 2)
    images_to_save = crop_image(overlay, list(group['bbox']))
    direc = os.path.join(path_to_save, 'Overlay Images', 'Frame ' + str(frame))
    os.makedirs(direc)
    image_names = [os.path.join(direc, 'Cell ' + str(f) + '.png') for f in list(group['Cell'])]
    if len(images_to_save) > 1:
        save = [cv.imwrite(f, j) for f, j in zip(image_names, images_to_save) if j.size != 0]

    return


def foci_overlay(contour_df: pd.DataFrame,  # vem do pkl
                 save_images: bool,
                 path_save: str,
                 channel_list: List[str],
                 ):
    contour_df.reset_index(inplace=True)

    color_list = [(0, 0, 255), (255, 0, 0), (0, 255, 0), (0, 128, 255),
                  (0, 255, 255), (255, 255, 0), (255, 0, 255), (127, 0, 255),
                  (128, 128, 0), (0, 128, 128), (128, 0, 128)]

    color_list = color_list * int(math.ceil(len(channel_list) / len(color_list)))

    cnt_col = [f for f in contour_df.columns if 'Nuc_cnt' in f][0]
    col = [f for f in contour_df.columns if 'Image' in f][0]
    shape = contour_df[col].loc[0].shape
    contour_df['bbox'] = contour_df.apply(lambda x: cv.boundingRect(x[cnt_col]), axis=1)

    groupped_contour_df = contour_df.groupby('Frame') # isso e o equivalente de um pickle

    all_pixel_count_dfs = []
    for name, group in groupped_contour_df:
        ch_image_dict, image_list = draw_foci_ch(group, channel_list, shape, color_list, True)
        df_pixel_count = measure_pixels(ch_image_dict, group)
        df_pixel_count['Frame'] = name
        all_pixel_count_dfs.append(df_pixel_count)
        if save_images == True:
            save_images_ch(group, channel_list, shape, color_list, cnt_col,
                           path_save, name)
    final_df = pd.concat(all_pixel_count_dfs)
    final_df.to_csv(os.path.join(path_save, 'Pixel Counts.csv'))
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
                     channel: bool = True,
                     channel_list: Optional[List[str]] = None,
                     ):
    if not os.path.exists(pkl_results_folder_path):
        raise FileNotFoundError(f'The path "{pkl_results_folder_path}" does not exist. Did you type it right?')
    if not os.path.exists(path_to_save):
        raise FileNotFoundError(f'The path "{path_to_save}" does not exist. Did you type it right?')

    paths_to_dfs = [os.path.join(pkl_results_folder_path, f) for f in os.listdir(pkl_results_folder_path)]
    dfs = [pd.read_pickle(f) for f in paths_to_dfs if f.endswith('.pkl')]
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

    index_of_frames_to_keep = []

    dfs = [dfs[f] for f in index_of_frames_to_keep]
    for col in cols_to_remove:
        [f.drop(col, axis=1, inplace=True) for f in dfs]

    return





def plot_proflie(frame: int,
                 nuc: int,
                 df: pd.DataFrame):
    """
         From a specific nucleus chosen by user (tuple frame_nuc specifies
     the nucleus) it plots the profile of intensity in all channels.
     The x  profile is given by mean of y pixels in an x line and the
     y profile is the mean of x pixels in an y axis.
     """
    df_nuc = df.loc[(df['Frame'] == frame) & (df['Cell'] == nuc)]
    channels = [f.replace('Image_name_', '') for f in df.columns if 'Image_name' in f]
    shape = df_nuc['Image_' + channels[0]].iloc[0].shape

    y_dict = {}
    x_dict = {}
    for ch in channels:
        image = np.zeros(shape)
        image2 = cv.drawContours(image, [df['Nuc_cnt_' + ch].iloc[0]], -1, (1, 1, 1), cv.FILLED)
        masked = np.ma.masked_where(image2 < 1, df['Image_' + ch].iloc[0])
        mean_y = masked.mean(axis=0)
        mean_y = mean_y[~mean_y.mask]
        y_dict[ch] = mean_y

        mean_x = masked.mean(axis=1)
        mean_x = mean_x[~mean_x.mask]
        x_dict[ch] = mean_x

    x_profile = pd.DataFrame(x_dict)
    y_profile = pd.DataFrame(y_dict)

    sns.set_theme()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    sns.lineplot(data=x_profile, ax=ax1)
    ax1.set_title('X profile')
    sns.lineplot(data=y_profile, ax=ax2)
    ax2.set_title('Y profile')

    return


# 1. Check if frames exist and blah
# 2. find all dfs to the specified frames
# drop othreh frames form list

# the overlap will get a list of df and if is to use frame or channel. The function must operat by itself


#### COMO CHAMAR

path = '/media/luiza/DATA/Doutorado/Nicolas/RPE ETOPO/imagens/forNMA results/results 11/Results.pkl'
contour_df = pd.read_pickle(path)
contour_df2 = contour_df.loc[contour_df['origin_folder'] == 'RPE WT ETOPOSIDE .zip']

foci_overlay(contour_df2, True,
             '/media/luiza/DATA/Doutorado/Nicolas/RPE ETOPO/imagens/forNMA results/results 11/overlapping',
             ['53BP1', 'gH2AX'])

# o overlay é de dois canais
# o overlay pode ser de um memsmo canal em dois temos diferentes? Talvez
