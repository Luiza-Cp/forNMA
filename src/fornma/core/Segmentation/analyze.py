# -*- coding: utf-8 -*-
"""
Created on Sun May 16 20:11:52 2021

@author: Luiza
"""
import numpy as np
import os
import pandas as pd
from typing import List, Optional, Union, Callable
import cv2 as cv

from pandas import DataFrame
from rich.progress import track

from .measure.Morphology import Morphology
from .measure.Cell import Cell
from .segmentation.find_contours import fornma_contour_finding, load_image
from .segmentation.cellpose_integration import get_cellpose_model, run_cellpose
from .df_managing.organize import get_foci_df, split_dfs
from fornma.core.image_io import imwrite

pd.options.mode.chained_assignment = None  # default='warn'
from fornma.shared.progress import update_progress


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
             df_draw: Optional[pd.DataFrame],
             result_label: Optional[str] = None):
    """ Saves dataframes"""
    tables = list(set(df_results['origin_folder']))
    result_name = f"{result_label} Results.csv" if result_label else "Results.csv"
    foci_name = f"{result_label} Foci Results.csv" if result_label else "Foci Results.csv"
    pkl_label = f" {result_label}" if result_label else ""

    for t in tables:
        df_foci, df_results = get_foci_df(df_results)
        df_save = df_results[df_results["origin_folder"] == t]
        df_save = df_save.reindex(columns=(['Frame'] + list([a for a in df_save.columns if a != 'Frame'])))
        df_save.drop(columns=(["origin_folder"]), inplace=True)
        cols = [f for f in df_save.columns if 'foci_df' not in f]
        df_save = df_save[cols]
        os.makedirs(os.path.join(path_save, t), exist_ok=True)
        image_name = os.path.splitext(df_results[[f for f in df_results.columns if f.startswith('Image_name')][0]].iloc[0])[0]
        if not os.path.exists(os.path.join(path_save, t, result_name)):
            df_save.to_csv(os.path.join(path_save, t, result_name))
        else:
            df_save.to_csv(os.path.join(path_save, t, result_name), mode='a', header=None)

        if df_draw is not None:
            path_pkl = os.path.join(path_save, t, 'pkl-data')
            os.makedirs(path_pkl, exist_ok=True)
            df_draw.to_pickle(os.path.join(path_pkl, f' {image_name}{pkl_label} results.pkl'))

        if df_foci is not None:
            if not os.path.exists(os.path.join(path_save, t, foci_name)):
                df_foci.to_csv(os.path.join(path_save, t, foci_name))
            else:
                df_foci.to_csv(os.path.join(path_save, t, foci_name), mode='a', header=None)
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
                    and 'Y_draw' not in f and 'Image_' not in f and 'Nuc_cnt_' not in f]

    df = df.filter(regex=ch + "|Cell|X")
    cnt_grouped = df.groupby('Image_name_' + ch)
    fs = cv.getFontScaleFromHeight(2, 15, 2)
    for name, group in cnt_grouped:
        img = group['Image_' + ch].iloc[0]
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
        cnt_nuc = list(group['Nuc_cnt_' + ch])
        img = _draw_contours_if_any(img, cnt_nuc, (98, 59, 132), 1)
        for i in range(len(group['Cell'])):
            img = cv.putText(img, str(int(group['Cell'].iloc[i])),
                             ((group['X'] + 5).iloc[i], group['Y_draw_' + ch].iloc[i]),
                             2, fs, (122, 144, 248), 1)

        for col in cols_to_draw:
            if 'Foci' in col:
                foci_cnt = list(group['Foci_cnt_' + ch])
                img = _draw_contours_if_any(img, foci_cnt, (122, 144, 248), 1)

            else:
                cnt = list(group[col])
                img = _draw_contours_if_any(img, cnt, (122, 144, 248), 1)

        prog = os.environ.get("FORNMA_PROGRESS_FILE")
        imwrite(os.path.join(saving_dir, name), img)
        preview_path = os.path.join(saving_dir, "_preview.png")
        # UI-only copy: contrast-stretched with thicker, brighter contours so they are visible on screen.
        imwrite(preview_path, _render_preview(group, ch, cols_to_draw, fs))
        update_progress(prog, preview_path=preview_path, append_preview_path=preview_path)

    return None


def _stretch_for_display(img: np.ndarray) -> np.ndarray:
    """Map the 1st-99.8th intensity percentiles to 0-255 so dim images are readable."""
    arr = np.asarray(img, dtype=np.float32)
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    lo, hi = np.percentile(arr, (1, 99.8))
    if hi <= lo:
        hi = lo + 1.0
    return (np.clip((arr - lo) / (hi - lo), 0.0, 1.0) * 255).astype(np.uint8)


def _render_preview(group: pd.DataFrame, ch: str, cols_to_draw: List[str], fs: float) -> np.ndarray:
    """Draw the UI preview for one image; colors are BGR because images are encoded with OpenCV."""
    nucleus_color = (0, 230, 255)   # yellow
    other_color = (255, 80, 255)    # magenta
    label_color = (255, 255, 255)
    preview = cv.cvtColor(_stretch_for_display(group['Image_' + ch].iloc[0]), cv.COLOR_GRAY2BGR)
    preview = _draw_contours_if_any(preview, list(group['Nuc_cnt_' + ch]), nucleus_color, 2)
    for col in cols_to_draw:
        values = list(group['Foci_cnt_' + ch]) if 'Foci' in col else list(group[col])
        preview = _draw_contours_if_any(preview, values, other_color, 2)
    for i in range(len(group['Cell'])):
        preview = cv.putText(preview, str(int(group['Cell'].iloc[i])),
                             ((group['X'] + 5).iloc[i], group['Y_draw_' + ch].iloc[i]),
                             2, fs, label_color, 1, cv.LINE_AA)
    return preview


def saving_images(df_draw: pd.DataFrame,
                  path_to_save: str,
                  ch_name_list: List[str],
                  use_cellpose: bool,
                  result_label: Optional[str] = None
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
        if result_label:
            saving_dir = os.path.join(saving_dir, result_label)
        os.makedirs(saving_dir, exist_ok=True)
        #    iterates over each image channel inside the folder
        for ch in ch_name_list:
            saving_dir_ch = os.path.join(saving_dir, ch)
            os.makedirs(saving_dir_ch, exist_ok=True)
            draw_and_save(df_dir, ch, saving_dir_ch, use_cellpose)
    return None

def _drawable_contours(values) -> List[np.ndarray]:
    """Return OpenCV-drawable contours from dataframe contour values."""
    contours = []

    def collect(value):
        if value is None:
            return
        if isinstance(value, np.ndarray):
            cnt = np.asarray(value)
            if cnt.ndim == 2 and cnt.shape[1] == 2 and len(cnt) > 0:
                contours.append(np.ascontiguousarray(cnt, dtype=np.int32))
            elif cnt.ndim == 3 and cnt.shape[1:] == (1, 2) and len(cnt) > 0:
                contours.append(np.ascontiguousarray(cnt, dtype=np.int32))
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                collect(item)

    collect(values)
    return contours


def _draw_contours_if_any(img: np.ndarray, contours, color, thickness: int) -> np.ndarray:
    contours = _drawable_contours(contours)
    if not contours:
        return img
    return cv.drawContours(img, contours, -1, color, thickness)


def _measurable_contours(contours: List[np.ndarray]) -> List[np.ndarray]:
    """Return contours that can be represented in the measurement output."""
    return [cnt for cnt in contours if len(cnt) > 5]


def create_nuclei_cytoplasm_mapping(
        nucleus_contours: List[np.ndarray],
        cytoplasm_contours: List[np.ndarray],
        frame: int,
        condition: Optional[str],
        is_overtime: bool,
        nucleus_image_name: str,
        cytoplasm_image_name: str,
        origin_folder: str,
) -> pd.DataFrame:
    """
    Relate nuclei to cytoplasm masks without copying measurement columns.

    A nucleus is assigned to every cytoplasm contour containing its centroid.
    Unmatched objects are preserved so the relationship table describes all
    segmented objects, including ambiguous and multinucleated cases.
    """
    nucleus_contours = _measurable_contours(nucleus_contours)
    cytoplasm_contours = _measurable_contours(cytoplasm_contours)
    nucleus_to_cytoplasm = {index + 1: [] for index in range(len(nucleus_contours))}
    cytoplasm_to_nucleus = {index + 1: [] for index in range(len(cytoplasm_contours))}

    for nucleus_id, nucleus_contour in enumerate(nucleus_contours, start=1):
        moments = cv.moments(nucleus_contour)
        if moments["m00"] == 0:
            continue
        centroid = (moments["m10"] / moments["m00"], moments["m01"] / moments["m00"])
        for cytoplasm_id, cytoplasm_contour in enumerate(cytoplasm_contours, start=1):
            if cv.pointPolygonTest(cytoplasm_contour, centroid, False) >= 0:
                nucleus_to_cytoplasm[nucleus_id].append(cytoplasm_id)
                cytoplasm_to_nucleus[cytoplasm_id].append(nucleus_id)

    common = {
        "Frame": frame,
        "Condition": condition,
        "Overtime": is_overtime,
        "Nucleus_image_name": nucleus_image_name,
        "Cytoplasm_image_name": cytoplasm_image_name,
        "origin_folder": origin_folder,
    }
    rows = []
    for nucleus_id, cytoplasm_ids in nucleus_to_cytoplasm.items():
        if not cytoplasm_ids:
            rows.append({
                **common,
                "Nucleus_ID": nucleus_id,
                "Cytoplasm_ID": pd.NA,
                "Pair_status": "nucleus_without_cytoplasm",
                "N_nuclei_in_cytoplasm": pd.NA,
                "N_cytoplasms_for_nucleus": 0,
            })
            continue
        for cytoplasm_id in cytoplasm_ids:
            nuclei_ids = cytoplasm_to_nucleus[cytoplasm_id]
            status = "ambiguous" if len(cytoplasm_ids) > 1 else (
                "multinucleated" if len(nuclei_ids) > 1 else "matched"
            )
            rows.append({
                **common,
                "Nucleus_ID": nucleus_id,
                "Cytoplasm_ID": cytoplasm_id,
                "Pair_status": status,
                "N_nuclei_in_cytoplasm": len(nuclei_ids),
                "N_cytoplasms_for_nucleus": len(cytoplasm_ids),
            })

    for cytoplasm_id, nucleus_ids in cytoplasm_to_nucleus.items():
        if not nucleus_ids:
            rows.append({
                **common,
                "Nucleus_ID": pd.NA,
                "Cytoplasm_ID": cytoplasm_id,
                "Pair_status": "cytoplasm_without_nucleus",
                "N_nuclei_in_cytoplasm": 0,
                "N_cytoplasms_for_nucleus": pd.NA,
            })

    columns = [
        "Frame", "Condition", "Overtime", "Nucleus_image_name", "Cytoplasm_image_name",
        "Nucleus_ID", "Cytoplasm_ID", "Pair_status", "N_nuclei_in_cytoplasm",
        "N_cytoplasms_for_nucleus", "origin_folder",
    ]
    mapping = pd.DataFrame(rows, columns=columns)
    for column in ("Nucleus_ID", "Cytoplasm_ID", "N_nuclei_in_cytoplasm", "N_cytoplasms_for_nucleus"):
        mapping[column] = mapping[column].astype("Int64")
    return mapping


def save_nuclei_cytoplasm_mapping(mapping: pd.DataFrame, path_save: str) -> None:
    """Save a relationship-only table alongside nuclear and cytoplasm results."""
    if mapping.empty:
        return
    for folder in mapping["origin_folder"].drop_duplicates():
        path_folder = os.path.join(path_save, folder)
        os.makedirs(path_folder, exist_ok=True)
        output_path = os.path.join(path_folder, "Nuclei Cytoplasm Mapping.csv")
        output = mapping[mapping["origin_folder"] == folder].drop(columns=["origin_folder"])
        output.to_csv(
            output_path,
            mode="a" if os.path.exists(output_path) else "w",
            header=not os.path.exists(output_path),
            index=False,
        )


def _uses_cytoplasm(subfolder_value) -> bool:
    return len(subfolder_value) > 3 and bool(subfolder_value[3])


def _measurement_subfolder_dict(subfolder_dict: dict, compartment: str) -> dict:
    suffix = "nuc" if compartment == "nucleus" else "cyto"
    measure_key = "measure_nucleus" if compartment == "nucleus" else "measure_cytoplasm"
    default_measure = compartment == "nucleus"
    selected = {}
    for channel, value in subfolder_dict.items():
        channel_params = value[1]
        if not bool(channel_params.get(measure_key, default_measure)):
            continue
        output_channel = f"{channel}_{suffix}"
        selected[output_channel] = [value[0], channel_params, value[2]]
    return selected


def _make_ref_dict(subfolder_dict: dict) -> dict:
    ref_dict = {}
    for key, value in subfolder_dict.items():
        ref_dict[key] = load_image(value[0][0]) if value[1]['match_hist'] else None
    return ref_dict


def _cellpose_segment(
        image_path: str,
        segment_dict: dict,
        compartment: str,
        model=None,
) -> List[np.ndarray]:
    cellpose_params = segment_dict.get("cytoplasm_cellpose", {}) if compartment == "cytoplasm" else {}
    return run_cellpose(
        image_path=image_path,
        use_gpu=segment_dict['use_gpu'],
        diameter=cellpose_params.get('diameter', segment_dict['diameter']),
        mag=segment_dict['magnification'],
        px_s=segment_dict['pixel_size'],
        shape=cellpose_params.get('shape', segment_dict['shape']),
        eccentricity=cellpose_params.get('eccentricity', segment_dict['eccentricity']),
        min_size=cellpose_params.get('min_size', segment_dict['min_size']),
        max_size=cellpose_params.get('max_size', segment_dict['max_size']),
        min_radius=cellpose_params.get('min_radius', segment_dict['min_radius']),
        max_radius=cellpose_params.get('max_radius', segment_dict['max_radius']),
        model_type=cellpose_params.get('model_type', segment_dict.get('model_type', 'nuclei')),
        invert=cellpose_params.get('invert', segment_dict['invert']),
        normalize=cellpose_params.get('normalize', segment_dict['normalize']),
        resample=cellpose_params.get('resample', segment_dict['resample']),
        rescale_intensity=cellpose_params.get('rescale_intensity', segment_dict['rescale_intensity']),
        remove_bg=cellpose_params.get('remove_bg', segment_dict['remove_bg']),
        radius_bg=cellpose_params.get('radius_bg', segment_dict['radius_bg']),
        flow_threshold=cellpose_params.get('flow_threshold', segment_dict['flow_threshold']),
        cellprob_threshold=cellpose_params.get('cellprob_threshold', segment_dict['cellprob_threshold']),
        model=model,
    )


def _process_measurement_pass(
        contours: List[np.ndarray],
        img_n: int,
        compartment: str,
        subfolder_dict: dict,
        segment_dict: dict,
        condition: Optional[str],
        is_overtime: bool,
        subfolder_images_in: str,
        path_to_save: str,
        wants_to_save: bool,
) -> bool:
    contours = _measurable_contours(contours)
    if len(contours) == 0:
        return False

    measure_dict = _measurement_subfolder_dict(subfolder_dict, compartment)
    if not measure_dict:
        return False

    ref_dict = _make_ref_dict(measure_dict)
    pass_segment_dict = dict(segment_dict)
    if compartment == "cytoplasm":
        pass_segment_dict["use_cellpose"] = True

    image_df = perform_measure(contours, img_n, measure_dict, ref_dict, pass_segment_dict)
    image_df["Condition"] = condition
    image_df["Overtime"] = is_overtime
    image_df['origin_folder'] = subfolder_images_in
    image_df = image_df.reset_index(drop=True)
    image_df = drop_cols(image_df, measure_dict)

    ch_name_list = list(measure_dict.keys())
    df_results, df_draw = split_dfs(image_df, ch_name_list)
    df_draw['use_cellpose'] = pass_segment_dict['use_cellpose']
    draw = df_draw if wants_to_save else None
    legacy_nucleus_only = segment_dict.get("segmentation_mode", "nucleus") == "nucleus" and compartment == "nucleus"
    result_label = None if legacy_nucleus_only else ("Nuclei" if compartment == "nucleus" else "Cytoplasm")
    save_dfs(df_results, path_to_save, draw, result_label=result_label)

    if wants_to_save:
        saving_images(
            df_draw,
            path_to_save,
            ch_name_list,
            pass_segment_dict['use_cellpose'],
            result_label=result_label,
        )

    return True


def analyze_dict(
        subfolder_dict: dict,  # dict of every channel
        segment_dict: dict,    # dict of global parameters
        is_overtime: bool,
        condition: Optional[str],
        preview: bool,
        ch_name_list: List[str],
        path_to_save: str,
        wants_to_save: bool,
        subfolder_images_in: str,
        progress_cb: Optional[Callable[[], None]] = None,
        preview_indices: Optional[List[int]] = None,
) -> Union[bool, DataFrame]:
    """
    Given a dictionary containing information about each image channel analysis and the parameters used to perform cell
    segmentation, returns a dataframe containing the measurements and contours of each cell in every channel.
    This function is responsible for organizing all measuring functions.
    """
    ch_segment = None
    ch_cytoplasm = None
    for key, value in subfolder_dict.items():
        if value[2]:
            ch_segment = key
        if _uses_cytoplasm(value):
            ch_cytoplasm = key

    # segurança: se nada foi marcado para segmentar, escolhe o primeiro canal
    if ch_segment is None:
        ch_segment = next(iter(subfolder_dict.keys()))

    all_df_list = []  # all dataframes to be concatenated

    # número total de imagens nessa subpasta
    total_images = len(list(subfolder_dict.values())[0][0])
    if preview and preview_indices is not None and len(preview_indices) > 0:
        img_indices = [i for i in preview_indices if 0 <= i < total_images]
    else:
        n_imgs_used = 5 if (preview and total_images > 10) else total_images
        img_indices = list(range(n_imgs_used))

    segmentation_mode = segment_dict.get("segmentation_mode", "nucleus")
    needs_nucleus = segmentation_mode in ("nucleus", "both")
    needs_cytoplasm = segmentation_mode in ("cytoplasm", "both")

    cellpose = segment_dict['use_cellpose']
    cellpose_model = None
    if needs_nucleus and cellpose:
        cellpose_model = get_cellpose_model(
            model_type=segment_dict.get('model_type', 'nuclei'),
            use_gpu=segment_dict['use_gpu'],
        )
    cytoplasm_model = None
    if needs_cytoplasm:
        cytoplasm_cellpose = segment_dict.get("cytoplasm_cellpose", {})
        cytoplasm_model = get_cellpose_model(
            model_type=cytoplasm_cellpose.get('model_type', 'cyto3'),
            use_gpu=segment_dict['use_gpu'],
        )

    # se você usa rich.progress.track, mantém:
    for img_n in track(img_indices, description=f'Analyzing {subfolder_images_in} images...'):
        img_to_segment = subfolder_dict[ch_segment][0][img_n]

        processed_any = False
        nucleus_contours = []
        cytoplasm_contours = []

        if needs_nucleus:
            if cellpose:  # calls cellpose
                nucleus_contours = _cellpose_segment(
                    image_path=img_to_segment,
                    segment_dict=segment_dict,
                    compartment="nucleus",
                    model=cellpose_model,
                )
            else:  # calls forNMA pipeline
                nucleus_contours = fornma_contour_finding(
                    img_to_segment,
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
                    weakly_labeled=segment_dict['weakly_labeled']
                )
            processed_any = _process_measurement_pass(
                nucleus_contours,
                img_n,
                "nucleus",
                subfolder_dict,
                segment_dict,
                condition,
                is_overtime,
                subfolder_images_in,
                path_to_save,
                wants_to_save,
            ) or processed_any

        if needs_cytoplasm:
            cytoplasm_channel = ch_cytoplasm or ch_segment
            img_to_segment_cyto = subfolder_dict[cytoplasm_channel][0][img_n]
            cytoplasm_contours = _cellpose_segment(
                image_path=img_to_segment_cyto,
                segment_dict=segment_dict,
                compartment="cytoplasm",
                model=cytoplasm_model,
            )
            processed_any = _process_measurement_pass(
                cytoplasm_contours,
                img_n,
                "cytoplasm",
                subfolder_dict,
                segment_dict,
                condition,
                is_overtime,
                subfolder_images_in,
                path_to_save,
                wants_to_save,
            ) or processed_any

        if (
            needs_nucleus
            and needs_cytoplasm
            and _measurement_subfolder_dict(subfolder_dict, "nucleus")
            and _measurement_subfolder_dict(subfolder_dict, "cytoplasm")
        ):
            mapping = create_nuclei_cytoplasm_mapping(
                nucleus_contours=nucleus_contours,
                cytoplasm_contours=cytoplasm_contours,
                frame=img_n,
                condition=condition,
                is_overtime=is_overtime,
                nucleus_image_name=os.path.basename(img_to_segment),
                cytoplasm_image_name=os.path.basename(img_to_segment_cyto),
                origin_folder=subfolder_images_in,
            )
            save_nuclei_cytoplasm_mapping(mapping, path_to_save)

        if not processed_any:
            # imagem “vazia”: mesmo assim contamos 1 passo de progresso
            message = f'Image {os.path.basename(img_to_segment)} has no objects.'
            print(message)
            prog = os.environ.get("FORNMA_PROGRESS_FILE")
            update_progress(prog, append_log=message, message=message)
            if progress_cb is not None:
                progress_cb()
            continue

        # 🔔 tick de progresso por imagem processada
        if progress_cb is not None:
            progress_cb()

    return None
