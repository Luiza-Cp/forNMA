"""tabs/analysis.py - contains all widgets used in forNMA's "analysis" tab."""
from __future__ import annotations

from typing import Any

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface import ForNMAWidget
from Interface.custom_widgets import CollapsableButton
from Interface.fornma_parameters import threshold_has_offset, get_default_threshold
from Interface.tabs import BaseParametersPage


class SegmentationParametersPage(BaseParametersPage):
    """Subclass of ParametersPage responsible for displaying the segmentation parameters."""
    channelsSet = qtc.Signal(list)
    segmentationDataChanged = qtc.Signal(dict)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a SegmentationParametersPage instance."""
        params_widget = SegmentationParametersWidget()
        super().__init__(title='Segmentation', params_widget=params_widget, parent=parent)

        # This connection servers as a "tunnel" in order to the channel names reach the params_widget
        self.channelsSet.connect(params_widget.set_channel_values)

        # Signal aliases
        self.segmentationParamsChanged = params_widget.segmentationParamsChanged


class SegmentationParametersWidget(qtw.QWidget):
    """Class defining the layout and widgets for the segmentation parameters."""
    segmentationParamsChanged = qtc.Signal(dict)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a SegmentationParametersWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Header
        self.nuclear_detection_channel_widget = ForNMAWidget(fornma_id='channel_with_nuclei')
        layout.addWidget(self.nuclear_detection_channel_widget)

        # forNMA Parameters
        self.fornma_params_widget = ForNMAParamsWidget()
        self.fornma_collapsable_button = CollapsableButton("forNMA", widget_to_hide=self.fornma_params_widget)
        layout.addWidget(self.fornma_collapsable_button)

        # Cellpose Parameters
        self.cellpose_params_widget = CellposeParamsWidget()
        self.cellpose_collapsable_button = CollapsableButton("Cellpose", widget_to_hide=self.cellpose_params_widget)
        layout.addWidget(self.cellpose_collapsable_button)

        # Keep widgets at the top
        layout.addStretch()

        # Connection
        self.nuclear_detection_channel_widget.valueChanged.connect(self.on_params_changed)
        self.fornma_params_widget.paramsChanged.connect(self.on_params_changed)
        self.cellpose_params_widget.paramsChanged.connect(self.on_params_changed)

    @qtc.Slot(list)
    def set_channel_values(
            self,
            channels: list[str],
    ) -> None:
        """Slot for setting the channel value names in the nuclei channel combobox."""
        while self.nuclear_detection_channel_widget.currentIndex() != -1:
            self.nuclear_detection_channel_widget.removeItem(0)
        for channel in channels:
            self.nuclear_detection_channel_widget.addItem(channel)

    def on_params_changed(
            self,
            _: Any = None,  # Parameter that has changed - we don't need it because we will get all parameters anyway
    ) -> None:
        """Emits all segmentation parameters at once."""
        params = {
            'fornma': self.fornma_params_widget.get_values(),
            'cellpose': self.cellpose_params_widget.get_values(),
        }
        # "Manually" add channel information
        k = self.nuclear_detection_channel_widget.objectName()
        params['fornma'][k] = self.nuclear_detection_channel_widget.value()
        self.segmentationParamsChanged.emit(params)


class ForNMAParamsWidget(qtw.QWidget):
    """Widget containing all of forNMA's parameters in it."""
    paramsChanged = qtc.Signal(object)  # type does not matter
    _blueprint = (
        # Format: ( forNMA ID, include_slider )
        ('magnification', False),
        ('pixel_size', False),
        ('threshold', False),
        ('offset', False),
        ('blur', True),
        ('adjust_size', True),
        ('shape', True),
        ('eccentricity', True),
        ('cut_edges', True),
        ('min_size', True),
        ('max_size', True),
        ('min_radius', True),
        ('max_radius', True),
        ('rescale_intensity', True),
        ('remove_background', True),
        ('radius_bg', True),
        ('weakly_labeled', True),
        ('find_low_intensity_nucleus', True),
    )

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ForNMAParamsWidget."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self._fornma_params = {}

        for fornma_id, add_slider in self._blueprint:
            fornma_widget = ForNMAWidget(fornma_id=fornma_id, add_slider=add_slider)
            layout.addWidget(fornma_widget)
            self._fornma_params[fornma_id] = fornma_widget
            if fornma_id == 'threshold':  # Specific routing for threshold widget
                fornma_widget.valueChanged.connect(self.on_threshold_combobox_changed)
            elif fornma_id == 'remove_background':  # Specific routing for remove background widget
                fornma_widget.valueChanged.connect(self.on_remove_background_checkbox_clicked)
            elif fornma_id in ('min_size', 'min_radius'):  # Specific routing for min size and min radius
                fornma_widget.valueChanged.connect(self.on_min_value_changed)
            elif fornma_id in ('max_size', 'max_radius'):  # Specific routing for max size and max radius
                fornma_widget.valueChanged.connect(self.on_max_value_changed)
            else:  # Generic routing for all other widgets
                fornma_widget.valueChanged.connect(self.paramsChanged)

        # Final setup
        threshold_widget = self._fornma_params['threshold']
        threshold_widget.setCurrentText(get_default_threshold())
        offset_widget = self._fornma_params['remove_background']
        offset_widget.setChecked(True)  # Checks and unchecks the checkbox just to make sure that the signal is emitted
        offset_widget.setChecked(False)

    @qtc.Slot(str)
    def on_threshold_combobox_changed(
            self,
            selected: str,
    ) -> None:
        """Enables/disables the threshold offset slider whenever the threshold combobox changes its value."""
        has_threshold = threshold_has_offset(threshold_name=selected)
        offset_widget = self._fornma_params['offset']  # HARD-CODED: parameter name in blueprint must be exact!
        offset_widget.setEnabled(has_threshold)
        self.paramsChanged.emit(selected)

    @qtc.Slot(str)
    def on_remove_background_checkbox_clicked(
            self,
            checked: bool,
    ) -> None:
        """Enables/disables the rolling ball radius whenever the remove_background checkbox is clicked."""
        offset_widget = self._fornma_params['radius_bg']  # HARD-CODED: parameter name in blueprint must be exact!
        offset_widget.setEnabled(checked)
        self.paramsChanged.emit(checked)

    @qtc.Slot(float)
    def on_min_value_changed(
            self,
            new_value: float,
    ) -> None:
        """Changes the max value of the related widget if the min value is greater than it."""
        sender_name = self.sender().objectName()  # 'min_size' or 'min_radius'
        max_size_widget_name = sender_name.replace('min', 'max')
        max_size_widget = self._fornma_params[max_size_widget_name]
        if max_size_widget.value() < new_value:
            max_size_widget.setValue(new_value)
        self.paramsChanged.emit(new_value)

    @qtc.Slot(float)
    def on_max_value_changed(
            self,
            new_value: float,
    ) -> None:
        """Changes the min value of the related widget if the max value is less than it."""
        sender_name = self.sender().objectName()  # 'max_size' or 'max_radius'
        min_size_widget_name = sender_name.replace('max', 'min')
        min_size_widget = self._fornma_params[min_size_widget_name]
        if min_size_widget.value() > new_value:
            min_size_widget.setValue(new_value)
        self.paramsChanged.emit(new_value)

    def get_values(self) -> dict[str, Any]:
        """Return the name and value of each forNMA parameter."""
        return {
            widget.objectName(): (widget.value() if widget.isEnabled() else None)
            for _, widget in self._fornma_params.items()
        }


class CellposeParamsWidget(qtw.QWidget):
    """Widget containing all of Cellpose's parameters in it."""
    paramsChanged = qtc.Signal(object)  # type does not matter
    _blueprint = (
        # Format: ( forNMA ID, include_slider )
        ('diameter', True),
        ('flow_threshold', True),
        ('mask_threshold', True),
        ('cellpose_rescale_intensity', False),
        ('cellpose_remove_background', False),
        ('use_gpu', False),
    )

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a CellposeParamsWidget."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self._fornma_params = {}

        for fornma_id, add_slider in self._blueprint:
            fornma_widget = ForNMAWidget(fornma_id=fornma_id, add_slider=add_slider)
            layout.addWidget(fornma_widget)
            self._fornma_params[fornma_id] = fornma_widget
            fornma_widget.valueChanged.connect(self.paramsChanged)

    def get_values(self) -> dict[str, Any]:
        """Return the name and value of each forNMA parameter."""
        return {
            widget.objectName(): (widget.value() if widget.isEnabled() else None)
            for _, widget in self._fornma_params.items()
        }
