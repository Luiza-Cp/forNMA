from typing import Tuple, Union

from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa

from src.interface.helpers.double_slider import DoubleSlider


# TOREVIEW: better name for this class!
class SliderWidgets:
    """
    Creates a slider widget coupled with a spinbox showing its current value, and a checkbox that enables and
    disables both widgets. Supports both integer and float data types.
    """
    valid_dtypes = [
        'int',
        'double',
        'float',
    ]

    def __init__(
            self,
            dtype: str,
            label: str,
            slider_name: str,
            minimum: float,
            maximum: float,
            singleStep: float,
            value: float,
    ) -> None:
        """Initializes a SliderWidgets instance."""
        self.validate_dtype(dtype=dtype)
        self.dtype = dtype
        if self.is_integer():
            Slider = qtw.QSlider
            SpinBox = qtw.QSpinBox
        else:
            Slider = DoubleSlider
            SpinBox = qtw.QDoubleSpinBox
        self.slider = Slider(objectName=slider_name, enabled=False, orientation=qtc.Qt.Horizontal)
        self.spinbox = SpinBox(enabled=False)  # noqa
        for widget in (self.slider, self.spinbox):  # setting constructor attributes for DoubleSlider is messy
            widget.setMinimum(minimum)
            widget.setMaximum(maximum)
            widget.setSingleStep(singleStep)
            widget.setValue(value)
        self.checkbox = qtw.QCheckBox(label, checked=False)  # noqa

        # Sets connections across the three widgets
        self.checkbox.toggled.connect(self.slider.setEnabled)
        self.checkbox.toggled.connect(self.spinbox.setEnabled)
        if self.is_integer():  # Appropriate signal is valueChanged
            self.slider.valueChanged.connect(self.spinbox.setValue)
        else:  # Appropriate signal is doubleValueChanged
            self.slider.doubleValueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)

    def items(self) -> Tuple[qtw.QSlider, qtw.QCheckBox, Union[qtw.QSpinBox, qtw.QDoubleSpinBox]]:
        """Returns a tuple containing the slider, checkbox and spinbox widgets."""
        return self.slider, self.checkbox, self.spinbox

    def is_integer(self) -> bool:
        """Returns whether the SliderWidgets instance represents an integer or float data type."""
        return self.dtype == 'int'

    def validate_dtype(
            self,
            dtype: str,
    ) -> None:
        """Raises a ValueError if the SliderWidgets instance was initialized with an invalid dtype argument."""
        if dtype not in self.valid_dtypes:
            raise ValueError(f'dtype must be one of {self.valid_dtypes}, not {dtype}')
