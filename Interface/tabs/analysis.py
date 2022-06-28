"""tabs/analysis.py - contains all widgets used in forNMA's "analysis" tab."""

from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.helpers import (
    CollapsibleWidget,
    DoubleSliderLabeledLayout,
    DoubleSliderSpinBox,
    ToolTipLayout,
    SlidingStackedWidget,
)


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

        self.stack = SlidingStackedWidget()
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

        btn_layout = qtw.QHBoxLayout()
        layout.addLayout(btn_layout)

        self.preview_button = qtw.QPushButton('Preview')
        btn_layout.addWidget(self.preview_button)

        self.run_button = qtw.QPushButton('Run')
        btn_layout.addWidget(self.run_button)

    def switch_to_analysis_parameters_home(self) -> None:
        """Changes the widget layout to the "home" page."""
        self.stack.slideInWidget(self.analysis_parameters_home)

    def switch_to_segmentation_parameters_page(self) -> None:
        """Changes the widget layout to the segmentation parameters."""
        self.stack.slideInWidget(self.segmentation_parameters)

    def switch_to_detection_parameters_page(self) -> None:
        """Changes the widget layout to the detection parameters."""
        self.stack.slideInWidget(self.detection_parameters)

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

        # Header
        self.nuclei_channel_combobox = qtw.QComboBox()
        nuclei_channel_layout = ToolTipLayout(
            widget_or_layout=self.nuclei_channel_combobox,
            widget_name='channel_with_nuclei',
            top_label="Channel for nuclear detection",
        )
        layout.addLayout(nuclei_channel_layout)

        # forNMA
        self.fornma_params_scroll_area = qtw.QScrollArea()
        layout.addWidget(self.fornma_params_scroll_area)
        self.fornma_params_widget = ForNMAParamsWidget()
        self.fornma_params_scroll_area.setWidget(self.fornma_params_widget)

        # Cellpose
        # Cellpose collapse - all widgets go under here
        self.cellpose_params_scroll_area = qtw.QScrollArea()
        layout.addWidget(self.cellpose_params_scroll_area)
        self.cellpose_params_widget = CollapsibleWidget(qtw.QVBoxLayout(), title="Cellpose")  # TODO: replace with class
        self.cellpose_params_scroll_area.setWidget(self.cellpose_params_widget)

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


class ForNMAParamsWidget(CollapsibleWidget):
    """Class representing a CollapsibleWidget that contains all of forNMA's parameters in it."""
    threshold_types = {  # structured as { threshold_name: uses_offset }
        'Isodata': False,
        'Li': False,
        'Mean': False,
        'Minimum': False,
        'Median': False,
        'Multi-otsu': False,
        'Otsu': False,
        'Triangle': False,
        'Yen': False,
        'Local Mean': True,
        'Local Gaussian': True,
    }

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ForNMAParamsWidget."""
        layout = qtw.QVBoxLayout()

        # Magnification
        self.magnification_spinbox = qtw.QSpinBox(minimum=0, maximum=1000, singleStep=5, value=20)  # noqa
        magnification_layout = ToolTipLayout(
            widget_or_layout=self.magnification_spinbox,
            widget_name='magnification',
            top_label="Objective magnification",
        )
        layout.addLayout(magnification_layout)

        # Pixel size
        self.pixel_size_spinbox = qtw.QDoubleSpinBox(minimum=0, maximum=1_000_000, singleStep=0.5, value=0.5)  # noqa
        pixel_size_layout = ToolTipLayout(
            widget_or_layout=self.pixel_size_spinbox,
            widget_name='pixel_size',
            top_label="Pixel size",
        )
        layout.addLayout(pixel_size_layout)

        # Threshold selection
        self.threshold_combobox = qtw.QComboBox()
        threshold_layout = ToolTipLayout(
            widget_or_layout=self.threshold_combobox,
            widget_name="threshold",
            top_label="Threshold type"
        )
        self.threshold_combobox.addItems(list(self.threshold_types))
        layout.addLayout(threshold_layout)

        # Threshold offset (a layout, not a widget!)
        self.threshold_offset_layout = DoubleSliderLabeledLayout(
            left_label='offset',
            minimum=0.0,
            maximum=1.0,
            value=0.5,
            step=0.05,
            enabled=False,
        )
        layout.addLayout(self.threshold_offset_layout)

        # Link threshold selection and threshold offset
        self.threshold_combobox.currentTextChanged.connect(self.on_threshold_combobox_changed)  # noqa

        # blur spinbox
        self.blur_spinbox = DoubleSliderSpinBox(
            minimum=0.0,
            maximum=100.0,
            value=12.0,
            step=0.05,
        )
        blur_layout = ToolTipLayout(
            widget_or_layout=self.blur_spinbox,
            widget_name='blur',
            top_label='Smooth',
        )
        layout.addLayout(blur_layout)

        # Adjust Size spinbox
        self.adjust_size_spinbox = DoubleSliderSpinBox(
            minimum=-1_000.0,
            maximum=1_000.0,
            value=0.0,
            step=0.05,
        )
        adjust_size_layout = ToolTipLayout(
            widget_or_layout=self.adjust_size_spinbox,
            widget_name='adjust_size',
            top_label='Adjust Size',
        )
        layout.addLayout(adjust_size_layout)

        # Shape spinbox
        self.shape_spinbox = DoubleSliderSpinBox(
            minimum=0.0,
            maximum=1.0,
            value=0.88,
            step=0.05,
        )
        shape_layout = ToolTipLayout(
            widget_or_layout=self.shape_spinbox,
            widget_name='shape',
            top_label='Shape',
        )
        layout.addLayout(shape_layout)

        # Eccentricity spinbox
        self.eccentricity_spinbox = DoubleSliderSpinBox(
            minimum=0.0,
            maximum=1.0,
            value=0.0,
            step=0.05,
        )
        eccentricity_layout = ToolTipLayout(
            widget_or_layout=self.eccentricity_spinbox,
            widget_name='eccentricity',
            top_label='Eccentricity',
        )
        layout.addLayout(eccentricity_layout)

        # Cut edges spinbox
        self.cut_edges_spinbox = DoubleSliderSpinBox(
            minimum=0.0,
            maximum=1.0,
            value=0.5,
            step=0.05,
        )
        cut_edges_layout = ToolTipLayout(
            widget_or_layout=self.cut_edges_spinbox,
            widget_name='cut_edges',
            top_label='Cut Edges',
        )
        layout.addLayout(cut_edges_layout)

        # Size spinboxes
        self.max_size_spinbox = qtw.QSpinBox()
        self.min_size_spinbox = qtw.QSpinBox()
        row = qtw.QHBoxLayout()
        row.addWidget(qtw.QLabel('Min'))
        row.addWidget(self.min_size_spinbox)
        row.addWidget(qtw.QLabel('Max'))
        row.addWidget(self.max_size_spinbox)
        size_layout = ToolTipLayout(
            widget_or_layout=row,
            widget_name='size',
            top_label='Size',
            use_top_checkbox=True,
        )
        layout.addLayout(size_layout)

        # Initializes all forNMA widgets here
        super().__init__(content_layout=layout, title="forNMA", parent=parent)

    @qtc.Slot(str)
    def on_threshold_combobox_changed(
            self,
            new_text: str,
    ) -> None:
        """Enables/disables the threshold offset slider whenever the threshold combobox changes its value."""
        enabled = self.threshold_types[new_text]
        self.threshold_offset_layout.setEnabled(enabled)
