"""fornma_parameters/widgets.py - module defining the interface between forNMA parameters and its widgets."""
from __future__ import annotations

from PySide6 import QtWidgets as qtw

from Interface import ForNMAParameter
from Interface.custom_widgets import ToolTipSpinBox
from Interface.fornma_parameters import get_fornma_data_type


def ForNMAWidget(
        fornma_id: str,
        *args,
        **kwargs,
) -> _ForNMAWidget:
    """Returns a properly structured PySide Widget for each forNMA parameter."""
    if (dtype := get_fornma_data_type(fornma_id=fornma_id)) in (int, float):
        return _ForNMANumericWidget(fornma_id=fornma_id, *args, **kwargs)
    elif dtype == bool:
        return _ForNMABoolWidget(fornma_id=fornma_id)
    elif dtype == str:
        return _ForNMAStringWidget(fornma_id=fornma_id)
    else:
        raise ValueError(f'Bad dtype found: {dtype}')


class _ForNMAWidget:
    """Class representing a forNMA parameter encapsulated in a PySide Widget."""
    @property
    def widget(self) -> qtw.QWidget:
        """Returns the PySide6 widget."""
        return self._widget

    @property
    def param(self) -> ForNMAParameter:
        """Returns the ForNMAParameter."""
        return self._fornma_parameter


class _ForNMANumericWidget(_ForNMAWidget):
    """Class representing a forNMA parameter encapsulated in a numeric PySide Widget."""
    def __init__(
            self,
            fornma_id: str,
            include_slider: bool = True,
    ) -> None:
        """Initializes a ForNMANumericWidget instance."""
        super().__init__()
        self._fornma_parameter = ForNMAParameter(fornma_id=fornma_id)
        self._widget = ToolTipSpinBox(include_slider=include_slider)
        self._widget.set_label(self._fornma_parameter.label)
        self._widget.set_tooltip(self._fornma_parameter.tooltip_text)
        self._widget.valueChanged.connect(self._fornma_parameter.set_value)


class _ForNMABoolWidget(_ForNMAWidget):
    """Class representing a forNMA parameter encapsulated in a boolean PySide Widget."""
    def __init__(
            self,
            fornma_id: str,
    ) -> None:
        """Initializes a ForNMANumericWidget instance."""
        super().__init__()
        self._fornma_parameter = ForNMAParameter(fornma_id=fornma_id)
        self._widget = qtw.QCheckBox()
        self._widget.setText(self._fornma_parameter.label)
        self._widget.setToolTip(self._fornma_parameter.tooltip_text)
        self._widget.toggled.connect(self._fornma_parameter.set_value)  # noqa


class _ForNMAStringWidget(_ForNMAWidget):
    """Class representing a forNMA parameter encapsulated in a string PySide Widget."""
    def __init__(
            self,
            fornma_id: str,
    ) -> None:
        """Initializes a ForNMANumericWidget instance."""
        super().__init__()
        self._fornma_parameter = ForNMAParameter(fornma_id=fornma_id)
        self._widget = qtw.QComboBox()
        self._widget.setToolTip(self._fornma_parameter.tooltip_text)
