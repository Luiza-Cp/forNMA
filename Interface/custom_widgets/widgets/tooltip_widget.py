"""helpers/tooltip_layout.py - module defining a widget with a tooltip button."""
from __future__ import annotations

from PySide6 import QtWidgets as qtw

from Interface import ForNMAParameter
from Interface.custom_widgets import AutoSpinBox, HelpButton, SliderSpinBox


class ToolTipWidget(qtw.QWidget):
    """Widget containing a tooltip text, an informative help button to the left, and an optional checkbox at the top."""
    def __init__(
            self,
            widget: qtw.QWidget,
            fornma_id: str = "",
            top_label: str = None,
            label_as_checkbox: bool = False,
            parent: qtw.QWidget = None,
    ) -> None:
        """Adds the widget to the Layout, including a tooltip."""
        super().__init__(parent=parent)
        fornma_params = ForNMAParameter(fornma_id)

        # Layout
        layout = qtw.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Optional checkbox or label
        self.checkbox = self.label = None
        if top_label is None:
            # No label above
            widget_row = 0
        else:  # top_label is not None
            if label_as_checkbox is True:
                # Checkbox that activates the widget
                self.checkbox = qtw.QCheckBox(top_label)
                self.checkbox.stateChanged.connect(widget.setEnabled)  # noqa
                layout.addWidget(self.checkbox, 0, 0, 1, 2)
                widget_row = 1
            else:  # label_as_checkbox is False:
                # Regular label with no checkbox
                self.label = qtw.QLabel(top_label)
                layout.addWidget(self.label, 0, 0, 1, 2)
                widget_row = 1

        # Help Button
        self.help_button = HelpButton(fornma_id=fornma_id)
        layout.addWidget(self.help_button, widget_row, 0, 1, 1)

        # Widget
        self.widget = widget
        self.widget.setToolTip(fornma_params.tooltip_text)
        layout.addWidget(self.widget, widget_row, 1, 1, 1)


class ToolTipSpinBox(ToolTipWidget):
    """Widget representing a ToolTipWidget with a spinbox as its main widget, which optionally includes a slider."""
    def __init__(
            self,
            fornma_id: str = "",
            include_slider: bool = False,
            label_as_checkbox: bool = False,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ToolTipSpinBox instance."""
        fornma_params = ForNMAParameter(fornma_id)
        if include_slider is True:
            widget = SliderSpinBox(**fornma_params.numeric_limits)
        else:
            widget = AutoSpinBox(**fornma_params.numeric_limits)
        ToolTipWidget.__init__(
            self,
            widget=widget,
            fornma_id=fornma_id,
            top_label=fornma_params.label,
            label_as_checkbox=label_as_checkbox,
            parent=parent,
        )
