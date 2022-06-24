"""analysis.py - contains all widgets used in forNMA's "analysis" tab."""

from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.helpers.collapsible_widget import CollapsibleWidget


class AnalysisWidget(qtw.QWidget):
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.label = qtw.QLabel('Select analysis parameters on the left')
        self.label.setStyleSheet('QLabel {font-size: 24px}')
        self.label.setAlignment(qtc.Qt.AlignCenter)  # noqa
        layout.addWidget(self.label)


class AnalysisParameters(qtw.QWidget):
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.params = qtw.QPushButton('Click!')
        lay = qtw.QVBoxLayout()
        lay.addWidget(self.params)

        self.segmentation_collapse = CollapsibleWidget(SegmentationParametersLayout(), title='Segmentation parameters')
        layout.addWidget(self.segmentation_collapse)
        self.detection_collapse = CollapsibleWidget(lay, title='Detection parameters')
        layout.addWidget(self.detection_collapse)
        layout.addStretch()


class SegmentationParametersLayout(qtw.QVBoxLayout):
    def __init__(
            self,
    ) -> None:
        super().__init__()
        self.label = qtw.QLabel("Channel for nuclear detection")
        self.addWidget(self.label)

        self.combobox = qtw.QComboBox()
        self.addWidget(self.combobox)
