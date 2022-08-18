"""Interface/tabs/analysis/analysis_tab.py - contains the top-level widgets used in forNMA's "Analysis" tab."""
from __future__ import annotations

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import LogAreaWidget, RowLayout, SlidingStackedWidget
from .detection_page import DetectionParametersPage
from .segmentation_page import SegmentationParametersPage


class AnalysisParametersWidget(qtw.QWidget):
    """Class representing the widget on the left-hand side of the "analysis" tab."""
    channelsSet = qtc.pyqtSignal(list)

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

        # Run button in a row layout
        self.run_button = qtw.QPushButton('Run forNMA Analysis')
        row_layout = RowLayout(widgets=['stretch', self.run_button])
        layout.addLayout(row_layout)

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
    segmentationButtonClicked = qtc.pyqtSignal()  # TODO: CHECK HERE!!!!!
    detectionButtonClicked = qtc.pyqtSignal()  # TODO: CHECK HERE!!!!!

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
        self.segmentation_parameters_button.clicked.connect(self.segmentationButtonClicked)
        layout.addWidget(self.segmentation_parameters_button)

        # Detection button
        self.detection_parameters_button = qtw.QPushButton('Detection parameters')
        self.detection_parameters_button.clicked.connect(self.detectionButtonClicked)
        layout.addWidget(self.detection_parameters_button)

        # Parameters label
        self.parameters_label = qtw.QTextEdit()
        self.parameters_label.setStyleSheet('QTextEdit {font-size: 14px}')
        self.parameters_label.setAlignment(qtc.Qt.AlignLeft)
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

        # Log Area
        self.log_area = LogAreaWidget(default_text='Select forNMA parameters on the left')
        layout.addWidget(self.log_area)

        # Progress bar
        self.progress_bar = qtw.QProgressBar()
        layout.addWidget(self.progress_bar)

        # Aliases
        self.update_progress_bar = self.progress_bar.setValue
        self.reset_progress_bar = self.progress_bar.reset
        self.reset_log = self.log_area.reset_log
        self.write_default_text = self.log_area.write_default_text
        self.write_message = self.log_area.write_message
        self.write_warning = self.log_area.write_warning
        self.write_title = self.log_area.write_title
