# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 14:25:56 2021

@author: Luiza

File that puts all functions together 
"""

import os
import tempfile
from typing import List, Tuple, Any, Union
from PySide6.QtCore import Signal

import cv2 as cv
import pandas as pd

from src.Segmentation.analyze import analyze_dict
from src.Segmentation.df_managing.organize import filter_dataframe, get_foci_df, split_dfs

pd.options.mode.chained_assignment = None  # default='warn'


def rename_channel_parameters(channel_parameters: dict) -> dict:
    """ Renames parameter dictionary keys"""

    min_size = channel_parameters['foci_min_size'] if channel_parameters['foci_min_size'] != False else None
    max_size = channel_parameters['foci_max_size'] if channel_parameters['foci_max_size'] != False else None
    min_int = channel_parameters['foci_min_int'] if channel_parameters['foci_min_int'] != False else None
    max_int = channel_parameters['foci_max_int'] if channel_parameters['foci_max_int'] != False else None
    prominence = channel_parameters['foci_prominence'] if channel_parameters['foci_prominence'] != False else None

    new_dict = {'rescale_intensity': channel_parameters['rescale_intensity'],
                'remove_bg': channel_parameters["remove_background"],
                'radius_bg': channel_parameters['rolling_ball_radius'],
                'match_hist': channel_parameters['match_histograms'],
                'wants_ktr': channel_parameters['measure_translocation'],
                'ring_size': channel_parameters['ring_size'],
                'use_ellipse': channel_parameters['use_ellipse'],
                'wants_foci': channel_parameters['measure_foci'],
                'foci_min_size': min_size,
                'foci_max_size': max_size,
                'foci_min_int': min_int,
                'foci_max_int': max_int,
                'foci_proeminence': prominence
                }

    return new_dict


def adjust_parameters(parameters_dict) -> tuple[
    Any, Any, Any, Any, Any, Any, list[dict], Any, dict[Union[str, Any], Any]]:
    """
    Adjusts dictionary from parameters.toml to establish new variable names.
    """
    path_to_save = parameters_dict['path_to_save']
    ch_name_list = parameters_dict['names']
    ch_path_list = parameters_dict['channel_path_list']
    ch_with_nuc = parameters_dict['channel_with_nuclei']
    overtime = parameters_dict['overtime']
    parameter_list = [f for f in parameters_dict['channel_parameters'].values()][0:len(ch_path_list)]
    parameter_list = [rename_channel_parameters(f) for f in parameter_list]
    conditions = parameters_dict['subfolder_names']
    save_images = parameters_dict['save_images']

    shape = parameters_dict['segmentation']['shape'] if parameters_dict['segmentation']['shape'] != False else None
    eccentricity = parameters_dict['segmentation']['eccentricity'] if parameters_dict['segmentation'][
                                                                          'eccentricity'] != False else None
    min_size = parameters_dict['segmentation']['minimum_size'] if parameters_dict['segmentation'][
                                                                      'minimum_size'] != False else None
    max_size = parameters_dict['segmentation']['maximum_size'] if parameters_dict['segmentation'][
                                                                      'maximum_size'] != False else None
    min_radius = parameters_dict['segmentation']['minimum_radius'] if parameters_dict['segmentation'][
                                                                          'minimum_radius'] != False else None
    max_radius = parameters_dict['segmentation']['maximum_radius'] if parameters_dict['segmentation'][
                                                                          'maximum_radius'] != False else None

    segment_dict = {'magnification': parameters_dict['segmentation']['magnification'],
                    'pixel_size': parameters_dict['segmentation']['pixel_size'],
                    'rescale_intensity': parameters_dict['segmentation']['rescale_intensity'],
                    'remove_bg': parameters_dict['segmentation']['remove_background'],
                    'radius_bg': parameters_dict['segmentation']['rolling_ball_radius'],
                    'threshold': parameters_dict['segmentation']['forNMA']['threshold'],
                    'offset': parameters_dict['segmentation']['forNMA']['offset'],
                    'blur': parameters_dict['segmentation']['forNMA']['smooth'],
                    'adjust_size': parameters_dict['segmentation']['forNMA']['adjust_size'],
                    'cut_edges': parameters_dict['segmentation']['forNMA']['cut_edges'],
                    'shape': shape,
                    'eccentricity': eccentricity,
                    'min_size': min_size,
                    'max_size': max_size,
                    'min_radius': min_radius,
                    'max_radius': max_radius,
                    'fast_detection': parameters_dict['segmentation']['forNMA']['find_low_intensity_nucleus'],
                    'weakly_labeled': parameters_dict['segmentation']['forNMA']['weakly_labeled'],
                    'use_cellpose': parameters_dict['segmentation']['cellpose']['use_cellpose'],
                    'invert': False,
                    'normalize': True,
                    'diameter': parameters_dict['segmentation']['cellpose']['diameter'],
                    'net_avg': True,
                    'resample': True,
                    'flow_threshold': parameters_dict['segmentation']['cellpose']['flow_threshold'],
                    'mask_threshold': parameters_dict['segmentation']['cellpose']['mask_threshold'],
                    'use_gpu': parameters_dict['segmentation']['cellpose']['use_gpu'],
                    }

    return save_images, path_to_save, ch_name_list, ch_path_list, ch_with_nuc, overtime, parameter_list, conditions, \
           segment_dict


def adjust_parameters_interface(parameters_dict) -> Tuple[bool, str, List[str], List[str], str, dict]:
    """
       Adjusts dictionary from interface parameter dictionary  to establish new variable names.
       """
    save_images = True  # TODO change forinterface outut
    path_to_save = parameters_dict['global']['output_folder']
    ch_name_list = [f.replace('Channel ', '') for f in parameters_dict.keys() if 'Channel' in f]
    ch_with_nuc = parameters_dict['global']['channel_with_nuclei']
    # overtime = parameters_dict['global']['overtime']
    overtime = False
    parameter_list = [parameters_dict['Channel ' + f] for f in ch_name_list]
    conditions = list(parameters_dict['Channel ' + ch_name_list[0]]['paths'].keys())
    segment_dict = {'magnification': parameters_dict['global']['magnification'],
                    'pixel_size': parameters_dict['global']['pixel_size'],
                    'rescale_intensity': parameters_dict['global']['rescale_intensity'],
                    'remove_bg': parameters_dict['global']['remove_background'],
                    'radius_bg': parameters_dict['global']['radius_bg'],
                    'threshold': parameters_dict['fornma']['threshold'],
                    'offset': parameters_dict['fornma']['offset'],
                    'blur': parameters_dict['fornma']['blur'],
                    'adjust_size': parameters_dict['fornma']['adjust_size'],
                    'cut_edges': parameters_dict['fornma']['cut_edges'],
                    'shape': parameters_dict['global']['shape'],
                    'eccentricity': parameters_dict['global']['eccentricity'],
                    'min_size': parameters_dict['global']['min_size'],
                    'max_size': parameters_dict['global']['max_size'],
                    'min_radius': parameters_dict['global']['min_radius'],
                    'max_radius': parameters_dict['global']['max_radius'],
                    'fast_detection': parameters_dict['fornma']['find_low_intensity_nucleus'],
                    'weakly_labeled': parameters_dict['fornma']['weakly_labeled'],
                    'use_cellpose': parameters_dict['cellpose']['use_cellpose'],
                    'invert': False,
                    'normalize': True,
                    'diameter': parameters_dict['cellpose']['diameter'],
                    'net_avg': True,
                    'resample': True,
                    'flow_threshold': parameters_dict['cellpose']['flow_threshold'],
                    'mask_threshold': parameters_dict['cellpose']['mask_threshold'],
                    'use_gpu': False,
                    }

    return save_images, path_to_save, ch_name_list, ch_with_nuc, overtime, parameter_list, conditions, segment_dict


def create_folder_dict(
        ch_name_list: List[str],
        ch_path_list: List[str],
        ch_with_nuc: str,
        parameter_list: List[str]
) -> dict:
    """
    Returns the subfolders and a dictionary for a folder where:
        key = channel name 
        values = [ list, dict, bool] 
            values[0]: a list with all folders in a given channel (each folder can be a field or a treatment condition,
            for example)
            values[1]: the param_dict for this channel
            values[2]: boolean indicating if user wants to perform segmentation in this chanel
    """
    folder_dict = {}
    for i in range(len(ch_name_list)):
        seg = ch_with_nuc == ch_path_list[i]
        subfolders = sorted((os.listdir(ch_path_list[i])))
        folder_dict[ch_name_list[i]] = [[os.path.join(ch_path_list[i], f) for f in subfolders],
                                        parameter_list[i], seg]

    return subfolders, folder_dict


def create_subfolder_dict(folder_dict: dict,
                          iterator: int
                          ) -> dict:
    """
    Returns a dictionary for each subfolder where:
        key =  channel name
        values = [list, dictionary, bool]
            values[0]: list of every item inside folder (list of images)
            values[1]: dictionary os parameters (param_dict)
            values[2]: boolean indicating if user wants to perform segmentation in this chanel
    """
    subfolder_dict = {}
    for key, value in folder_dict.items():
        files = sorted(os.listdir(value[0][iterator]))
        files = [os.path.join(value[0][iterator], f) for f in files]
        subfolder_dict[key] = [files, value[1], value[2]]

    return subfolder_dict


def check_size(ch_dict: dict) -> bool:
    """ Sorts files and checks if all file_lists have the same size. """

    len_files = len(list(ch_dict.values())[0][0])  # first file list
    for key, value in ch_dict.items():
        value[0] = sorted(value[0])
        if len(value[0]) != len_files:
            return False

    return True


def save_dfs(df_results: pd.DataFrame,
             path_save: str):
    """ Saves dataframes"""
    tables = list(set(df_results['origin_folder']))
    for t in tables:
        df_foci, df_results = get_foci_df(df_results)
        df_save = df_results[df_results["origin_folder"] == t]
        df_save = df_save.reindex(columns=(['Frame'] + list([a for a in df_save.columns if a != 'Frame'])))
        df_save.drop(columns=(["origin_folder"]), inplace=True)
        cols = [f for f in df_save.columns if 'foci_df' not in f]
        df_save = df_save[cols]
        df_save.to_csv(os.path.join(path_save, t[:-4]) + ' Results.csv')
        if df_foci is not None:
            df_foci.to_csv(os.path.join(path_save, t[:-4]) + ' Foci Results.csv')
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
                cnt = [f[0] for f in cnt if len(f) > 0] if use_cellpose else cnt
                img = cv.drawContours(img, cnt, -1, (122, 144, 248), 1)

        cv.imwrite(os.path.join(saving_dir, name), img)


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
    df_draw.to_pickle(os.path.join(path_to_save, 'Results.pkl'))

    #    iterates over each folder in the dataframe
    for d in dirs:
        df_dir = df_draw[df_draw["origin_folder"] == d]
        saving_dir = os.path.join(path_to_save, d[:-4] + '-') if os.path.isdir(
            os.path.join(path_to_save, d[:-4])) else os.path.join(path_to_save, d[:-4])
        os.mkdir(saving_dir)
        #    iterates over each image channel inside the folder
        for ch in ch_name_list:
            saving_dir_ch = os.path.join(saving_dir, ch)
            os.mkdir(saving_dir_ch)
            draw_and_save(df_dir, ch, saving_dir_ch, use_cellpose)


def is_file_supported(subfolder_dict: dict,
                      preview: bool,
                      ) -> tuple[list[list[Any]], Union[int, Any]]:
    """ Checks if all images within image folders are supported file formats."""
    supported_files = ['.bmp', '.dib', '.jpeg', '.jpg', '.jpe', '.jp2', '.png',
                       '.webp', '.pbm', '.pgm', '.ppm', '.pxm', '.pnm', '.sr',
                       '.ras', '.tiff', '.tif', '.exr', '.hdr', '.pic']
    not_supported = []
    for key, value in subfolder_dict.items():
        wrong_file_formats = [f for f in value[0] if not f.lower().endswith(tuple(supported_files))]
        not_supported.append(wrong_file_formats)

    return not_supported


class MockSignal:
    def emit(self, *args, **kwargs):
        return


def run(parameters_dict: dict,
        preview: bool = False,
        headless: bool = False,
        callback: Signal = None,
        ) -> Union[dict[str, Union[str, tuple[list[list[Any]], Union[int, Any]]]], dict[str, Union[str, list[Any]]]]:
    """
    Gets all user inputs and applies them to analyze all folders and subfolders.
    Then filters results, draws images (if requested) and saves all results.
    """
    if callback is None:
        callback = MockSignal()

    if list(parameters_dict.keys())[0] == 'global':
        wants_to_save, path_to_save, ch_name_list, ch_with_nuc, overtime, parameter_list, conditions, segment_dict = \
            adjust_parameters_interface(parameters_dict)
        subfolders = list(parameter_list[0]['paths'].keys())  # names of treatments/conditions
        folder_dict = {}
        for channel in ch_name_list:
            folder_dict[channel] = [list(parameters_dict['Channel ' + channel]['paths'].values()), parameters_dict['Channel ' + channel],
                                    parameters_dict['global']['channel_with_nuclei'] == channel]
    else:
        wants_to_save, path_to_save, ch_name_list, ch_path_list, ch_with_nuc, overtime, parameter_list, conditions, \
        segment_dict = adjust_parameters(parameters_dict)
        subfolders, folder_dict = create_folder_dict(ch_name_list, ch_path_list,
                                                     ch_with_nuc, parameter_list)
        # tests whether number of conditions match the number os subfolders/treatments
        if len(conditions) != len(subfolders):
            conditions = [False] * len(subfolders)

    temp_dir = tempfile.TemporaryDirectory()

    for i in range(len(subfolders)):
        subfolder_dict = create_subfolder_dict(folder_dict, i)
        if not check_size(subfolder_dict):
            raise Exception("The folders contain different image numbers")

        not_supported = is_file_supported(subfolder_dict, preview)
        if len(not_supported) != 0:
            message = 'The following files are not supported by forNMA. Remove them from your folders an try again.'
            return {'status': 'bad', 'message': message, 'data': not_supported}

        total_df = analyze_dict(subfolder_dict, segment_dict, overtime, conditions[i], preview,
                                callback)  # ju usa esse pra remover outliers
        if total_df is None:
            continue

        filename = os.path.basename(subfolders[i]) + '.zip'
        # adds files to temporary directory
        total_df.to_pickle(os.path.join(temp_dir.name, filename))

    complete_df = filter_dataframe(temp_dir, headless)  # TODO AQUI QUE FILTRA, EU DIVIDIRIA EM 2 FUNÇÔES
    if complete_df.empty:
        raise Exception('No nucleus could be found on your images, adjust parameters and try again')

    # now the complete df is splitted in smaller ones and saved
    df_results, df_draw = split_dfs(complete_df, ch_name_list)
    save_dfs(df_results, path_to_save)
    if wants_to_save:  # save images
        saving_images(df_draw, path_to_save, ch_name_list,
                      segment_dict['use_cellpose'])  # foci pkl object is generated here

    temp_dir.cleanup()

    return {'status': 'ok', 'message': 'Completed Successfully!', 'data': []}
