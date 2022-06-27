"""tabs/analysis.py - contains all widgets used in forNMA's "analysis" tab."""

from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.helpers import CollapsibleWidget, ToolTipLayout


class AnalysisAreaWidget(qtw.QWidget):
    """Class representing the widget on the right-hand side of the "analysis" tab."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an AnalysisAreaWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.label = qtw.QLabel('Select analysis parameters on the left')
        self.label.setStyleSheet('QLabel {font-size: 24px}')
        self.label.setAlignment(qtc.Qt.AlignCenter)  # noqa
        layout.addWidget(self.label)


class AnalysisParametersWidget(qtw.QWidget):
    """Class representing the widget on the left-hand side of the "analysis" tab."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an AnalysisParametersWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.stack = qtw.QStackedWidget()
        layout.addWidget(self.stack)

        self.analysis_parameters_home = AnalysisParametersHome()
        self.analysis_parameters_home.segmentationButtonClicked.connect(self.switch_to_segmentation_parameters_page)
        self.analysis_parameters_home.detectionButtonClicked.connect(self.switch_to_detection_parameters_page)
        self.stack.addWidget(self.analysis_parameters_home)

        self.segmentation_parameters = SegmentationParametersWidget()
        self.segmentation_parameters.backButtonClicked.connect(self.switch_to_analysis_parameters_home)
        self.stack.addWidget(self.segmentation_parameters)

        self.detection_parameters = DetectionParametersWidget()
        self.detection_parameters.backButtonClicked.connect(self.switch_to_analysis_parameters_home)
        self.stack.addWidget(self.detection_parameters)

        layout.addStretch()

        btn_layout = qtw.QHBoxLayout()
        layout.addLayout(btn_layout)

        self.preview_button = qtw.QPushButton('Preview')
        btn_layout.addWidget(self.preview_button)

        self.run_button = qtw.QPushButton('Run')
        btn_layout.addWidget(self.run_button)

    def switch_to_analysis_parameters_home(self) -> None:
        """Changes the widget layout to the "home" page."""
        self.stack.setCurrentWidget(self.analysis_parameters_home)

    def switch_to_segmentation_parameters_page(self) -> None:
        """Changes the widget layout to the segmentation parameters."""
        self.stack.setCurrentWidget(self.segmentation_parameters)

    def switch_to_detection_parameters_page(self) -> None:
        """Changes the widget layout to the detection parameters."""
        self.stack.setCurrentWidget(self.detection_parameters)

    def set_channel_values(
            self,
            channels: list[str],
    ) -> None:
        """Sets the channel value names on the SegmentationParametersWidget."""
        self.segmentation_parameters.set_channel_values(channels=channels)


class AnalysisParametersHome(qtw.QWidget):
    """Class defining the "home" layout of the AnalysisParametersWidget."""
    segmentationButtonClicked = qtc.Signal()
    detectionButtonClicked = qtc.Signal()

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an AnalysisParametersHome instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.segmentation_parameters_button = qtw.QPushButton('Segmentation parameters')
        self.segmentation_parameters_button.clicked.connect(self.segmentationButtonClicked)  # noqa
        layout.addWidget(self.segmentation_parameters_button)

        self.detection_parameters_button = qtw.QPushButton('Detection parameters')
        self.detection_parameters_button.clicked.connect(self.detectionButtonClicked)  # noqa
        layout.addWidget(self.detection_parameters_button)

        self.parameters_label = qtw.QLabel("")
        layout.addWidget(self.parameters_label)


class ParametersBaseWidget(qtw.QWidget):
    """Class defining the base layout shared by the segmentation and detection widgets."""
    backButtonClicked = qtc.Signal()

    def __init__(
            self,
            title: str = "",
    ) -> None:
        """Initializes a ParametersBaseWidget instance."""
        super().__init__()

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        top_row_layout = qtw.QHBoxLayout()
        layout.addLayout(top_row_layout)

        self.back_button = qtw.QPushButton("Back")
        self.back_button.clicked.connect(self.backButtonClicked)  # noqa
        top_row_layout.addWidget(self.back_button)

        self.title_label = qtw.QLabel(title)
        top_row_layout.addWidget(self.title_label)


class SegmentationParametersWidget(ParametersBaseWidget):
    """Class defining the layout and widgets for the segmentation parameters."""
    def __init__(
            self,
            title: str = "Segmentation",
    ) -> None:
        """Initializes a SegmentationParametersWidget instance."""
        super().__init__(title=title)
        layout = self.layout()

        # ### HEADER SECTION
        # Nuclear detection channel
        self.nuclei_channel_combobox = qtw.QComboBox()
        nuclei_channel_layout = ToolTipLayout(
            widget=self.nuclei_channel_combobox,
            widget_name='channel_with_nuclei',
            top_label="Channel for nuclear detection",
        )
        layout.addLayout(nuclei_channel_layout)

        # ### FORNMA SECTION
        # Magnification
        self.magnification_spinbox = qtw.QSpinBox(minimum=0, maximum=1000, singleStep=5, value=10)  # noqa
        magnification_layout = ToolTipLayout(
            widget=self.magnification_spinbox,
            widget_name='magnification',
            top_label="Objective magnification",
        )
        # forNMA collapse - all widgets go under here
        self.fornma_collapse = CollapsibleWidget(magnification_layout, title="forNMA")
        layout.addWidget(self.fornma_collapse)

        # ### CELLPOSE SECTION
        # Cellpose collapse - all widgets go under here
        self.cellpose_collapse = CollapsibleWidget(qtw.QVBoxLayout(), title="Cellpose")
        layout.addWidget(self.cellpose_collapse)

        layout.addStretch()

    def set_channel_values(
            self,
            channels: list[str],
    ) -> None:
        """Sets the channel value names on the SegmentationParameters combobox."""
        while self.nuclei_channel_combobox.currentIndex() != -1:
            self.nuclei_channel_combobox.removeItem(0)
        for channel in channels:
            self.nuclei_channel_combobox.addItem(channel)


class DetectionParametersWidget(ParametersBaseWidget):
    """Class defining the layout and widgets for the detection parameters."""
    def __init__(
            self,
            title: str = "Detection",
    ) -> None:
        """Initializes a DetectionParametersWidget instance."""
        super().__init__(title=title)
        layout = self.layout()

        layout.addStretch()
