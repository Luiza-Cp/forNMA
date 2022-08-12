"""Interface/tabs/nma/nma_tab.py - contains the top-level widgets used in forNMA's "NMA" tab."""
from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw


class NMAParametersWidget(qtw.QWidget):
    """
    Class representing the widget on the left-hand side of the "NMA" tab,
    where the settings for the NMA analysis are set.
    """
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a NMAParametersWidget."""
        super().__init__(parent=parent)
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.label = qtw.QLabel('Welcome to NMA!')
        self.label.setStyleSheet('QLabel {font-size: 24px}')
        self.label.setAlignment(qtc.Qt.AlignCenter)  # noqa
        layout.addWidget(self.label)


class NMAAreaWidget(qtw.QWidget):
    """
    Class representing the widget on the right-hand side of the "NMA" tab,
    where the NMA plots are displayed.
    """
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a NMAAreaWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
