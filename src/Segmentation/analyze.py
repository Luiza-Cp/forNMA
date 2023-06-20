# -*- coding: utf-8 -*-
"""
Created on Sun May 16 20:11:52 2021

@author: Luiza
"""
import numpy as np
import os
import pandas as pd
from typing import List, Optional, Union
import cv2 as cv
from PySide6.QtCore import Signal

from pandas import DataFrame
from rich.progress import track

from .measure.Morphology import Morphology
from .measure.Cell import Cell
from .segmentation.find_contours import fornma_contour_finding, load_image
from .segmentation.cellpose_integration import run_cellpose
from src.Segmentation.df_managing.organize import filter_dataframe, get_foci_df, split_dfs

pd.options.mode.chained_assignment = None  # default='warn'


def measure_image(
        path_image: str,
        dict_param: dict,
        ref: np.ndarray,
        contour_list: List[np.ndarray],
        mag: int,
        ps: float,
        channel_name: str
) -> pd.DataFrame:
    """
    Loads an image - given by its path - using parameters present in dict_param.
    Uses the ref as reference for matching histograms during load.
    Creates Cell objects  based on parameters present at dict_param and returns 
    a dataframe with its measurements.
    """

    dp = dict_param
    name = os.path.basename(path_image)
    img_to_measure = load_image(path_image, rescale_intensity=dp['rescale_intensity'],
                                remove_bg=dp['remove_bg'], radius_bg=dp['radius_bg'],
                                ref=ref)
    cell_df_list = []
    for i in range(len(contour_list)):
        cell_obj = Cell(i + 1, contour_list[i], mag, ps, img_to_measure, name,
                        channel_name, dp['wants_ktr'], dp['ring_size'],
                        dp['wants_foci'], dp['foci_min_size'],
                        dp['foci_max_size'], dp['foci_min_int'],
                        dp['foci_max_int'], dp['foci_proeminence'],
                        dp['use_ellipse'])
        cell_df_list.append(cell_obj.df)

    return cell_df_list, img_to_measure, name


def perform_measure(contours: np.ndarray,
                    img_n: int,
                    subfolder_dict: dict,
                    ref_dict: dict,
                    segment_dict: dict
                    ):
    """ 
        Applies functions needed for cell morphometry and intesity measures
    Returns a dataframe with all image information.
    """
    df_morpho_list = []
    for n in range(len(contours)):
        morpho = Morphology(n + 1, contours[n], segment_dict['use_cellpose'])
        df_morpho_list.append(morpho.df)
    image_df = pd.concat(df_morpho_list)

    for key, value in subfolder_dict.items():
        df_ch_list, im, im_name = measure_image(value[0][img_n], value[1],
                                                ref_dict[key], contours, segment_dict['magnification'],
                                                segment_dict['pixel_size'], key)

        df_ch = pd.concat(df_ch_list)
        image_df = pd.merge(image_df, df_ch, on='Cell')
        image_df["Frame"] = img_n

    return image_df


def drop_cols(
        complete_df: pd.DataFrame,
        subfolder_dict: dict
) -> pd.DataFrame:
    """ Drops columns that store values not required by user."""

    for key, value in subfolder_dict.items():
        if not value[1]['wants_foci']:
            drop_foci = ["Total_foci_" + key, "Total_foci_area_" + key,
                         "Total_foci_mean_" + key, "Foci_area_fraction_" + key,
                         "Foci_cnt_" + key]
            complete_df.drop(columns=drop_foci, inplace=True)

        if not value[1]['wants_ktr']:
            drop_ktr = ["Mean_ring_" + key, "Median_ring_" + key, "Mean_ellipse_" + key,
                        "Median_ellipse_" + key, "Mean_Ring/Nucleus_" + key, "Median_Ring/Nucleus_" + key,
                        "Mean_Nucleus/Ring_" + key, "Median_Nucleus/Ring_" + key,
                        "Mean_Ellipse/Nucleus_" + key, "Median_Ellipse/Nucleus_" + key,
                        "Mean_Nucleus/Ellipse_" + key, "Median_Nucleus/Ellipse_" + key,
                        "Cyto_ring_cnt_" + key]

            complete_df.drop(columns=(drop_ktr), inplace=True)

    return complete_df


def save_dfs(df_results: pd.DataFrame,
             path_save: str,
             df_draw: Optional[pd.DataFrame]):
    """ Saves dataframes"""
    tables = list(set(df_results['origin_folder']))

    for t in tables:
        df_foci, df_results = get_foci_df(df_results)
        df_save = df_results[df_results["origin_folder"] == t]
        df_save = df_save.reindex(columns=(['Frame'] + list([a for a in df_save.columns if a != 'Frame'])))
        df_save.drop(columns=(["origin_folder"]), inplace=True)
        cols = [f for f in df_save.columns if 'foci_df' not in f]
        df_save = df_save[cols]
        os.makedirs(os.path.join(path_save, t), exist_ok=True)
        image_name = os.path.splitext(df_results[[f for f in df_results.columns if f.startswith('Image_name')][0]].iloc[0])[0]
        if not os.path.exists(os.path.join(path_save, t, f'Results.csv')):
            df_save.to_csv(os.path.join(path_save, t, f'Results.csv'))
        else:
            df_save.to_csv(os.path.join(path_save, t, f'Results.csv'), mode='a', header=None)

        if df_draw is not None:
            path_pkl = os.path.join(path_save, t, 'pkl-data')
            os.makedirs(path_pkl, exist_ok=True)
            df_draw.to_pickle(os.path.join(path_pkl, f' {image_name} results.pkl'))

        if df_foci is not None:
            if not os.path.exists(os.path.join(path_save, t, f'Foci Results.csv')):
                df_foci.to_csv(os.path.join(path_save, t, f'Foci Results.csv'))
            else:
                df_foci.to_csv(os.path.join(path_save, t, f'Foci Results.csv'), mode='a', header=None)
    return None  # print("files saved")


def draw_and_save(df: pd.DataFrame,
                  ch: str,
                  saving_dir: str,
                  use_cellpose: bool
                  ):
    """
    Loop though a dataframe based on its channels and draws contours at the
    specified images and then saves them.
    """

    cols_to_draw = [f for f in list(df.columns) if ch in f
                    and 'Y_draw' not in f and 'Image_' not in f]

    df = df.filter(regex=ch + "|Cell|X")
    cnt_grouped = df.groupby(['Image_name_' + ch])
    fs = cv.getFontScaleFromHeight(2, 15, 2)
    for name, group in cnt_grouped:
        img = group['Image_' + ch].iloc[0]
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
        cnt_nuc = list(group['Nuc_cnt_' + ch])
        img = cv.drawContours(img, cnt_nuc, -1, (98, 59, 132), 1)
        for i in range(len(group['Cell'])):
            img = cv.putText(img, str(int(group['Cell'].iloc[i])),
                             ((group['X'] + 5).iloc[i], group['Y_draw_' + ch].iloc[i]),
                             2, fs, (122, 144, 248), 1)

        for col in cols_to_draw:
            if 'Foci' in col:
                foci_cnt = list(group['Foci_cnt_' + ch])
                foci_cnt = [i for f in foci_cnt for i in f if len(f) > 0]
                img = cv.drawContours(img, foci_cnt, -1, (122, 144, 248), 1)

            else:
                cnt = list(group[col])
                cnt = [f[0] for f in cnt if len(f) > 0] if use_cellpose or 'Cyto' in col else cnt
                img = cv.drawContours(img, cnt, -1, (122, 144, 248), 1)

        cv.imwrite(os.path.join(saving_dir, name), img)

    return None


def saving_images(df_draw: pd.DataFrame,
                  path_to_save: str,
                  ch_name_list: List[str],
                  use_cellpose: bool
                  ):
    """
   Splits dataframe according to their folders, creates directories
   for saving and pass values to draw_and_save, that draws contours and saves
   images.
   """
    dirs = list(set(df_draw.origin_folder.values))
    #    iterates over each folder in the dataframe
    for d in dirs:
        df_dir = df_draw[df_draw["origin_folder"] == d]
        saving_dir = os.path.join(path_to_save, d)
        os.makedirs(saving_dir, exist_ok=True)
        #    iterates over each image channel inside the folder
        for ch in ch_name_list:
            saving_dir_ch = os.path.join(saving_dir, ch)
            os.makedirs(saving_dir_ch, exist_ok=True)
            draw_and_save(df_dir, ch, saving_dir_ch, use_cellpose)
    return None


def analyze_dict(
        subfolder_dict: dict,  # dict of every channel
        segment_dict: dict,  # dict of global parameters
        is_overtime: bool,
        condition: Optional[str],
        preview: bool,
        ch_name_list: List[str],
        path_to_save: str,
        wants_to_save: bool,
        subfolder_images_in: str,

) -> Union[bool, DataFrame]:
    """
    Given a dictionary containing information about each image channel analysis  and the parameters used to perform cell
     segmentation, returns a dataframe containing the measurements and contours of each cell in every channel.
    This function is responsible for organizing all measuring functions.
    """
    ref_dict = {}  # reference images for matching histograms
    for key, value in subfolder_dict.items():
        if value[2]:
            ch_segment = key
        ref_dict[key] = load_image(value[0][0]) if value[1]['match_hist'] else None

    all_df_list = []  # all dataframes to be concatenated
    total_images = len((list(subfolder_dict.values())[0][0]))  # number of images in the folder
    # if running on preview mode, analyzes just the first 5 images of each folder
    total_images = 5 if preview and total_images > 10 else total_images
    for img_n in track(range(total_images), description=f'Analyzing {subfolder_images_in} images...'):
        img_to_segment = subfolder_dict[ch_segment][0][img_n]

        cellpose = segment_dict['use_cellpose']
        if cellpose:  # calls cellpose
            contours = run_cellpose(img_to_segment, segment_dict['use_gpu'],
                                    segment_dict['diameter'], segment_dict['magnification'],
                                    segment_dict['pixel_size'], segment_dict['shape'],
                                    segment_dict['eccentricity'], segment_dict['min_size'],
                                    segment_dict['max_size'], segment_dict['min_radius'],
                                    segment_dict['max_radius'], segment_dict['invert'],
                                    segment_dict['normalize'], segment_dict['net_avg'],
                                    segment_dict['resample'], segment_dict['flow_threshold'],
                                    segment_dict['mask_threshold'])

        else:  # calls forNMA pipeline
            contours = fornma_contour_finding(img_to_segment,
                                              magnification=segment_dict['magnification'],
                                              pixel_size=segment_dict['pixel_size'],
                                              rescale_intensity=segment_dict['rescale_intensity'],
                                              remove_bg=segment_dict['remove_bg'],
                                              radius_bg=segment_dict['radius_bg'],
                                              threshold=segment_dict['threshold'],
                                              offset=segment_dict['offset'],
                                              blur=segment_dict['blur'],
                                              adjust_size=segment_dict['adjust_size'],
                                              cut_edges=segment_dict['cut_edges'],
                                              shape=segment_dict['shape'],
                                              eccentricity=segment_dict['eccentricity'],
                                              min_size=segment_dict['min_size'],
                                              max_size=segment_dict['max_size'],
                                              min_radius=segment_dict['min_radius'],
                                              max_radius=segment_dict['max_radius'],
                                              fast_detection=segment_dict['fast_detection'],
                                              weakly_labeled=segment_dict['weakly_labeled'])

        contours = [f for f in contours if len(f) > 5]  # remove contours with less than 5 points
        if len(contours) == 0:  # skips execution if there are no contours
            message = f'Image {os.path.basename(img_to_segment)} has no objects.'
            print(message)
            continue

        image_df = perform_measure(contours, img_n, subfolder_dict, ref_dict, segment_dict)
        image_df["Condition"] = condition
        image_df["Overtime"] = is_overtime
        image_df['origin_folder'] = subfolder_images_in
        image_df = image_df.reset_index(drop=True)
        image_df = drop_cols(image_df, subfolder_dict)  # drop columns
        # now the complete df is split in smaller ones and saved

        df_results, df_draw = split_dfs(image_df, ch_name_list)
        df_draw['use_cellpose'] = cellpose
        draw = df_draw if wants_to_save else None
        save_dfs(df_results, path_to_save, draw)

        # save images
        saving_images(df_draw, path_to_save, ch_name_list, segment_dict['use_cellpose']) if wants_to_save else None
        # foci pkl object is generated here

    return None