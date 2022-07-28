"""
widgets/auto_slider.py - contains a function that can returns the proper slider type
(meant to look like a class when using).
"""
from __future__ import annotations

from typing import Type

from PySide6 import QtWidgets as qtw

from Interface.custom_widgets import DoubleSlider


def AutoSlider(
        dtype: Type[int, float],
        *args,
        **kwargs,
) -> qtw.QSlider | DoubleSlider:
    """Returns the proper Slider instance, depending on the dtype parameter."""
    if dtype == int:
        return qtw.QSlider(*args, **kwargs)
    elif dtype == float:
        return DoubleSlider(*args, **kwargs)
    else:
        raise TypeError(f"Invalid dtype: {dtype}")
