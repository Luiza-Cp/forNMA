"""
Interface/custom_widgets/auto_widgets/auto_spinbox.py - contains a function that returns
the proper spinbox type (meant to look like a class when using).
"""
from __future__ import annotations

from typing import Type

from PySide6 import QtWidgets as qtw


def AutoSpinBox(
        dtype: Type[int, float],
        *args,
        **kwargs,
) -> qtw.QSpinBox | qtw.QDoubleSpinBox:
    """Returns the proper SpinBox instance, depending on the dtype parameter."""
    if dtype == int:
        return qtw.QSpinBox(*args, **kwargs)
    elif dtype == float:
        return qtw.QDoubleSpinBox(*args, **kwargs)
    else:
        raise TypeError(f"Invalid dtype: {dtype}")
