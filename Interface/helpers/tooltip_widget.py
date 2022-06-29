"""helpers/tooltip_layout.py - module defining a widget with a tooltip button."""
from __future__ import annotations

from PySide6 import QtGui as qtg, QtWidgets as qtw

from Interface.helpers import SliderSpinBox, AutoSpinBox


class ToolTipWidget(qtw.QWidget):
    """Widget containing an informative tooltip/info button to the left, and an optional checkbox at the top."""

    def __init__(
            self,
            widget: qtw.QWidget,
            tooltip_name: str = "",
            checkbox: bool = False,
            top_label: str = "",
            parent: qtw.QWidget = None,
    ) -> None:
        """Adds the widget to the Layout, including a tooltip."""
        super().__init__(parent=parent)

        # Tooltip data
        self.tooltip_name = tooltip_name
        self.tooltip_text = self.get_tooltip_text()

        # Layout
        layout = qtw.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Optional checkbox or label
        self.checkbox = self.label = None
        if top_label is not None and checkbox is True:  # Checkbox that activates the widget
            self.checkbox = qtw.QCheckBox(top_label)
            self.checkbox.stateChanged.connect(widget.setEnabled)  # noqa
            layout.addWidget(self.checkbox, 0, 0, 1, 2)
            widget_row = 1
        elif checkbox is False:  # Regular label with no checkbox
            self.label = qtw.QLabel(top_label)
            layout.addWidget(self.label, 0, 0, 1, 2)
            widget_row = 1
        else:  # No label above
            widget_row = 0

        # Tooltip button
        self.tooltip_button = qtw.QToolButton()
        self.tooltip_button.setIcon(self.get_tooltip_icon())
        self.tooltip_button.setToolTip(self.tooltip_text)
        self.tooltip_button.clicked.connect(self.display_tooltip_information)  # noqa
        layout.addWidget(self.tooltip_button, widget_row, 0, 1, 1)

        # Widget
        self.widget = widget
        layout.addWidget(self.widget, widget_row, 1, 1, 1)

    def get_tooltip_text(self) -> str:
        """Returns the tooltip's text."""
        return self._tooltips.get(self.tooltip_name, '<TOOLTIP NOT FOUND!>')

    def get_tooltip_icon(self) -> qtg.QIcon | qtg.QPixmap:
        """Returns the tooltip button's icon."""
        return self.tooltip_button.style().standardIcon(getattr(qtw.QStyle, "SP_TitleBarContextHelpButton"))

    def display_tooltip_information(self) -> None:
        """Displays the tooltip information in a textbox."""
        qtw.QMessageBox.information(self, self.tooltip_name, self.tooltip_text)


class ToolTipSpinBox(ToolTipWidget):
    """Widget representing a ToolTipWidget with a spinbox as its main widget, which optionally includes a slider."""
    def __init__(
            self,
            name: str,
            label: str,
            add_slider: bool = False,
            spinbox_params: dict[str, float] = None,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ToolTipSpinBox instance."""
        spinbox_params = spinbox_params or {}
        if add_slider is True:
            widget = SliderSpinBox(**spinbox_params)
        else:
            widget = AutoSpinBox(**spinbox_params)
        super().__init__(widget=widget, tooltip_name=name, top_label=label, parent=parent)
