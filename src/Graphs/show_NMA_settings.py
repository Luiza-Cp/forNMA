from matplotlib import pyplot as plt
import pickle
import os
import matplotlib

matplotlib.use('TkAgg')


def show_nma_settings():
    """ Shows plot of stored NMA settings"""
    if not os.path.isfile('control_parameters.pickle'):
        raise Exception("The NMA controls were not set. Run 'NMA control' command before proceeding.")

    with open('control_parameters.pickle', 'rb') as f:
        parameters = pickle.load(f)
        control_name = parameters['name']
        sd_area = parameters['sd_area']
        sd_NII = parameters['sd_NII']
        fig = parameters['fig']
        dummy = plt.figure()
        new_manager = dummy.canvas.manager
        new_manager.canvas.figure = fig
        fig.set_canvas(new_manager.canvas)
        plt.show()

        return print(
            f'Your current control configuration was defined with table named {control_name} with an area standard '
            f'deviation of {sd_area} and NII standard deviation of {sd_NII}.\nIf you need other control settings, '
            f'please run "NMA control" command again.')


if __name__ == '__main__':
    show_nma_settings()
