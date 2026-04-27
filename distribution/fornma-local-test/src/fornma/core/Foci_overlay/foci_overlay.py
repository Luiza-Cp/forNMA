#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 17:49:36 2022

@author: luiza
"""
import warnings
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import cv2 as cv
import numpy as np
from typing import List, Tuple, Optional, Callable
import math
from matplotlib import pyplot as plt
import seaborn as sns
from rich.progress import track
from fornma.core.image_io import imwrite

import os, time, json, inspect

# ===== Progresso (GUI) =====
try:
    from fornma.gui.utils.progress import update_progress, cancel_requested
except Exception:
    from progress import update_progress, cancel_requested


# -------------------------------------------------------------------------
# Helpers de progresso
# -------------------------------------------------------------------------
def _progress_tick(progress_file,
                   pct_base,
                   pct_span,
                   done,
                   total,
                   log=None,
                   throttle_s=0.25,
                   _last=[0.0]):
    """Escreve progresso a cada 'throttle_s' segundos."""
    if not progress_file or not total:
        return
    now = time.time()
    if now - _last[0] < throttle_s:
        return
    _last[0] = now
    percent = pct_base + int((done / max(1, total)) * pct_span)
    percent = max(pct_base, min(pct_base + pct_span, percent))
    update_progress(progress_file, status="running", percent=percent, log=log or "")


# -------------------------------------------------------------------------
# Funções de overlay (sua lógica + instrumentação)
# -------------------------------------------------------------------------
def draw_foci_ch(group: pd.DataFrame,
                 channel_list: List[str],
                 shape: Tuple[int],
                 color_list: List[Tuple[int]],
                 monocolor: bool,
                 ):
    """
    Cria máscaras por canal desenhando os contornos de foci.
    """
    ch_image_dict = {}
    image_list = []
    for i in range(len(channel_list)):
        image = np.zeros((shape[0], shape[1], 3)) if not monocolor else np.zeros(shape)
        cnt_list = list(group['Foci_cnt_' + channel_list[i]])
        cnt_list = [item for sublist in cnt_list for item in sublist]
        image2 = cv.drawContours(image, cnt_list, -1, color_list[i], cv.FILLED) if not monocolor else \
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
    Dado uma lista de bboxes, recorta a imagem em sub-imagens.
    """
    img_list = []
    for bbox in bbox_list:  # x, y , w ,h
        img = image[bbox[1] - 2:bbox[1] + bbox[3] + 4,
                    bbox[0] - 2:bbox[0] + bbox[2] + 4]
        img_list.append(img)
    return img_list
def measure_pixels(ch_img_dict: dict,
                   df: pd.DataFrame,
                   *,
                   progress_cb: Optional[Callable[[int, Optional[str]], None]] = None,
                   log_prefix: str = "",
                   ) -> pd.DataFrame:
    """
    Conta pixels por célula, fazendo tick de progresso após processar cada célula.
    Evita criar listas gigantes de recortes antes de progredir.
    """
    bbox_list = list(df['bbox'])
    cell_list = list(df['Cell'])

    # dicionário de listas que vamos preencher célula a célula
    pixel_count_dict = {'Cell': []}
    for key in ch_img_dict.keys():
        pixel_count_dict['Total_pixel_' + key] = []

    for idx, (bbox, cell_id) in enumerate(zip(bbox_list, cell_list), start=1):
        x0, y0, w, h = bbox
        x1, y1 = x0 - 2, y0 - 2
        x2, y2 = x0 + w + 4, y0 + h + 4

        # conta pixels em cada canal/overlay para ESTA célula
        pixel_count_dict['Cell'].append(cell_id)
        for key, img in ch_img_dict.items():
            sub = img[y1:y2, x1:x2]
            pixel_count_dict['Total_pixel_' + key].append(int(np.count_nonzero(sub)))

        # tick de progresso aqui, enquanto o trabalho acontece
        if progress_cb:
            progress_cb(1, log=f"{log_prefix} — cell {cell_id} ({idx}/{len(cell_list)})")

    df_pixel_number = pd.DataFrame(pixel_count_dict)
    return df_pixel_number



def save_images_ch(group: pd.DataFrame,
                   channel_list: List[str],
                   shape: Tuple[int],
                   color_list: List[Tuple[int]],
                   cnt_col: str,
                   path_to_save: str,
                   name: str):
    """
    Gera e salva as imagens de overlay por célula (sem alterar progresso).
    """
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
        _ = [imwrite(f, j) for f, j in zip(image_names, images_to_save) if j.size != 0]
    return


def perform_foci_overlay(dfs: List[pd.DataFrame],
                         df_names: List[str],
                         save_images: bool,
                         path_save: str,
                         *,
                         # novos (opcionais) para progresso fino/cancelamento:
                         progress_cb: Optional[Callable[[int, Optional[str]], None]] = None,
                         cancel_check: Optional[Callable[[], bool]] = None,
                         progress_file: Optional[str] = None,
                         pct_base: int = 0,
                         pct_span: int = 100,
                         ):
    """
    Percorre cada DF/canal e executa a lógica de overlay por linha,
    disparando progresso fino dentro do processamento (medição/crop).
    """
    # Detecta canais a partir das colunas Image_name_
    channel_list = [f.replace('Image_name_', '') for f in dfs[0].columns if 'Image_name_' in f]
    color_list = [(0, 0, 255), (255, 0, 0), (0, 255, 0), (0, 128, 255),
                  (0, 255, 255), (255, 255, 0), (255, 0, 255), (127, 0, 255),
                  (128, 128, 0), (0, 128, 128), (128, 0, 128)]
    color_list = color_list * int(math.ceil(len(channel_list) / len(color_list)))

    cnt_col = [f for f in dfs[0].columns if 'Nuc_cnt' in f][0]
    shape = dfs[0]['Image_' + channel_list[0]].iloc[0].shape

    # total de unidades = nº de células em todos os DFs
    grand_total = int(sum(df.shape[0] for df in dfs))
    done = 0
    update_progress(progress_file, status="running", percent=pct_base,
                    log=f"Overlay stage: {len(dfs)} file(s), channels={channel_list}, total_cells={grand_total}")

    # wrapper local para somar +1 e repassar ao JSON (chamado dentro de measure_pixels)
    def _tick(step: int = 1, log: Optional[str] = None):
        nonlocal done
        done += step
        if cancel_check and cancel_check():
            update_progress(progress_file, status="canceled", log="Canceled (overlay).")
            raise KeyboardInterrupt("Canceled by user")
        _progress_tick(progress_file, pct_base, pct_span, done, grand_total, log=log)

    # acumulador para CSV final
    all_pixel_count_dfs = []

    for name, df in zip(df_names, dfs):
        if cancel_check and cancel_check():
            update_progress(progress_file, status="canceled", log="Canceled (overlay).")
            return

        df['bbox'] = df.apply(lambda x: cv.boundingRect(x[cnt_col]), axis=1)
        df.reset_index(inplace=True)

        # desenha máscaras mono (para contagem de pixels)
        ch_image_dict, image_list = draw_foci_ch(df, channel_list, shape, color_list, True)

        # contagem de pixels — aqui acontece o trabalho por célula, então “ticamos” aqui:
        df_pixel_count = measure_pixels(
            ch_img_dict=ch_image_dict,
            df=df,
            progress_cb=_tick,
            log_prefix=name
        )
        df_pixel_count['Image'] = name
        all_pixel_count_dfs.append(df_pixel_count)

        # salvar imagens coloridas por célula (opcional; sem mexer em progresso)
        if save_images:
            save_images_ch(df, channel_list, shape, color_list, cnt_col, path_save, name)

    # salvar CSV final com contagem de pixels
    os.makedirs(path_save, exist_ok=True)
    final_df = pd.concat(all_pixel_count_dfs)
    final_df.to_csv(os.path.join(path_save, 'Overlay Pixel Counts.csv'), index=False)

    update_progress(progress_file, status="running",
                    percent=min(100, pct_base + pct_span),
                    log=f"Overlay finished: {done}/{grand_total}")


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


def foci_overlay(
    pkl_results_folder_path: str,
    path_to_save: str,
    channel_list: Optional[List[str]] = None,
    save_images: bool = True,
    *,
    progress_file: str = None,
    pct_base: int = 0,
    pct_span: int = 100,
):
    """
    Função de orquestração do overlay (compatível com a sua API), agora com progresso fino.
    """
    # validações originais
    if not os.path.exists(pkl_results_folder_path):
        raise FileNotFoundError(f'The path "{pkl_results_folder_path}" does not exist. Did you type it right?')
    if not os.path.exists(path_to_save):
        raise FileNotFoundError(f'The path "{path_to_save}" does not exist. Did you type it right?')

    # coleta e lê PKLs
    pkl_files = sorted([os.path.join(pkl_results_folder_path, f) for f in os.listdir(pkl_results_folder_path) if f.endswith(".pkl")])
    if not pkl_files:
        update_progress(progress_file, status="error", message="No .pkl files found for overlay.")
        return

    dfs = [pd.read_pickle(f) for f in pkl_files]
    df_names = [os.path.splitext(os.path.basename(f))[0] for f in pkl_files]

    # descobre canais presentes (Foci_cnt_<CANAL>)
    channels_on_df = [c.replace('Foci_cnt_', '') for c in dfs[0].columns if c.startswith('Foci_cnt_')]

    # valida lista passada pelo usuário (mesma lógica)
    def _test_channel_list(df0: pd.DataFrame, ch_list: List[str], ch_on_df: List[str]) -> bool:
        return all(ch in ch_on_df for ch in ch_list)

    if channel_list is not None:
        channels = channel_list if _test_channel_list(dfs[0], channel_list, channels_on_df) else channels_on_df
    else:
        channels = channels_on_df

    # remove colunas de canais NÃO escolhidos (mesma lógica)
    channels_to_remove = [c for c in channels_on_df if c not in channels]
    cols_to_remove = []
    for ch in channels_to_remove:
        ctr = [c for c in dfs[0].columns if ch in c]
        cols_to_remove.extend(ctr)
    for col in cols_to_remove:
        _ = [df.drop(col, axis=1, inplace=True, errors="ignore") for df in dfs]

    # total = nº de células (linhas) em todos os DFs → progresso mais fluido
    total = int(sum(df.shape[0] for df in dfs))
    done = 0
    update_progress(
        progress_file,
        status="running",
        percent=pct_base,
        log=f"Overlay: {len(dfs)} file(s), channels={channels}, total_cells={total}"
    )

    # progress_cb que será chamado DENTRO do processamento (measure_pixels)
    def progress_cb(step: int = 1, log: Optional[str] = None):
        nonlocal done
        done += step
        if progress_file and cancel_requested(progress_file):
            update_progress(progress_file, status="canceled", log="Canceled (overlay).")
            raise KeyboardInterrupt("Canceled by user")
        _progress_tick(progress_file, pct_base, pct_span, done, total, log=log)

    # chama a função real (agora instrumentada para fazer ticks dentro do trabalho)
    try:
        perform_foci_overlay(
            dfs=dfs,
            df_names=df_names,
            save_images=save_images,
            path_save=path_to_save,
            progress_cb=progress_cb,
            cancel_check=(lambda: cancel_requested(progress_file) if progress_file else False),
            progress_file=progress_file,
            pct_base=pct_base,
            pct_span=pct_span,
        )
    except KeyboardInterrupt:
        return
    except Exception as e:
        update_progress(progress_file, status="error", message=str(e))
        raise

    update_progress(
        progress_file,
        status="running",
        percent=min(100, pct_base + pct_span),
        log=f"Overlay finished: {done}/{total}"
    )
    print('complete!')


# -------------------------------------------------------------------------
# Perfil (plot_profile) + instrumentação de progresso
# -------------------------------------------------------------------------
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
    for i in range(8):
        for j in range(8):
            if idx == len(x_df):
                break
            if i % 2 == 0:
                ax = axs[j, i]
                nuc = x_df[idx]['nuc'].iloc[0]
                sns.lineplot(data=x_df[idx].drop(columns=['nuc']), ax=ax)
                ax.set_title(f'X profile of nucleus {nuc}')
                ax.set(xticklabels=[]); ax.tick_params(bottom=False)
                ax.set(yticklabels=[]); ax.tick_params(left=False)
                plt.setp(ax.get_legend().get_texts(), fontsize='8')
                ax2 = axs[j, i + 1]
                sns.lineplot(data=y_df[idx].drop(columns=['nuc']), ax=ax2)
                ax2.set_title(f'Y profile of nucleus {nuc}')
                ax2.set(xticklabels=[]); ax2.tick_params(bottom=False)
                ax2.set(yticklabels=[]); ax2.tick_params(left=False)
                ax.legend_.remove(); ax2.legend_.remove()
                idx += 1

    if idx == len(x_df):
        for i in range(8):
            for j in range(8):
                ax = axs[j, i]
                ax.set(xticklabels=[]); ax.tick_params(bottom=False)
                ax.set(yticklabels=[]); ax.tick_params(left=False)

    legend_ax = fig.add_axes([0.92, .35, .075, 0.2])
    legend_ax.set(xticklabels=[]); legend_ax.tick_params(bottom=False)
    legend_ax.set(yticklabels=[]); legend_ax.tick_params(left=False)
    legend_ax.grid(False)
    handles, labels = axs[0, 0].get_legend_handles_labels()
    legend_ax.legend(handles, labels, loc='center', frameon=False)

    plt.suptitle(f'X and Y intensity profiles of {name}')
    plt.tight_layout(rect=[0, 0, .92, 0.98])

    os.makedirs(os.path.join(path_save, 'Profile-plots'), exist_ok=True)
    plt.savefig(os.path.join(path_save, 'Profile-plots', f'{name} {list_number}.png'))
    plt.savefig(os.path.join(path_save, 'Profile-plots', f'{name} {list_number}.svg'))
    plt.close(fig)
    return

def plot_profile(path_pickle_data: str,
                 path_save: str,
                 columns: List[str] = None,
                 *,
                 progress_file: str = None,
                 pct_base: int = 0,
                 pct_span: int = 100,
                 ):
    """
    From a folder with pickle files, plots intensity profiles per nucleus.
    Progress bar advances per nucleus computed.
    """
    # --- load data
    paths = [os.path.join(path_pickle_data, f) for f in os.listdir(path_pickle_data) if f.endswith('.pkl')]
    if not paths:
        update_progress(progress_file, status="error", message="No .pkl files found for plot_profile.")
        return

    dfs = [pd.read_pickle(f) for f in paths]
    names = [os.path.splitext(os.path.basename(f))[0] for f in paths]

    # --- channels
    if columns is None:
        channel_list = [c.replace('Foci_cnt_', '') for c in dfs[0].columns if c.startswith('Foci_cnt_')]
    else:
        channel_list = list(columns)

    # --- setup
    os.makedirs(os.path.join(path_save, 'Profile-plots'), exist_ok=True)
    shape = dfs[0][f'Image_{channel_list[0]}'].iloc[0].shape

    # --- progress bookkeeping
    total = int(sum(df.shape[0] for df in dfs))  # nuclei count across all files
    done = 0
    update_progress(
        progress_file,
        status="running",
        percent=pct_base,
        log=f"Profiles: {len(dfs)} file(s), channels={channel_list}, total_nuclei={total}"
    )

    # small helper to tick progress right after heavy per-nucleus work
    def _tick_after_nucleus(log_msg: str):
        nonlocal done
        done += 1
        if progress_file and cancel_requested(progress_file):
            update_progress(progress_file, status="canceled", log="Canceled (profiles).")
            raise KeyboardInterrupt("Canceled by user")
        _progress_tick(progress_file, pct_base, pct_span, done, total, log=log_msg)

    # --- main loop
    try:
        for name, df in zip(names, dfs):
            if progress_file and cancel_requested(progress_file):
                update_progress(progress_file, status="canceled", log="Canceled (profiles).")
                return

            x_df_list, y_df_list = [], []
            # compute profiles nucleus-by-nucleus (heavy step)
            for i in range(df.shape[0]):
                # heavy computation for this nucleus
                x_nuc_df, y_nuc_df = get_nuc_profile(channel_list, shape, df, i)

                # annotate nucleus id and accumulate
                nuc_id = df['Cell'].iloc[i]
                x_nuc_df['nuc'] = nuc_id
                y_nuc_df['nuc'] = nuc_id
                x_df_list.append(x_nuc_df)
                y_df_list.append(y_nuc_df)

                # tick progress immediately after computing this nucleus
                _tick_after_nucleus(f"{name} — nucleus {nuc_id} — {done+0}/{total}")

            # plot in batches of 32 nuclei (IO bound; no extra ticks needed)
            splitted_x_df_list = [x_df_list[k:k + 32] for k in range(0, len(x_df_list), 32)]
            splitted_y_df_list = [y_df_list[k:k + 32] for k in range(0, len(y_df_list), 32)]
            for sub_idx in range(len(splitted_y_df_list)):
                if progress_file and cancel_requested(progress_file):
                    update_progress(progress_file, status="canceled", log="Canceled (profiles).")
                    return
                plot_and_save_profile(
                    splitted_x_df_list[sub_idx],
                    splitted_y_df_list[sub_idx],
                    name,
                    path_save,
                    sub_idx
                )

    except KeyboardInterrupt:
        # graceful cancel
        return
    except Exception as e:
        update_progress(progress_file, status="error", message=str(e))
        raise

    # --- finish this action's span
    update_progress(
        progress_file,
        status="running",
        percent=min(100, pct_base + pct_span),
        log=f"Profiles finished: {done}/{total}"
    )
