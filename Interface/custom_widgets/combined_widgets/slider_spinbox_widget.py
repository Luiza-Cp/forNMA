"""
Interface/custom_widgets/combined_widgets/slider_spinbox_widget.py - module containing SliderSpinBoxWidget,
combining a Slider and a Spinbox into a single widget.
"""
from __future__ import annotations

from typing import Type

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import DoubleSlider, AutoSlider, AutoSpinBox


class SliderSpinBoxWidget(qtw.QWidget):
    """
    Class representing a widget containing a slider widget and a spinbox,
    which both displays and selects the current widget value. The dtype parameter determines
    if the SliderSpinBox holds an integer or float value.
    """
    valueChanged = qtc.pyqtSignal(object)  # int | float

    def __init__(
            self,
            dtype: Type[int] | Type[float] = int,
            minimum: int = 0,
            maximum: int = 10,
            singleStep: int = 1,
            value: int = 5,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a SliderSpinBoxWidget instance."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Get proper classes
        Slider = qtw.QSlider if dtype == int else DoubleSlider

        # Slider
        self.slider = AutoSlider(
            dtype=dtype,
            minimum=minimum,
            maximum=maximum,
            singleStep=singleStep,
            value=value,
        )
        layout.addWidget(self.slider)

        # Spinbox
        self.spinbox = AutoSpinBox(
            dtype=dtype,
            minimum=minimum,
            maximum=maximum,
            singleStep=singleStep,
            value=value,
        )
        layout.addWidget(self.spinbox)

        # Method aliases
        self.value = self.slider.value
        self.setValue = self.slider.setValue

        # Connect slider to spinbox
        if isinstance(self.slider, DoubleSlider):
            self.slider.doubleValueChanged.connect(self.on_value_changed)
        else:  # qtw.QSlider instance
            self.slider.valueChanged.connect(self.on_value_changed)
        self.spinbox.valueChanged.connect(self.on_value_changed)

    def on_value_changed(
            self,
            new_value: int | float,
    ) -> None:
        """Updates the slider value whenever the spinbox value changes (and vice-versa), then emits it."""
        if (sender := self.sender()) == self.slider:
            self.spinbox.blockSignals(True)
            self.spinbox.setValue(new_value)
            self.spinbox.blockSignals(False)
        elif sender == self.spinbox:
            self.slider.blockSignals(True)
            self.slider.setValue(new_value)
            self.slider.blockSignals(False)
        self.valueChanged.emit(new_value)
