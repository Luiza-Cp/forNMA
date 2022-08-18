"""Interface/tabs/analysis/segmentation_page - contains the widgets used in forNMA's segmentation parameters page."""
from __future__ import annotations

from typing import Any

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import CollapsableWidget
from Interface.fornma_core import ForNMAWidget, threshold_has_offset, get_default_threshold
from .base_parameters_page import BaseParametersPage


class SegmentationParametersPage(BaseParametersPage):
    """Subclass of ParametersPage responsible for displaying the segmentation parameters."""
    channelsSet = qtc.pyqtSignal(list)

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
    segmentationParamsChanged = qtc.pyqtSignal(dict)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a SegmentationParametersWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Header
        self.output_folder_widget = ForNMAWidget(fornma_id='output_folder', add_slider=False, add_help=True)
        layout.addWidget(self.output_folder_widget)
        self.nuclear_detection_channel_widget = ForNMAWidget(
            fornma_id='channel_with_nuclei',
            add_slider=False,
            add_help=True,
        )
        layout.addWidget(self.nuclear_detection_channel_widget)

        # Global Parameters
        self.global_params_widget = GlobalParamsWidget()
        self.global_collapsable_button = CollapsableWidget(
            "Global parameters",
            widget_to_hide=self.global_params_widget,
        )
        layout.addWidget(self.global_collapsable_button)

        # forNMA Parameters
        self.fornma_checkbox = ForNMAWidget(fornma_id='use_fornma', add_slider=False, add_help=False)
        layout.addWidget(self.fornma_checkbox)
        self.fornma_params_widget = ForNMAParamsWidget()
        self.fornma_collapsable_button = CollapsableWidget(
            "forNMA parameters",
            widget_to_hide=self.fornma_params_widget,
        )
        layout.addWidget(self.fornma_collapsable_button)

        # Cellpose Parameters
        self.cellpose_checkbox = ForNMAWidget(fornma_id='use_cellpose', add_slider=False, add_help=False)
        layout.addWidget(self.cellpose_checkbox)
        self.cellpose_params_widget = CellposeParamsWidget()
        self.cellpose_collapsable_button = CollapsableWidget(
            "Cellpose parameters",
            widget_to_hide=self.cellpose_params_widget,
        )
        layout.addWidget(self.cellpose_collapsable_button)

        # Keep widgets at the top
        layout.addStretch()

        # Start with fornma_checkbox checked
        self.fornma_checkbox.setChecked(True)
        # Start with cellpose_collapsable_button disabled
        self.cellpose_collapsable_button.setEnabled(False)

        # Connections
        self.output_folder_widget.valueChanged.connect(self.on_params_changed)
        self.nuclear_detection_channel_widget.valueChanged.connect(self.on_params_changed)
        self.global_params_widget.paramsChanged.connect(self.on_params_changed)
        self.fornma_params_widget.paramsChanged.connect(self.on_params_changed)
        self.cellpose_params_widget.paramsChanged.connect(self.on_params_changed)
        self.fornma_checkbox.valueChanged.connect(self.on_fornma_checkbox_state_changed)
        self.cellpose_checkbox.valueChanged.connect(self.on_cellpose_checkbox_state_changed)

    def set_channel_values(
            self,
            channels: list[str],
    ) -> None:
        """Slot for setting the channel value names in the nuclei channel combobox."""
        while self.nuclear_detection_channel_widget.currentIndex() != -1:
            self.nuclear_detection_channel_widget.removeItem(0)
        for channel in channels:
            self.nuclear_detection_channel_widget.addItem(channel)
        self.on_params_changed()  # Emit signal as soon as new channels are set

    def on_fornma_checkbox_state_changed(self) -> None:
        """Sets the fornma_params_widget on/off, whenever the fornma_checkbox is clicked."""
        self.fornma_collapsable_button.setEnabled(self.fornma_checkbox.value())
        self.on_params_changed()  # Emit signal as soon as checkbox is clicked

    def on_cellpose_checkbox_state_changed(self) -> None:
        """Sets the cellpose_params_widget on/off, whenever the cellpose_checkbox is clicked."""
        self.cellpose_collapsable_button.setEnabled(self.cellpose_checkbox.value())
        self.on_params_changed()  # Emit signal as soon as checkbox is clicked

    def on_params_changed(
            self,
            _: Any = None,  # Parameter that has changed - we don't need it because we will get all parameters anyway
    ) -> None:
        """Emits all segmentation parameters at once."""
        params = {
            'global': self.get_global_params(),
            'fornma': self.get_fornma_params(),
            'cellpose': self.get_cellpose_params(),
        }
        self.segmentationParamsChanged.emit(params)

    def get_global_params(self) -> dict[str, Any]:
        """Returns the global segmentation parameters."""
        params = {
            self.nuclear_detection_channel_widget.objectName(): self.nuclear_detection_channel_widget.value(),
            self.output_folder_widget.objectName(): self.output_folder_widget.value(),
        }
        params.update(self.global_params_widget.get_values())
        return params

    def get_fornma_params(self) -> dict[str, Any]:
        """Returns the forNMA's segmentation parameters."""
        params = {self.fornma_checkbox.objectName(): self.fornma_checkbox.value()}
        params.update(self.fornma_params_widget.get_values())
        return params

    def get_cellpose_params(self) -> dict[str, Any]:
        """Returns the Cellpose's segmentation parameters."""
        params = {self.cellpose_checkbox.objectName(): self.cellpose_checkbox.value()}
        params.update(self.cellpose_params_widget.get_values())
        return params


class GlobalParamsWidget(qtw.QWidget):
    """Widget containing all global parameters in it."""
    paramsChanged = qtc.pyqtSignal(object)  # type does not matter
    _blueprint = (
        # Format: ( forNMA ID, add_slider, add_help )
        ('magnification', False, True),
        ('pixel_size', False, True),
        ('rescale_intensity', True, True),
        ('remove_background', True, True),
        ('radius_bg', True, True),
        ('shape', True, True),
        ('eccentricity', True, True),
        ('min_size', True, True),
        ('max_size', True, True),
        ('min_radius', True, True),
        ('max_radius', True, True),
    )

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a GlobalParamsWidget."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self._fornma_params = {}

        for fornma_id, add_slider, add_help in self._blueprint:
            fornma_widget = ForNMAWidget(fornma_id=fornma_id, add_slider=add_slider, add_help=add_help)
            layout.addWidget(fornma_widget)
            self._fornma_params[fornma_id] = fornma_widget
            if fornma_id == 'remove_background':  # Specific routing for remove background widget
                fornma_widget.valueChanged.connect(self.on_remove_background_checkbox_clicked)
            elif fornma_id in ('min_size', 'min_radius'):  # Specific routing for min size and min radius
                fornma_widget.valueChanged.connect(self.on_min_value_changed)
            elif fornma_id in ('max_size', 'max_radius'):  # Specific routing for max size and max radius
                fornma_widget.valueChanged.connect(self.on_max_value_changed)
            else:  # Generic routing for all other widgets
                fornma_widget.valueChanged.connect(self.paramsChanged)

        # Checks and unchecks the checkbox just to make sure that its sub-widgets are disabled
        offset_widget = self._fornma_params['remove_background']
        offset_widget.setChecked(True)
        offset_widget.setChecked(False)

    def get_values(self) -> dict[str, Any]:
        """Return the name and value of each forNMA parameter."""
        return {
            widget.objectName(): (widget.value() if widget.isEnabled() else None)
            for _, widget in self._fornma_params.items()
        }

    def on_remove_background_checkbox_clicked(
            self,
            checked: bool,
    ) -> None:
        """Enables/disables the rolling ball radius whenever the remove_background checkbox is clicked."""
        offset_widget = self._fornma_params['radius_bg']  # HARD-CODED: parameter name in blueprint must be exact!
        offset_widget.setEnabled(checked)
        self.paramsChanged.emit(checked)

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


class ForNMAParamsWidget(qtw.QWidget):
    """Widget containing all of forNMA's parameters in it."""
    paramsChanged = qtc.pyqtSignal(object)  # type does not matter
    _blueprint = (
        # Format: ( forNMA ID, add_slider, add_help )
        ('threshold', False, True),
        ('offset', False, True),
        ('blur', True, True),
        ('adjust_size', True, True),
        ('cut_edges', True, True),
        ('find_low_intensity_nucleus', True, True),
        ('weakly_labeled', True, True),
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

        for fornma_id, add_slider, add_help in self._blueprint:
            fornma_widget = ForNMAWidget(fornma_id=fornma_id, add_slider=add_slider, add_help=add_help)
            layout.addWidget(fornma_widget)
            self._fornma_params[fornma_id] = fornma_widget
            if fornma_id == 'threshold':  # Specific routing for threshold widget
                fornma_widget.valueChanged.connect(self.on_threshold_combobox_changed)
            else:  # Generic routing for all other widgets
                fornma_widget.valueChanged.connect(self.paramsChanged)

        # Final setup
        # Set threshold values
        threshold_widget = self._fornma_params['threshold']
        threshold_widget.setCurrentText(get_default_threshold())

    def get_values(self) -> dict[str, Any]:
        """Return the name and value of each forNMA parameter."""
        return {
            widget.objectName(): (widget.value() if widget.isEnabled() else None)
            for _, widget in self._fornma_params.items()
        }

    def on_threshold_combobox_changed(
            self,
            selected: str,
    ) -> None:
        """Enables/disables the threshold offset slider whenever the threshold combobox changes its value."""
        has_threshold = threshold_has_offset(threshold_name=selected)
        offset_widget = self._fornma_params['offset']  # HARD-CODED: parameter name in blueprint must be exact!
        offset_widget.setEnabled(has_threshold)
        self.paramsChanged.emit(selected)


class CellposeParamsWidget(qtw.QWidget):
    """Widget containing all of Cellpose's parameters in it."""
    paramsChanged = qtc.pyqtSignal(object)  # type does not matter
    _blueprint = (
        # Format: ( forNMA ID, add_slider, add_help )
        ('diameter', True, True),
        ('flow_threshold', True, True),
        ('mask_threshold', True, True),
        # ('use_gpu', False, True),
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

        for fornma_id, add_slider, add_help in self._blueprint:
            fornma_widget = ForNMAWidget(fornma_id=fornma_id, add_slider=add_slider, add_help=add_help)
            layout.addWidget(fornma_widget)
            self._fornma_params[fornma_id] = fornma_widget
            fornma_widget.valueChanged.connect(self.paramsChanged)

    def get_values(self) -> dict[str, Any]:
        """Return the name and value of each forNMA parameter."""
        return {
            widget.objectName(): (widget.value() if widget.isEnabled() else None)
            for _, widget in self._fornma_params.items()
        }
