"""tabs/analysis.py - contains the main widget used in forNMA's "analysis" tab."""
from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import RowLayout, SlidingStackedWidget
from Interface.tabs import SegmentationParametersPage, DetectionParametersPage


class AnalysisParametersWidget(qtw.QWidget):
    """Class representing the widget on the left-hand side of the "analysis" tab."""
    channelsSet = qtc.Signal(list)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an AnalysisParametersWidget instance."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # ### Widget pages (stack)
        self.stack = SlidingStackedWidget()
        layout.addWidget(self.stack)
        # Main page
        self.analysis_main_page = AnalysisMainPage()
        self.analysis_main_page.segmentationButtonClicked.connect(self.switch_to_segmentation_parameters_page)
        self.analysis_main_page.detectionButtonClicked.connect(self.switch_to_detection_parameters_page)
        self.stack.addWidget(self.analysis_main_page)
        # Segmentation page
        self.segmentation_parameters_page = SegmentationParametersPage()
        self.segmentation_parameters_page.backButtonClicked.connect(self.switch_to_analysis_main_page)
        self.channelsSet.connect(self.segmentation_parameters_page.channelsSet)
        self.stack.addWidget(self.segmentation_parameters_page)
        # Detection page
        self.detection_parameters_page = DetectionParametersPage()
        self.detection_parameters_page.backButtonClicked.connect(self.switch_to_analysis_main_page)
        self.channelsSet.connect(self.detection_parameters_page.channelsSet)
        self.stack.addWidget(self.detection_parameters_page)

        # ### Button row
        button_row_layout = RowLayout()
        layout.addLayout(button_row_layout)
        # Preview button
        self.preview_button = qtw.QPushButton('Preview')
        # Run button
        self.run_button = qtw.QPushButton('Run')
        # Add buttons to row
        button_row_layout.addWidgets([self.preview_button, self.run_button])
        button_row_layout.addStretch()

        # Method aliases
        self.setText = self.analysis_main_page.setText

        # Signal aliases
        self.segmentationParamsChanged = self.segmentation_parameters_page.segmentationParamsChanged
        self.detectionParamsChanged = self.detection_parameters_page.detectionParamsChanged

    def switch_to_analysis_main_page(self) -> None:
        """Changes the current widget to the analysis main page."""
        self.stack.slideInWidget(self.analysis_main_page)

    def switch_to_segmentation_parameters_page(self) -> None:
        """Changes the current widget to the segmentation parameters page."""
        self.stack.slideInWidget(self.segmentation_parameters_page)

    def switch_to_detection_parameters_page(self) -> None:
        """Changes the current widget to the detection parameters page."""
        self.stack.slideInWidget(self.detection_parameters_page)


class AnalysisMainPage(qtw.QWidget):
    """Class defining the main page layout of the AnalysisParametersWidget."""
    segmentationButtonClicked = qtc.Signal()
    detectionButtonClicked = qtc.Signal()

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an AnalysisMainPage instance."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Segmentation button
        self.segmentation_parameters_button = qtw.QPushButton('Segmentation parameters')
        self.segmentation_parameters_button.clicked.connect(self.segmentationButtonClicked)  # noqa
        layout.addWidget(self.segmentation_parameters_button)

        # Detection button
        self.detection_parameters_button = qtw.QPushButton('Detection parameters')
        self.detection_parameters_button.clicked.connect(self.detectionButtonClicked)  # noqa
        layout.addWidget(self.detection_parameters_button)

        # Parameters label
        self.parameters_label = qtw.QTextEdit()
        self.parameters_label.setStyleSheet('QTextEdit {font-size: 14px}')
        self.parameters_label.setAlignment(qtc.Qt.AlignLeft)  # noqa
        self.parameters_label.setReadOnly(True)
        layout.addWidget(self.parameters_label)

    def setText(
            self,
            params: dict,
    ) -> None:
        """Sets the parameters label text, given the params dictionary."""
        text = '--- Current Parameters ---\n\n'
        for param_section_name, param_dict in params.items():
            text += f' -> {param_section_name.capitalize()} Parameters:\n'
            for key, value in param_dict.items():
                text += f'{key}: {value}\n'
            text += '\n'
        self.parameters_label.setText(text)


class AnalysisAreaWidget(qtw.QWidget):
    """Class representing the widget on the right-hand side of the "analysis" tab."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an AnalysisAreaWidget instance."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Label
        self.label = qtw.QLabel('Select analysis parameters on the left')
        self.label.setStyleSheet('QLabel {font-size: 24px}')
        self.label.setAlignment(qtc.Qt.AlignCenter)  # noqa
        layout.addWidget(self.label)
