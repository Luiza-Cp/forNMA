"""Interface/tabs/analysis/detection_page - contains the widgets used in forNMA's detection parameters page."""
from __future__ import annotations

from typing import Any

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import CollapsableWidget
from Interface.fornma_core import ForNMAWidget
from .base_parameters_page import BaseParametersPage


class DetectionParametersPage(BaseParametersPage):
    """Subclass of ParametersPage responsible for displaying the segmentation parameters."""
    channelsSet = qtc.pyqtSignal(list)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DetectionParametersPage instance."""
        params_widget = DetectionParametersWidget()
        super().__init__(title='Detection', params_widget=params_widget, parent=parent)

        # This connection servers as a "tunnel" in order to the channel names reach the params_widget
        self.channelsSet.connect(params_widget.set_channel_values)

        # Signal aliases
        self.detectionParamsChanged = params_widget.detectionParamsChanged


class DetectionParametersWidget(qtw.QWidget):
    """Class defining the layout and widgets for the detection parameters."""
    detectionParamsChanged = qtc.pyqtSignal(dict)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DetectionParametersWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self._channels = {}

    def set_channel_values(
            self,
            channels: list[str],
    ) -> None:
        """Slot for setting the channel value names in the nuclei channel combobox."""
        self._channels = {}
        self.clear_layout()
        layout = self.layout()
        for channel in channels:
            channel_widget = ChannelWidget(channel_name=channel)
            channel_widget.paramsChanged.connect(self.on_params_changed)
            layout.addWidget(CollapsableWidget(f'Channel: {channel}', widget_to_hide=channel_widget))
            self._channels[channel] = channel_widget
        layout.addStretch()
        self.on_params_changed()  # Emit signal as soon as new channels are set

    def on_params_changed(
            self,
            _: Any = None,  # Parameter that has changed - we don't need it because we will get all parameters anyway
    ) -> None:
        """Emits all detection parameters at once."""
        params = {
            f'Channel {channel}': channel_widget.get_values()
            for channel, channel_widget in self._channels.items()
        }
        self.detectionParamsChanged.emit(params)

    def clear_layout(
            self,
            layout: qtw.QWidget = None,
    ) -> None:
        """
        Recursively clears all widgets in the layout.
        Source: https://stackoverflow.com/a/23087057/11161432
        """
        layout = layout or self.layout()
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clear_layout(child.layout())


class ChannelWidget(qtw.QWidget):
    """Widget containing a channel's parameters in it."""
    paramsChanged = qtc.pyqtSignal(object)  # type does not matter  # TODO: CHECK HERE!!!!!
    _blueprint = (
        # Format: ( forNMA ID, add_slider, add_help)
        ('channel_rescale_intensity', False, True),
        ('remove_bg', False, True),
        ('channel_radius_bg', True, True),
        ('match_hist', False, True),
        ('wants_ktr', False, True),
        ('ring_size', True, True),
        ('use_ellipse', False, True),
        ('wants_foci', False, True),
        ('foci_min_size', True, True),
        ('foci_max_size', True, True),
        ('foci_min_int', True, True),
        ('foci_max_int', True, True),
        ('foci_prominence', True, True),
    )

    def __init__(
            self,
            channel_name: str = "",
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ChannelWidget."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self._channel_name = channel_name

        self._fornma_params = {}
        for fornma_id, add_slider, add_help in self._blueprint:
            fornma_widget = ForNMAWidget(fornma_id=fornma_id, add_slider=add_slider, add_help=add_help)
            layout.addWidget(fornma_widget)
            self._fornma_params[fornma_id] = fornma_widget
            if fornma_id == 'remove_bg':  # Specific routing for remove background widget
                fornma_widget.valueChanged.connect(self.on_remove_background_checkbox_clicked)
            elif fornma_id == 'wants_ktr':  # Specific routing for wants KTR widget
                fornma_widget.valueChanged.connect(self.on_wants_ktr_checkbox_clicked)
            elif fornma_id == 'wants_foci':  # Specific routing for wants Foci widget
                fornma_widget.valueChanged.connect(self.on_wants_foci_checkbox_clicked)
            elif fornma_id in ('foci_min_size', 'foci_min_int'):  # Specific routing for foci min size and foci min int
                fornma_widget.valueChanged.connect(self.on_min_value_changed)
            elif fornma_id in ('foci_max_size', 'foci_max_int'):  # Specific routing for foci min size and foci max int
                fornma_widget.valueChanged.connect(self.on_max_value_changed)
            else:  # Generic routing for all other widgets
                fornma_widget.valueChanged.connect(self.paramsChanged)

        # Final setup
        for widget_name in [  # Checks and unchecks the checkbox just to make sure that its sub-widgets are disabled
            'remove_bg',
            'wants_ktr',
            'wants_foci',
        ]:
            widget = self._fornma_params[widget_name]
            widget.setChecked(True)
            widget.setChecked(False)

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
        offset_widget = self._fornma_params['channel_radius_bg']  # HARD-CODED: parameter name in blueprint must match!
        offset_widget.setEnabled(checked)
        self.paramsChanged.emit(checked)

    def on_wants_ktr_checkbox_clicked(
            self,
            checked: bool,
    ) -> None:
        """Enables/disables the KTR widgets whenever the wants_ktr checkbox is clicked."""
        for widget_name in ['ring_size', 'use_ellipse']:  # HARD-CODED: names in blueprint must match!
            widget = self._fornma_params[widget_name]
            widget.setEnabled(checked)
        self.paramsChanged.emit(checked)

    def on_wants_foci_checkbox_clicked(
            self,
            checked: bool,
    ) -> None:
        """Enables/disables the Foci widgets whenever the wants_ktr checkbox is clicked."""
        for widget_name in [
            'foci_min_size',
            'foci_max_size',
            'foci_min_int',
            'foci_max_int',
            'foci_prominence',
        ]:  # HARD-CODED: names in blueprint must match!
            widget = self._fornma_params[widget_name]
            widget.setEnabled(checked)
        self.paramsChanged.emit(checked)

    def on_min_value_changed(
            self,
            new_value: float,
    ) -> None:
        """Changes the max value of the related widget if the min value is greater than it."""
        sender_name = self.sender().objectName()  # 'foci_min_size' or 'foci_min_int'
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
        sender_name = self.sender().objectName()  # 'foci_max_size' or 'foci_max_int'
        min_size_widget_name = sender_name.replace('max', 'min')
        min_size_widget = self._fornma_params[min_size_widget_name]
        if min_size_widget.value() > new_value:
            min_size_widget.setValue(new_value)
        self.paramsChanged.emit(new_value)
