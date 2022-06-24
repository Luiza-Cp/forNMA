"""analysis.py - contains all widgets used in forNMA's "analysis" tab."""

from __future__ import annotations

from PySide6 import QtWidgets as qtw


class AnalysisWidget(qtw.QWidget):
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.label = qtw.QLabel('AnalysisWidget')
        layout.addWidget(self.label)


class AnalysisParameters(qtw.QWidget):
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.label = qtw.QLabel('AnalysisParameters')
        layout.addWidget(self.label)
