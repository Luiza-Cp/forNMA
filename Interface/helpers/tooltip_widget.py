"""helpers/tooltip_layout.py - module defining a widget with a tooltip button."""
from __future__ import annotations

from PySide6 import QtGui as qtg, QtWidgets as qtw


class ToolTipWidget(qtw.QWidget):
    """Widget containing an informative tooltip/info button to the left, and an optional checkbox at the top."""
    _tooltips = {
        'channel_with_nuclei': "This is the channel with nuclei text.",
        'magnification': "No tooltip yet!",
        'pixel_size': "Tooltip",
        'threshold': "Tooltip",
        'offset': "tooltip",
        'blur': "This is smooth + blur",
        'adjust_size': "ADJUST SIZE tooltip",
        'shape': "SHAPE tooltip",
        'eccentricity': "eccentricity tooltip",
        'cut_edges': "cut_edges tooltip",
        'size': "SIZE MIN MAX tooltip",
        'radius': "RADIUS MIN MAX tooltip",
        'rescale_intensity': "Rescale???",
        'remove_bg': "Remove???",
        'radius_bg': "Rolling ball",
        'weakly_labeled': "These are some weakly labeled stuff",
        'find_low_intensity_nucleus': "Let's try to find them!",
    }

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
