import cv2 as cv
import streamlit as st
import os
from streamlit_image_coordinates import streamlit_image_coordinates
import numpy as np
import ast
import random
import pandas as pd
import math
from fornma.core.image_io import imread, imwrite

st.set_page_config(layout='wide')


def draw_x(image, coordinates):
    y = int((image.shape[0] * coordinates['y']) / coordinates['height'])
    x = int((image.shape[1] * coordinates['x']) / coordinates['width'])
    cv.putText(image, 'x', (x, y), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    return image


def draw_track(
        df: pd.DataFrame,
        img: np.ndarray,
        frame: int,
        complete: bool = False):  # teoricamente desenha o tarck em uma imagem, a partir de um df

    df_0 = df.loc[df['Frame'] == frame]
    coordinates = list(zip(df_0['X'].astype(int), df_0['Y'].astype(int)))
    family_name = list(df_0['family_name'].astype(str))
    colors = list(df_0['family_color'])
    font_scale = min(img.shape[0:2]) * 0.0005
    thickness = math.ceil(min(img.shape[0:2]) * 0.0011)
    for f in range(len(coordinates)):
        cv.circle(img, coordinates[f], 2, colors[f], 2)
    for f, g, h in zip(family_name, coordinates, colors):
        cv.putText(img, f, g, cv.FONT_HERSHEY_SIMPLEX, font_scale, h, thickness)

    tracks_df = df.loc[df["Frame"] <= frame].sort_values(by='Frame')
    if not complete:
        tracks_df = tracks_df.loc[tracks_df["Frame"] >= frame - 7].sort_values(by='Frame')
    line = list(zip(tracks_df['X'], tracks_df['Y']))
    line_previous = list(zip(tracks_df['previous_x'], tracks_df['previous_y']))
    track_colors = list(tracks_df['family_color'])
    for f, g, h in zip(line, line_previous, track_colors):
        if not np.isnan(f[0]) and not np.isnan(g[0]):
            g = (int(g[0]), int(g[1]))
            cv.line(img, (int(f[0]), int(f[1])), (int(g[0]), int(g[1])), h, thickness=1)

    return img


def redraw_images():
    images_dict = {}
    for f in range(len(st.session_state['images_dict'].keys())):
        images_dict[f] = draw_track(st.session_state['df'], st.session_state['images_dict'][f].copy(), f)

    st.session_state['temp_images_dict'] = images_dict.copy()
    st.session_state['frame_value_dict'] = {}  # clear all selection
    return


def find_corresponding_cell(
        df: pd.DataFrame,
        coordinates,
        frame,
) -> pd.Series:
    """
    Measures the distance between the coordinates and the cells from table, to find which is the clicked cell
    """
    image_shape = st.session_state['image_shape']
    df_frame = df[df['Frame'] == frame]
    y = int((image_shape[0] * coordinates['y']) / coordinates['height'])
    x = int((image_shape[1] * coordinates['x']) / coordinates['width'])
    df_frame['distance'] = np.sqrt(
        df_frame['X'].apply(lambda n: (n - x) ** 2) + df_frame['Y'].apply(lambda n: (n - y) ** 2)
    )
    closer = df_frame.sort_values(by=['distance']).iloc[0]

    return closer


def get_selected_cells_df(positions):
    cells = []
    for frame, coordinates in positions.items():
        cells.append(find_corresponding_cell(st.session_state['df'], coordinates, frame))
    cells_df = pd.concat(cells, axis=1).transpose().sort_values(by='Frame')

    return cells_df


def link_tracks():
    st.session_state['df']['family_name'] = st.session_state['df']['family_name'].astype(str)
    positions = st.session_state['frame_value_dict']
    cells_df = get_selected_cells_df(positions)

    #cells_df.iloc[-1]['previous_x'] = np.nan # cuidar isso, pq daí a célula a ser ligada é sempre a ultima, e as vezes ela n vai estar desvinculada das outras
    #cells_df.iloc[-1]['previous_y'] = np.nan

    #st.write(cells_df)

    if not any(cells_df['previous_x'].isna()):
        cells_df['previous_x'].iloc[-1] = np.nan
        cells_df['previous_y'].iloc[-1] = np.nan

    cells_df['previous_x'] = cells_df['previous_x'].fillna(cells_df['X'].shift())
    cells_df['previous_y'] = cells_df['previous_y'].fillna(cells_df['Y'].shift())
    first_family_name = cells_df['family_name'].iloc[0]
    first_family_color = str(cells_df['family_color'].iloc[0])
    last_family_name = cells_df['family_name'].iloc[-1]
    last_family_track = cells_df['track_id'].iloc[-1]

    cells_df['family'] = cells_df['family'].iloc[0]
    cells_df['family_name'] = cells_df['family_name'].iloc[0]
    cells_df['family_color'] = first_family_color
    cells_df['family_color'] = cells_df['family_color'].apply(ast.literal_eval)

    st.session_state['df'].update(cells_df)

    track_to_modify = st.session_state['df'][st.session_state['df']['track_id'] == last_family_track]
    track_to_modify['family_name'] = track_to_modify['family_name'].apply(
        lambda x: x.replace(last_family_name, first_family_name)
    )
    track_to_modify['family_color'] = first_family_color
    track_to_modify['family_color'] = track_to_modify['family_color'].apply(ast.literal_eval)
    st.session_state['df'].update(track_to_modify)

    redraw_images()
    message = {'success': 'Tracks linked successfully!'}

    return message


def cell_division_func():
    positions = st.session_state['frame_value_dict']
    if len(positions.keys()) > 2:
        st.session_state['frame_value_dict'] = {}  # clear all selection
        message = {'error': 'You have to select only two points to link the cell before division and after division'}

    else:
        cells_df = get_selected_cells_df(positions)

        # daughter 1 is the extension of mother track
        # daughter 2 is the new track
        mother = cells_df.iloc[0]
        daughter2 = cells_df.iloc[-1]

        daughter2['previous_x'] = mother['X']
        daughter2['previous_y'] = mother['Y']

        daughter1_df = st.session_state['df'][
            (st.session_state['df']['Frame'] > mother['Frame']) &
            (st.session_state['df']['family_name'].str.startswith(mother['family_name']))
            ]

        daughter2_df = st.session_state['df'][
            (st.session_state['df']['Frame'] > mother['Frame']) &
            (st.session_state['df']['family_name'].str.startswith(daughter2['family_name']))
            ]

        daughter1_df['family_name'] = daughter1_df['family_name'].apply(
            lambda x: x.replace(mother['family_name'], f"{mother['family_name']}1.")
        )

        daughter2_df['family_name'] = daughter2_df['family_name'].apply(
            lambda x: x.replace(daughter2['family_name'], f"{mother['family_name']}2.")
        )
       # st.write(mother['family_name'])

        daughter1_df['family_color'] = str(mother['family_color'])
        daughter1_df['family_color'] = daughter1_df['family_color'].apply(ast.literal_eval)

        daughter2_df['family_color'] = str(mother['family_color'])
        daughter2_df['family_color'] = daughter2_df['family_color'].apply(ast.literal_eval)

        st.session_state['df'].update(daughter1_df)
        st.session_state['df'].update(daughter2_df)

        redraw_images()
        message = {'success': 'Cell division was added successfully'}

    return message


def unlink_track_func():
    positions = st.session_state['frame_value_dict']
    cells_df = get_selected_cells_df(positions)
   # st.write(cells_df)
    if len(positions.keys()) > 2:
        st.session_state['frame_value_dict'] = {}  # clear all selection
        message = {'error': 'You have to select only two points to unlink'}

    else:
        new_track = st.session_state['df'][
            (st.session_state['df']['family'] == cells_df['family'].iloc[0]) &
            (st.session_state['df']['Frame'] > cells_df['Frame'].iloc[0])
            ]

        new_track.iloc[0, new_track.columns.get_loc('previous_x')] = 'nan'
        new_track.iloc[0, new_track.columns.get_loc('previous_y')] = 'nan'

        previous_family_name = cells_df['family_name'].iloc[0]
        previous_track_id = cells_df['track_id'].iloc[0]
        new_track_id = st.session_state['df']['track_id'].max() + 1

        new_track.loc[new_track['track_id'] == previous_track_id, 'track_id'] = new_track_id
        new_track['family'] = new_track_id
        new_track['family_name'] = new_track['family_name'].apply(
            lambda x: x.replace(previous_family_name, f'{new_track_id}.'))
        seq = list(range(0, 256))
        random_color = (random.choice(seq), random.choice(seq), random.choice(seq))
        new_track['family_color'] = str(random_color)
        new_track['family_color'] = new_track['family_color'].apply(ast.literal_eval)

        st.session_state['df'].update(new_track)
        st.session_state['df'] = st.session_state['df'].replace('nan', np.nan)


        redraw_images()
        message = {'success': 'Tracks unlinked successfully'}

    return message


def unlink_cells_func():
    positions = st.session_state['frame_value_dict']
    cells_df = get_selected_cells_df(positions)
    if len(positions.keys()) > 1:
        st.session_state['frame_value_dict'] = {}  # clear all selection
        message = {'error': 'You have to select only one point in one image to unlink'}

    else:  #só isolo tudo
       # st.write(cells_df)
        track_df = st.session_state['df'][
            (st.session_state['df']['Frame'] == st.session_state['current_frame']) &
            (st.session_state['df']['track_id'] == cells_df['track_id'].iloc[0])
            ]
       # st.write(track_df)
        track_df['previous_x'] = 'nan'
        track_df['previous_y'] = 'nan'
        max_track = st.session_state['df']['track_id'].max()
        new_tracks = [max_track + f for f in range(1, len(track_df) + 1)]
        track_df['track_id'] = new_tracks
        track_df['family_name'] = new_tracks
        seq = list(range(0, 256))
        random_colors = []
        for f in range(len(track_df)):
            random_colors.append(str((random.choice(seq), random.choice(seq), random.choice(seq))))
        track_df['family_color'] = random_colors
        track_df['family_color'] = track_df['family_color'].apply(ast.literal_eval)
       # st.write(track_df)

        st.session_state['df'].update(track_df)
        st.session_state['df'] = st.session_state['df'].replace('nan', np.nan)

        redraw_images()
        message = {'success': 'ok'}

    return message


def delete_track_func():
    positions = st.session_state['frame_value_dict']
    cells_df = get_selected_cells_df(positions)
    track = list(set(cells_df['track_id']))
    st.session_state['df'] = st.session_state['df'][~st.session_state['df']['track_id'].isin(track)]

    images_dict = {}
    for f in range(len(st.session_state['images_dict'].keys())):
        images_dict[f] = draw_track(st.session_state['df'], st.session_state['images_dict'][f].copy(), f)

    st.session_state['temp_images_dict'] = images_dict.copy()
    st.session_state['frame_value_dict'] = {}  # clear all selection

    return {'success': 'All selected tracks deleted!'}


def show_controllers():
    message = None
    with st.container(border=True):
        st.subheader(f" Current frame: {st.session_state['current_frame']}")
        st.write(f'nome_da_imagem_vai_aqui')
        clear_current = st.button('Clear selection', help='Clear current selection', use_container_width=True)
        if clear_current:
            del st.session_state['frame_value_dict'][st.session_state['current_frame']]
            message = {'success': 'Selection cleared!'}
        clear_all = st.button('Clear All', help='Clear all selections', use_container_width=True)
        if clear_all:
            st.session_state['frame_value_dict'] = {}
            message = {'success': 'All selectionn cleared!'}
        link = st.button('Link Tracks', help='Link cell Track', use_container_width=True)
        if link:
            message = link_tracks()
        cell_division = st.button('Cell division', help='Link cell to parent cell', use_container_width=True)
        if cell_division:
            message = cell_division_func()
        unlink = st.button('Unlink Tracks', help='Unlink Cell Track', use_container_width=True)
        if unlink:
            message = unlink_track_func()
        unlink_cells = st.button('Unlink Cells', help='Unlink two or more cells in an image', use_container_width=True)
        if unlink_cells:
            message = unlink_cells_func()
        delete = st.button('Delete Track', help='Delete cell track', use_container_width=True)
        if delete:
            message = delete_track_func()
        save = st.button('Save', help='Stores alterations', use_container_width=True)
        if save:
            st.session_state['saved_df'] = st.session_state['df'].copy()
            message = {'success': 'Progress saved'}
        undo = st.button('Undo', help='Undo alterations to the previous save', use_container_width=True)
        if undo:
            st.session_state['df'] = st.session_state['saved_df'].copy()
            redraw_images()
            message = {'success': 'Progress restored to the last save'}
        save_track = st.button("Complete", help='Finish editing', use_container_width=True)
        if 'save_track' not in st.session_state:
            st.session_state['save_track'] = True
        if save_track:
            st.session_state['save_track']=True
        if st.session_state['save_track']:
            path_to_save = st.text_input('Folder to save')
            salvamento = st.button('Salvar')
            if salvamento:
                st.session_state['saved_df'].to_csv(
                    os.path.join(path_to_save,'tabela_corrigida2.csv'))
                st.session_state['save_track'] = False
                st.rerun()
        save_images = st.button('Save Images', help='Stores images', use_container_width=True)
        if save_images:
            for f in range(len(st.session_state['images_dict'].keys())):
                img = draw_track(st.session_state['df'], st.session_state['images_dict'][f].copy(), f, True)
                imwrite(
                    '/media/luiza/DATA/Doutorado/forNMA/experimentos/exp_kaka/populacional 1/exp kaka populacional 1/results/dados para tracking/results/GREEN_D8_3 Registered/tracked_images'
                    + str(f) + '.jpeg', img)
            message = {'success': 'Images saved!'}
    return message


def show_slidebar():
    new_current_frame = st.slider("Frames", 0, len(image_paths) - 1, st.session_state['current_frame'],
                                  label_visibility='hidden')
    if st.session_state['current_frame'] != new_current_frame:
        st.session_state['current_frame'] = new_current_frame
        st.rerun()

    return


def show_message(message):
    if message is not None:
        if list(message.keys())[0] == 'success':
            st.success(message['success'])
        elif list(message.keys())[0] == 'error':
            st.warning(message['error'])

    return


##### df operations and opennign of images
if 'table_path' not in st.session_state and 'path' not in st.session_state:
    path = st.text_input('Path to images')
    table_path = st.text_input('Path to table')
    if st.button('Start'):
        st.session_state['path'] = path
        st.session_state['table_path'] = table_path
        st.rerun()

else:
    path = st.session_state['path']
    table_path = st.session_state['table_path']
    image_names = sorted(os.listdir(path))
    image_paths = [os.path.join(path, i) for i in image_names]
    df = pd.read_csv(table_path)
    df['family_name'] = df['family_name'].astype(str)

    if 'family_color' not in df.columns:
        df['family_color'] = None
        for family, df_family in df.groupby('family'):
            seq = list(range(0, 256))
            random_color = (random.choice(seq), random.choice(seq), random.choice(seq))
            df.loc[df['family'] == family, 'family_color'] = [str(random_color)] * len(df_family)
    df['family_color'] = df['family_color'].apply(ast.literal_eval)

    if 'saved_df' not in st.session_state:
        st.session_state['saved_df'] = df
        st.session_state['df'] = df.copy()
    #####
    ## creations of session states ###
    if 'images_dict' not in st.session_state:
        image_names = sorted(os.listdir(path))
        image_paths = [os.path.join(path, i) for i in image_names]
        images = [cv.cvtColor(imread(f), cv.COLOR_BGR2RGB) for f in image_paths]

        temp_images_dict = {}
        images_dict = {}
        for f in range(len(images)):
            temp_images_dict[f] = draw_track(df, images[f].copy(), f)
            images_dict[f] = images[f]
        st.session_state['temp_images_dict'] = temp_images_dict
        st.session_state['images_dict'] = images_dict

    if 'image_shape' not in st.session_state:
        st.session_state['image_shape'] = list(st.session_state['images_dict'].values())[0].shape

    if 'current_frame' not in st.session_state:
        st.session_state['current_frame'] = 0

    if 'frame_value_dict' not in st.session_state:
        st.session_state['frame_value_dict'] = {}

    ## creations of session states ###
    col1, col2, col3, col4 = st.columns([1, 6, 1, 2])

    with col1:
        disable_previous = True if st.session_state['current_frame'] == 0 else False
        previous = st.button('←', help='Previous image', use_container_width=True, disabled=disable_previous)
        if previous:
            st.session_state['current_frame'] = st.session_state['current_frame'] - 1 if st.session_state[
                                                                                             'current_frame'] > 0 else 0

    with col3:
        disable_next = True if st.session_state['current_frame'] == len(image_paths) - 1 else False
        next_img = st.button('→', help='Next image', use_container_width=True, disabled=disable_next)
        if next_img:
            st.session_state['current_frame'] = st.session_state['current_frame'] + 1 if st.session_state[
                                                                                             'current_frame'] < len(
                image_paths) - 1 else len(image_paths) - 1

    with col4:
        message = show_controllers()

    frame = st.session_state['current_frame']
    if frame in st.session_state['frame_value_dict'].keys():
        image = draw_x(st.session_state['temp_images_dict'][frame].copy(), st.session_state['frame_value_dict'][frame])
    else:
        image = st.session_state['temp_images_dict'][frame]

    with col2:
        with st.container(border=None):
            value = streamlit_image_coordinates(image, use_column_width="always", key="local")

    if 'value' not in st.session_state:
        st.session_state['value'] = None

    if value != st.session_state['value']:
        st.session_state['frame_value_dict'][frame] = value
        st.session_state['value'] = value
        st.rerun()

    st.session_state['value'] = value

    with col2:
        show_slidebar()
        show_message(message)
