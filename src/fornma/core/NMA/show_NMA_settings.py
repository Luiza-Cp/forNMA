from matplotlib import pyplot as plt
import pickle
import os
import matplotlib
from pathlib import Path
matplotlib.use('TkAgg')

HERE = Path(__file__).resolve().parent
PICKLE_PATH = HERE / "control_parameters.pickle"   # 2) caminho estável


def show_nma_settings():
    """ Shows plot of stored NMA settings"""
    if not os.path.isfile('control_parameters.pickle') and not PICKLE_PATH.exists():
        return print("The NMA settings were not defined. Run 'NMA settings' command before proceeding.")

    with open(PICKLE_PATH, 'rb') as f:
        parameters = pickle.load(f)
        control_name = parameters.get('name')
        sd_area = parameters.get('sd_area')
        sd_NII = parameters.get('sd_NII')
        fig = parameters.get('fig')
        area_bottom = parameters["h_y_down"][0]
        area_top = parameters["h_y_up"][0]
        sr = f'Area < {area_bottom}\nNII < {parameters["v_downx"][0]}'
        s = f'Area < {area_bottom}\n{parameters["v_downx"][0]} > NII > {parameters["v_downx2"][0]}'
        si = f'Area < {area_bottom}\nNII > {parameters["v_downx2"][0]}'
        n = f'{area_bottom} < Area < {area_top}\nNII < {parameters["v_midx"][0]}'
        i = f'{area_bottom} < Area < {area_top}\nNII >  {parameters["v_midx"][0]}'
        l = f'Area > {area_top}\nNII < {parameters["v_upx"][0]}'
        li = f'Area > {area_top}\nNII > {parameters["v_upx"][0]}'

        if fig is not None:
            dummy = plt.figure()
            new_manager = dummy.canvas.manager
            new_manager.canvas.figure = fig
            fig.set_canvas(new_manager.canvas)
            plt.show()
        else:
            print("No stored figure found in settings; skipping plot display.")

        return print(
            f'Your current control configuration was defined with table named {control_name} with an area standard '
            f'deviation of {sd_area} and NII standard deviation of {sd_NII}.\n'
            f'The threshold coordinates are:\n'
            f'Small Regular:\n{sr}\n'
            f'Small:\n{s}\n'
            f'Small Irregular:\n{si}\n'
            f'Normal:\n{n}\n'
            f'Irregular:\n{i}\n'
            f'Large Regular:\n{l}\n'
            f'Large Irregular:\n{li}\n'
            f'If you need other control settings, '
            f'please run "NMA control" command again.')


if __name__ == '__main__':
    show_nma_settings()
