"""helpers/tooltip_layout.py - module defining a widget with a tooltip button."""
from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import AutoSpinBox, SliderSpinBox


class ToolTipWidget(qtw.QWidget):
    """Widget containing a tooltip text, an informative help button to the left, and an optional checkbox at the top."""
    valueChanged = qtc.Signal(object)  # int | float

    def __init__(
            self,
            numeric_limits: dict[str, int | float] = None,
            include_slider: bool = False,
            label_as_checkbox: bool = False,
            parent: qtw.QWidget = None,
    ) -> None:
        """Adds the widget to the Layout, including a tooltip."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Optional checkbox or label
        if label_as_checkbox is True:
            self.label = qtw.QCheckBox("")
            self.label.stateChanged.connect(widget.setEnabled)  # noqa
        else:
            self.label = qtw.QLabel("")
        layout.addWidget(self.label, 0, 0, 1, 2)

        # Widget
        numeric_limits = numeric_limits or {}
        if include_slider is True:
            self.widget = SliderSpinBox(**numeric_limits)
        else:
            self.widget = AutoSpinBox(**numeric_limits)
        layout.addWidget(self.widget, 1, 1, 1, 1)

    def set_tooltip(
            self,
            tooltip_text: str,
    ) -> None:
        """Sets the tooltip text onto the widget."""
        self.widget.setToolTip(tooltip_text)

    def set_label(
            self,
            label_text: str,
    ) -> None:
        """Sets the label text."""
        self.label.setText(label_text)

    def on_spinbox_value_changed(
            self,
            new_value: int | float,
    ) -> None:
        """Emits a signal whenever the spinbox value changes."""
        self.valueChanged.emit(new_value)


# class ToolTipSpinBox(ToolTipWidget):
#     """Widget representing a ToolTipWidget with a spinbox as its main widget, which optionally includes a slider."""
#     valueChanged = qtc.Signal(object)  # int | float
#
#     def __init__(
#             self,
#             numeric_limits: dict[str, int | float] = None,
#             include_slider: bool = False,
#             label_as_checkbox: bool = False,
#             parent: qtw.QWidget = None,
#     ) -> None:
#         """Initializes a ToolTipSpinBox instance."""
#         numeric_limits = numeric_limits or {}
#         if include_slider is True:
#             widget = SliderSpinBox(**numeric_limits)
#         else:
#             widget = AutoSpinBox(**numeric_limits)
#         super().__init__(widget=widget, label_as_checkbox=label_as_checkbox, parent=parent)
#         widget.valueChanged.connect(self.on_spinbox_value_changed)  # noqa
#
#     def on_spinbox_value_changed(
#             self,
#             new_value: int | float,
#     ) -> None:
#         """Emits a signal whenever the spinbox value changes."""
#         self.valueChanged.emit(new_value)
