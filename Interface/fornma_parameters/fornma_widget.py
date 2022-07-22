"""fornma_parameters/fornma_widget.py - module defining the interface between forNMA parameters and its widgets."""
from __future__ import annotations

from PySide6 import QtWidgets as qtw

from Interface import ForNMAParameter
from Interface.custom_widgets import ToolTipSpinBox


def ForNMAWidget(
        fornma_id: str,
        *args,
        **kwargs,
) -> qtw.QWidget:
    """Returns a properly structured PySide Widget for each forNMA parameter."""
    fornma_parameter = ForNMAParameter(fornma_id=fornma_id)
    if (dtype := fornma_parameter.dtype) in (int, float):
        widget = ToolTipSpinBox(fornma_parameter.numeric_limits, *args, **kwargs)
        widget.set_label(fornma_parameter.label)
        widget.valueChanged.connect(fornma_parameter.set_value)
    elif dtype == bool:
        widget = qtw.QCheckBox()
        widget.setText(fornma_parameter.label)
        widget.toggled.connect(fornma_parameter.set_value)  # noqa
    elif dtype == str:
        widget = qtw.QComboBox()
    else:
        raise ValueError(f'Bad dtype {dtype} found in forNMA parameter {fornma_parameter}')
    widget.setToolTip(fornma_parameter.tooltip_text)

    return widget


class _ForNMAWidget:
    """Class representing a forNMA parameter encapsulated inside a PySide Widget."""
    def __init__(
            self,
            fornma_id: str,
            widget: qtw.QWidget = None,
    ) -> None:
        """Initializes a ForNMAWidget instance."""
        super().__init__()
        self.fornma_parameter = ForNMAParameter(fornma_id=fornma_id)
        self.widget = widget or qtw.QWidget()
        self.connect()

    def connect(self) -> None:
        """Sets up the connection between the widget and the forNMA parameter."""
        self.widget.setToolTip(self.fornma_parameter.tooltip_text)
