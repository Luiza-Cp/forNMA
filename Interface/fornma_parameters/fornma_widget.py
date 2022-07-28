"""fornma_parameters/fornma_widget.py - module defining the interface between forNMA parameters and its widgets."""
from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface import ForNMAParameter
from Interface.custom_widgets import SliderSpinBox, ForNMAHelpButton
from Interface.custom_widgets.widgets.double_slider_widget import DoubleSliderSpinBox
from Interface.fornma_parameters import get_fornma_dtype


def ForNMAWidget(
        fornma_id: str,
        add_slider: bool = False,
) -> _ForNMAIntWidget | _ForNMAFloatWidget | _ForNMAStringWidget | _ForNMABoolWidget:
    """Returns a properly structured PySide Widget for each forNMA parameter."""
    dtype = get_fornma_dtype(fornma_id=fornma_id)
    fornma_parameter = ForNMAParameter(fornma_id=fornma_id)
    fornma_help_button = ForNMAHelpButton(fornma_id=fornma_id)
    if dtype == int:
        widget = _ForNMAIntWidget(
            name=fornma_id,
            label=fornma_parameter.label,
            help_button=fornma_help_button,
            limits=fornma_parameter.numeric_limits,
            add_slider=add_slider,
        )
    elif dtype == float:
        widget = _ForNMAFloatWidget(
            name=fornma_id,
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
            label=fornma_parameter.label,
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

        self.help_button = help_button
        layout.addWidget(self.help_button, self._current_row, 0, 1, 1)

    def _on_widget_value_changed(
            self,
            new_value: int,
    ) -> None:
        """Emits the new values through the valueChanged slot."""
        self.valueChanged.emit(new_value)


class _ForNMAIntWidget(_BaseForNMAWidget):
    """Class representing an integer forNMA parameter."""
    def __init__(
            self,
            name: str = "",
            label: str = "",
            help_button: qtw.QWidget = None,
            limits: dict = None,
            add_slider: bool = False,
            parent: qtw.QWidget = None
    ) -> None:
        """Initializes a forNMANumericWidget instance."""
        super().__init__(name=name, label=label, help_button=help_button, parent=parent)
        layout: qtw.QGridLayout = self.layout()

        self.widget = SliderSpinBox(**limits) if add_slider is True else qtw.QSpinBox(**limits)
        layout.addWidget(self.widget, self._current_row, 1, 1, 1)
        self.widget.valueChanged.connect(self._on_widget_value_changed)

        # Method aliases
        self.value = self.widget.value


class _ForNMAFloatWidget(_BaseForNMAWidget):
    """Class representing a float forNMA parameter."""
    def __init__(
            self,
            name: str = "",
            label: str = "",
            help_button: qtw.QWidget = None,
            limits: dict = None,
            add_slider: bool = False,
            parent: qtw.QWidget = None
    ) -> None:
        """Initializes a _ForNMAFloatWidget instance."""
        super().__init__(name=name, label=label, help_button=help_button, parent=parent)
        layout: qtw.QGridLayout = self.layout()

        self.widget = DoubleSliderSpinBox(**limits) if add_slider is True else qtw.QDoubleSpinBox(**limits)
        layout.addWidget(self.widget, self._current_row, 1, 1, 1)
        self.widget.valueChanged.connect(self._on_widget_value_changed)

        # Method aliases
        self.value = self.widget.value


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


# class _ForNMAWidget:
#     """Class representing a forNMA parameter encapsulated inside a PySide Widget."""
#     valueChanged = qtc.Signal(object)
#
#     def __init__(
#             self,
#             fornma_id: str,
#             add_slider: bool = False,
#     ) -> None:
#         """Initializes a ForNMAWidget instance."""
#         self.fornma_id = fornma_id
#         self._fornma_parameter = ForNMAParameter(fornma_id=self.fornma_id)
#         self._help_button = ForNMAHelpButton(fornma_id=self.fornma_id)
#         self._widget = self._get_widget(add_slider=add_slider)
#         self._widget.valueChanged.connect(self.valueChanged)  # noqa
#         # self.connect()
#
#     def _get_widget(
#             self,
#             add_slider: bool,
#     ) -> qtw.QWidget:
#         """Returns the proper widget for the given forNMA ID."""
#         dtype = get_fornma_dtype(fornma_id=self.fornma_id)
#         if dtype == int:
#             widget = _ForNMAIntWidget(
#                 label=self._fornma_parameter.label,
#                 help_button=self._help_button,
#                 add_slider=add_slider,
#                 limits=self._fornma_parameter.numeric_limits,
#             ).widget
#         elif dtype == float:
#             widget = _ForNMAFloatWidget(
#                 label=self._fornma_parameter.label,
#                 help_button=self._help_button,
#                 add_slider=add_slider,
#                 limits=self._fornma_parameter.numeric_limits,
#             ).widget
#         elif dtype == str:
#             widget = _ForNMAStringWidget(
#                 label=self._fornma_parameter.label,
#                 help_button=self._help_button,
#                 options=['foo', 'bar'],
#             ).widget
#         elif dtype == bool:
#             widget = _ForNMABoolWidget(
#                 label="",
#                 help_button=self._help_button,
#                 checkbox_text=self._fornma_parameter.label,
#             ).widget
#         else:
#             raise ValueError(f'Invalid dtype: {dtype}')
#         widget.setToolTip(self)
#         return widget
