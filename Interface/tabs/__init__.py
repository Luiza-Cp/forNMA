"""tabs module - contains the widgets for each individual tab in forNMA's interface."""

# Data tab
from .data import DataAreaWidget, DataParametersWidget

# Analysis tab
from .analysis.parameters_page import BaseParametersPage
from .analysis.detection import DetectionParametersPage
from .analysis.segmentation import SegmentationParametersPage
from .analysis.analysis import AnalysisAreaWidget, AnalysisParametersWidget
