"""
Interface/custom_widgets/auto_widgets/auto_slider.py - contains a function that returns
the proper slider type (meant to look like a class when using).
"""
from __future__ import annotations

from typing import Type

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from ..extended_widgets.double_slider_widget import DoubleSlider


def AutoSlider(
        dtype: Type[int, float],
        *args,
        **kwargs,
) -> qtw.QSlider | DoubleSlider:
    """Returns the proper Slider instance, depending on the dtype parameter."""
    if dtype == int:
        return qtw.QSlider(*args, **kwargs, orientation=qtc.Qt.Horizontal)
    elif dtype == float:
        return DoubleSlider(*args, **kwargs, orientation=qtc.Qt.Horizontal)
    else:
        raise TypeError(f"Invalid dtype: {dtype}")
