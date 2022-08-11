"""fornma_parameters/fornma_widget.py - module defining the interface between forNMA parameters and its widgets."""
from __future__ import annotations

from typing import Type

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface import ForNMAParameter
from Interface.custom_widgets import AutoSpinBox, ForNMAHelpButton, SliderSpinBoxWidget
from Interface.fornma_parameters import get_fornma_dtype


def ForNMAWidget(
        fornma_id: str,
        add_slider: bool = False,
        add_help: bool = True,
) -> _ForNMANumericWidget | _ForNMAStringWidget | _ForNMABoolWidget:
    """Returns a properly structured PySide Widget for each forNMA parameter."""
    dtype = get_fornma_dtype(fornma_id=fornma_id)
    fornma_parameter = ForNMAParameter(fornma_id=fornma_id)
    fornma_help_button = None
    if add_help is True:
        fornma_help_button = ForNMAHelpButton(fornma_id=fornma_id)
    if dtype in (int, float):
        widget = _ForNMANumericWidget(
            name=fornma_id,
            dtype=dtype,
            label=fornma_parameter.label,
            help_button=fornma_help_button,
            limits=fornma_parameter.numeric_limits,
            add_slider=add_slider,
        )
    elif dtype == str:
        widget = _ForNMAStringWidget(
            name=fornma_id,
            label=fornma_parameter.label,
            help_button=fornma_help_button,
            options=fornma_parameter.text_options,
        )
    elif dtype == bool:
        widget = _ForNMABoolWidget(
            name=fornma_id,
            label="",
            checkbox_text=fornma_parameter.label,
            help_button=fornma_help_button,
        )
    else:
        raise ValueError(f'Invalid dtype: {dtype}')
    widget.setToolTip(fornma_parameter.tooltip_text)
    return widget


class _BaseForNMAWidget(qtw.QWidget):
    """Base class for forNMA parameter."""
    valueChanged = qtc.Signal(object)  # int | float | str | bool

    def __init__(
            self,
            name: str = "",
            label: str = "",
            help_button: qtw.QWidget = None,
            parent: qtw.QWidget = None
    ) -> None:
        """Initializes a BaseForNMAWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QGridLayout()
        self.setLayout(layout)

        self.setObjectName(name)
        self._current_row = 0

        if label:
            self.label = qtw.QLabel(label)
            layout.addWidget(self.label, self._current_row, 0, 1, 2)
            self._current_row += 1

        if help_button is not None:
            self.help_button = help_button
            layout.addWidget(self.help_button, self._current_row, 0, 1, 1)

    def _on_widget_value_changed(
            self,
            new_value: object,
    ) -> None:
        """Emits the new values through the valueChanged slot."""
        self.valueChanged.emit(new_value)


class _ForNMANumericWidget(_BaseForNMAWidget):
    """Class representing a numeric( integer or float) forNMA parameter."""
    def __init__(
            self,
            name: str = "",
            dtype: Type[int, float] = int,
            label: str = "",
            help_button: qtw.QWidget = None,
            limits: dict = None,
            add_slider: bool = False,
            parent: qtw.QWidget = None
    ) -> None:
        """Initializes a forNMANumericWidget instance."""
        super().__init__(name=name, label=label, help_button=help_button, parent=parent)
        layout: qtw.QGridLayout = self.layout()

        Widget = SliderSpinBoxWidget if add_slider is True else AutoSpinBox
        self.widget = Widget(dtype=dtype, **limits)
        layout.addWidget(self.widget, self._current_row, 1, 1, 1)
        self.widget.valueChanged.connect(self._on_widget_value_changed)

        # Method aliases
        self.value = self.widget.value
        self.setValue = self.widget.setValue


class _ForNMAStringWidget(_BaseForNMAWidget):
    """Class representing a string forNMA parameter."""
    def __init__(
            self,
            name: str = "",
            label: str = "",
            help_button: qtw.QWidget = None,
            options: list = None,
            parent: qtw.QWidget = None
    ) -> None:
        """Initializes a _ForNMAFloatWidget instance."""
        super().__init__(name=name, label=label, help_button=help_button, parent=parent)
        layout: qtw.QGridLayout = self.layout()

        self.widget = qtw.QComboBox()
        for option in options:
            self.widget.addItem(option)
        self.widget.currentTextChanged.connect(self._on_widget_value_changed)  # noqa
        layout.addWidget(self.widget, self._current_row, 1, 1, 1)

        # Method aliases
        self.setCurrentText = self.widget.setCurrentText
        self.addItem = self.widget.addItem
        self.removeItem = self.widget.removeItem
        self.currentIndex = self.widget.currentIndex
        self.value = self.widget.currentText


class _ForNMABoolWidget(_BaseForNMAWidget):
    """Class representing a bool forNMA parameter."""
    def __init__(
            self,
            name: str = "",
            label: str = "",
            help_button: qtw.QWidget = None,
            checkbox_text: str = "",
            parent: qtw.QWidget = None
    ) -> None:
        """Initializes a _ForNMAFloatWidget instance."""
        super().__init__(name=name, label=label, help_button=help_button, parent=parent)
        layout: qtw.QGridLayout = self.layout()

        self.widget = qtw.QCheckBox(checkbox_text)
        layout.addWidget(self.widget, self._current_row, 1, 1, 1)
        self.widget.stateChanged.connect(self._on_widget_value_changed)  # noqa

        # Method aliases
        self.value = self.widget.isChecked
        self.setChecked = self.widget.setChecked
