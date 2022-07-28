"""tabs/analysis.py - contains all widgets used in forNMA's "analysis" tab."""

from __future__ import annotations

from typing import Any

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import CollapsableButton
from Interface.tabs import BaseParametersPage


class DetectionParametersPage(BaseParametersPage):
    """Subclass of ParametersPage responsible for displaying the segmentation parameters."""
    channelsSet = qtc.Signal(list)
    detectionDataChanged = qtc.Signal(dict)

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
    detectionParamsChanged = qtc.Signal(dict)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DetectionParametersWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self._channels = {}

    @qtc.Slot(list)
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
            layout.addWidget(CollapsableButton(f'Channel: {channel}', widget_to_hide=channel_widget))
            self._channels[channel] = channel_widget
        layout.addStretch()

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
    paramsChanged = qtc.Signal(int)  # type does not matter

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

        # Mock values just for testing right now
        self.label = qtw.QLabel(f'{self._channel_name} Channel Parameters!')
        layout.addWidget(self.label)
        self.spinbox = qtw.QSpinBox()
        layout.addWidget(self.spinbox)
        self.spinbox.valueChanged.connect(self.paramsChanged)  # noqa

    def get_values(self) -> dict[str, Any]:
        """Return the name and value of each forNMA parameter."""
        return {'checkbox': self.spinbox.value()}
        # return {
        #     widget.objectName(): (widget.value() if widget.isEnabled() else None)
        #     for _, widget in self._fornma_params.items()
        # }
