import pandas as pd
from typing import List, Optional, Tuple
import os
import numpy as np
from math import pi
from scipy import stats
import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib.patches as mp



def check_column_names(df: pd.DataFrame,
                       name: str):
    """ Checks if DataFrame columns rare the ones expected by forNMA. If not, raises an error."""

    columns = ['Frame', 'Cell', 'X', 'Y', 'Area', 'Perimeter', 'Aspect', 'Extent', 'Roundness', 'Radius_ratio', 'NII',
               'FitEllipse_X','FitEllipse_Y', 'FitEllipse_a', 'FitEllipse_b', 'FitEllipse_angle', 'Condition',
               'Overtime']

    if not all(item in df.columns for item in columns):
        raise ValueError(
            'The table ' + name + 'does not have forNMA output column names. Rename your columns according to forNMA '
                                  'standard outputs and try again.')

    return None


def NMA_control(path: str,
                sd: Optional[float] == 2.0,
                headless: bool == False):

    # vou refazer isso tudo
    # 1. criar novo env pra versão pypi
    # 2. copio a classe NMA pra cá e usoelapra criar os controles, apagando as funções e partes não necessárias, mas
    # mantendo a classe
    # 3. salvo os valores importantes em um dic e mando via pickle para uma temp
    # isso vai ser usado para criar a segunda função
    """Adjust tables and controls for NMA plots. ...."""
    df = pd.read_csv(path)
    name = os.basename(path)
    check_column_names(df, name)


















