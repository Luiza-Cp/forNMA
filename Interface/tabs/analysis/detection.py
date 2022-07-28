"""tabs/analysis.py - contains all widgets used in forNMA's "analysis" tab."""

from __future__ import annotations

from PySide6 import QtWidgets as qtw

from Interface.tabs import BaseParametersPage


class DetectionParametersPage(BaseParametersPage):
    """Subclass of ParametersPage responsible for displaying the segmentation parameters."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DetectionParametersPage instance."""
        super().__init__(title='Detection', params_widget=DetectionParametersWidget(), parent=parent)


class DetectionParametersWidget(qtw.QWidget):
    """Class defining the layout and widgets for the detection parameters."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DetectionParametersWidget instance."""
        super().__init__(parent=parent)
        layout = qtw.QVBoxLayout()

        self.label = qtw.QLabel("Detection!!!")
        layout.addWidget(self.label)

        layout.addStretch()
