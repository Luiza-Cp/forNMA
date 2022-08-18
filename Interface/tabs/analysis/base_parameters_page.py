"""
Interface/tabs/analysis/base_parameters_page.py - contains the base "page" widget
used in forNMA's "Analysis" tab, left-hand side.
"""
from __future__ import annotations

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import RowLayout


class BaseParametersPage(qtw.QWidget):
    """Class defining the base layout shared by the segmentation/detection parameters pages."""
    backButtonClicked = qtc.pyqtSignal()  # TODO: CHECK HERE!!!!!

    def __init__(
            self,
            title: str,
            params_widget: qtw.QWidget,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ParametersPage instance."""
        super().__init__(parent=parent)
        self.params_widget = params_widget

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # ### Top row
        top_row_layout = RowLayout()
        layout.addLayout(top_row_layout)
        # Back button
        self.back_button = qtw.QPushButton("Back")
        self.back_button.clicked.connect(self.backButtonClicked)
        # Title label
        self.title_label = qtw.QLabel(title)
        top_row_layout.addWidget(self.title_label)
        # Add widgets to top row layout
        top_row_layout.addWidgets([self.back_button, self.title_label])

        # Params widget area
        self.scroll_area = qtw.QScrollArea()
        layout.addWidget(self.scroll_area)
        if self.params_widget is not None:
            self.scroll_area.setWidget(self.params_widget)
            self.scroll_area.setWidgetResizable(True)
