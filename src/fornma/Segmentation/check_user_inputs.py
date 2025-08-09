import os
from typing import List

def check_dict(dictionary: dict,
               key_list: List[str]):
    """Checks if all keys are in a dictionary, given a list of standard keys."""
    if not set(dictionary.keys()).issubset(key_list):
        for key, value in dictionary.items():
            if key not in key_list:
                raise Exception(
                    f' The value {key} could not be found. Did you erase it? Try to download the parameters.toml file '
                    f'before trying again again.'
                )

    return None


def basic_path_check(path: str):
    """Checks if a path exists and if it is a folder"""
    if not type(path) == str:
        raise Exception(
            f'The  path  {path} is no in string format. Make sure to add quotation marks in every file.\n'
            f'Also make sure to add a comma every each file.\n'
            f'We know this whole path thing is complicated, so if you are '
            f'having troubles, try to check the tutorial at www.colocar aui caminho certo.br and try again')
    if not os.path.exists(path):
        raise Exception(f'The path {path} does not exist.\n '
                        f'We know this whole path thing is complicated, so if you are '
                        f'having troubles, try to check the tutorial at www.colocar aui caminho certo.br and try again')
    if not os.path.isdir(path):
        raise Exception(
            f'The path {path} is not a folder.\nWe know this whole path thing is complicated, so if you are'
            f' having troubles, try to check the tutorial at www.colocar aui caminho certo.br and try '
            f'again')

    return None


def basic_bool_check(val, key):
    if not type(val) == bool:
        raise Exception(f' The value for {key}  must be either true or false. Your input was: {val}')

    return None


def basic_int_check(val, key):
    if not type(val) == int:
        raise Exception(f' The value for {key} must be an integer number. Your input was: {val}')

    return None


def basic_float_check(val, key):
    if not type(val) == float and not type(val) == int:
        raise Exception(f' The value for {key} must be a number. Your input was: {val}')

    return None


def basic_str_check(val, key):
    if not type(val) == str:
        raise Exception(
            f' The value for {key} must be a string. Your input was: {val}.\nRemember to add quotation marks'
            f'around the word.')

    return None


def check_user_inputs(dic: dict):
    """Checks if user segmentation inputs are correct"""
    print('Checking user inputs...')
    main_keys = ['channel_path_list', 'names', 'subfolder_names', 'channel_with_nuclei', 'overtime', 'path_to_save',
                 'save_images', 'segmentation', 'channel_parameters']
    seg_keys = ['magnification', 'pixel_size', 'rescale_intensity', 'remove_background', 'rolling_ball_radius', 'shape',
                'eccentricity', 'minimum_size', 'maximum_size', 'minimum_radius', 'maximum_radius', 'forNMA',
                'cellpose']
    fornma_keys = ['use_fornma', 'threshold', 'offset', 'smooth', 'adjust_size', 'cut_edges',
                   'find_low_intensity_nucleus', 'weakly_labeled']
    cellpose_keys = ['use_cellpose', 'diameter', 'flow_threshold', 'mask_threshold', 'use_gpu', 'cellprob_threshold',
                     'invert']
    channel_keys = ['rescale_intensity', 'remove_background', 'rolling_ball_radius', 'match_histograms',
                    'measure_translocation', 'ring_size', 'use_ellipse', 'measure_foci', 'foci_min_size',
                    'foci_max_size', 'foci_min_int', 'foci_max_int', 'foci_prominence']

    check_dict(dic, main_keys)
    check_dict(dic['segmentation'], seg_keys)
    check_dict(dic['segmentation']['forNMA'], fornma_keys)
    check_dict(dic['segmentation']['cellpose'], cellpose_keys)
    for key, value in dic['channel_parameters'].items():
        check_dict(value, channel_keys)

    for file in dic['channel_path_list']:
        basic_path_check(file)

        subfiles = [os.path.join(file, f) for f in os.listdir(file)]
        for subfile in subfiles:
            if not os.path.isdir(file):
                raise Exception(f'The file {subfile}, that is located inside the folder {file} is not a folder.\n'
                                f'Remember that forNMA works with a file with subfolders structure. If you have images'
                                f'inside the folder {os.path.basename(file)}, please create a new folder and move your '
                                f'files inside. If you already have this, check if there is not any other files in this'
                                f' folder')

    basic_path_check(dic['channel_with_nuclei'])
    basic_path_check(dic['path_to_save'])

    if dic['names']:
        for name in dic['names']:
            if not type(name) == str:
                raise Exception(
                    f'The name {name} is no in string format. Make sure to add quotation marks in every name.\n'
                    f'Also make sure to add a comma every each file.')

    if dic['subfolder_names']:
        for name in dic['subfolder_names']:
            if not type(name) == str:
                raise Exception(
                    f'The name {name} is no in string format. Make sure to add quotation marks in every name.\n'
                    f'Also make sure to add a comma every each file.')

    basic_bool_check(dic['overtime'], 'overtime')
    basic_bool_check(dic['save_images'], 'save_images')

    seg = dic['segmentation']

    basic_int_check(seg['magnification'], 'magnification')
    basic_float_check(seg['pixel_size'], 'pixel_size')
    basic_bool_check(seg['rescale_intensity'], 'rescale_intensity')
    basic_bool_check(seg['remove_background'], 'remove_background')
    basic_int_check(seg['rolling_ball_radius'], 'rolling_ball_radius')
    basic_float_check(seg['shape'], 'shape') if seg['shape'] is not False else None
    basic_float_check(seg['eccentricity'], 'eccentricity') if seg['eccentricity'] is not False else None
    basic_float_check(seg['minimum_size'], 'minimum_size') if seg['minimum_size'] is not False else None
    basic_float_check(seg['maximum_size'], 'maximum_size') if seg['maximum_size'] is not False else None
    basic_float_check(seg['minimum_radius'], 'minimum_radius') if seg['minimum_radius'] is not False else None
    basic_float_check(seg['maximum_radius'], 'maximum_radius') if seg['maximum_radius'] is not False else None

    segf = dic['segmentation']['forNMA']
    basic_bool_check(segf['use_fornma'], 'use_fornma')

    available_thresholds = ['isodata', 'li', 'mean', 'minimum', 'otsu', 'triangle', 'yen', 'median', 'multiotsu',
                            'local_mean', 'local_gaussian']
    basic_str_check(segf['threshold'], 'threshold')
    if segf['threshold'] not in available_thresholds:
        raise Exception(f'The threshold you chose does not exist. Choose between: {", ".join(available_thresholds)}.')

    basic_float_check(segf['offset'], 'offset')
    basic_int_check(segf['smooth'], 'smooth')
    basic_float_check(segf['adjust_size'], 'adjust_size') if segf['adjust_size'] is not False else None
    basic_float_check(segf['cut_edges'], 'cut_edges') if segf['cut_edges'] is not False else None
    basic_bool_check(segf['find_low_intensity_nucleus'], 'find_low_intensity_nucleus')
    basic_bool_check(segf['weakly_labeled'], 'weakly_labeled')

    segc = dic['segmentation']['cellpose']
    basic_bool_check(segc['use_cellpose'], 'use_cellpose')
    basic_float_check(segc['diameter'], 'diameter')
    basic_float_check(segc['flow_threshold'], 'flow_threshold')
    basic_float_check(segc['mask_threshold'], 'mask_threshold')
    basic_bool_check(segc['use_gpu'], 'use_gpu')

    for channel, ch_dict in dic['channel_parameters'].items():
        basic_bool_check(ch_dict['rescale_intensity'], f'rescale_intensity at {channel} in channel_parameters')
        basic_bool_check(ch_dict['remove_background'], f'remove_background at {channel} in channel_parameters')
        basic_float_check(ch_dict['rolling_ball_radius'], f'rolling_ball_radius at {channel} in channel_parameters')
        basic_bool_check(ch_dict['match_histograms'], f'match_histograms at {channel} in channel_parameters')
        basic_bool_check(ch_dict['measure_translocation'], f'measure_translocation at {channel} in channel_parameters')
        basic_int_check(ch_dict['ring_size'], f'ring_size at {channel} in channel_parameters') \
            if ch_dict['ring_size'] is not False else None
        basic_bool_check(ch_dict['use_ellipse'], f'use_ellipse at {channel} in channel_parameters')
        basic_bool_check(ch_dict['measure_foci'], f'measure_foci at {channel} in channel_parameters')
        basic_float_check(ch_dict['foci_min_size'], f'foci_min_size at {channel} in channel_parameters') \
            if ch_dict['foci_min_size'] is not False else None
        basic_float_check(ch_dict['foci_max_size'], f'foci_max_size at {channel} in channel_parameters') \
            if ch_dict['foci_max_size'] is not False else None
        basic_float_check(ch_dict['foci_min_int'], f'foci_min_int at {channel} in channel_parameters') \
            if ch_dict['foci_min_int'] is not False else None
        basic_float_check(ch_dict['foci_max_int'], f'foci_max_size at {channel} in channel_parameters') \
            if ch_dict['foci_max_int'] is not False else None
        basic_float_check(ch_dict['foci_prominence'], f'foci_max_size at {channel} in channel_parameters') \
            if ch_dict['foci_prominence'] is not False else None

    print('Inputs: ok')

    return None
