"""tabs/analysis.py - contains all widgets used in forNMA's "analysis" tab."""
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

        # Signal aliases
        self.segmentationParamsChanged = self.segmentation_parameters_page.segmentationParamsChanged

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
        self.parameters_label = qtw.QLabel("")
        layout.addWidget(self.parameters_label)


class ParametersPage(qtw.QWidget):
    """Class defining the base layout shared by the segmentation/detection parameters pages."""
    backButtonClicked = qtc.Signal()

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
        self.back_button.clicked.connect(self.backButtonClicked)  # noqa
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
        self.label.setStyleSheet('QLabel {font-size: 14px}')
        self.label.setAlignment(qtc.Qt.AlignLeft)  # noqa
        layout.addWidget(self.label)

        # Method aliases
        self.setText = self.label.setText
