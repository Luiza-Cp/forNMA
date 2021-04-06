from typing import Dict, Optional, Tuple

from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa

from src.interface.helpers.collapsible_widget import CollapsibleWidget
from src.interface.layouts.advanced_settings_layout import AdvancedSettingsLayout
from src.interface.layouts.basic_settings_layout import BasicSettingsLayout
from src.interface.layouts.input_selection_layout import InputSelectionLayout


class SettingsWidget(qtw.QWidget):
    """
    Class representing a vertical menu where the user is able to choose the settings for the forNMA analysis.
    Meant to be used as a DockWidget in the forNMA's interface.
    """
    def __init__(
            self,
            parent: Optional[qtw.QWidget] = None,
    ):
        """Initializes a SettingsWidget instance."""
        super().__init__(parent=parent)

        # Main Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Top label
        self.top_label = qtw.QLabel('Load images and select settings here')
        layout.addWidget(self.top_label)

        # Settings frame
        self.settings_frame = qtw.QFrame()
        self.settings_frame.setFrameStyle(1)
        layout.addWidget(self.settings_frame)

        # Frame layout
        frame_layout = qtw.QVBoxLayout()
        self.settings_frame.setLayout(frame_layout)

        # Input selection
        self.input_selection_layout = InputSelectionLayout()
        self.input_selection_widget = CollapsibleWidget(self.input_selection_layout, title='Input Selection')
        frame_layout.addWidget(self.input_selection_widget)

        # Basic settings
        self.basic_settings_layout = BasicSettingsLayout()
        self.basic_settings_widget = CollapsibleWidget(self.basic_settings_layout, title='Basic Settings')
        frame_layout.addWidget(self.basic_settings_widget)

        # Remove errors checkbox
        self.remove_errors_checkbox = qtw.QCheckBox('Remove errors')
        frame_layout.addWidget(self.remove_errors_checkbox)

        # Fast detection checkbox
        self.fast_detection_checkbox = qtw.QCheckBox('Fast detection')
        frame_layout.addWidget(self.fast_detection_checkbox)

        # Enable advanced settings checkbox
        self.enable_advanced_settings_checkbox = qtw.QCheckBox('Enable advanced settings')
        frame_layout.addWidget(self.enable_advanced_settings_checkbox)

        # Advanced settings
        self.advanced_settings_layout = AdvancedSettingsLayout()
        self.advanced_settings_widget = CollapsibleWidget(self.advanced_settings_layout, title='Advanced Settings')
        self.advanced_settings_widget.setVisible(False)  # starts hidden
        frame_layout.addWidget(self.advanced_settings_widget)

        # Connect enable advanced settings checkbox to advanced settings widget
        self.enable_advanced_settings_checkbox.toggled.connect(self.advanced_settings_widget.setVisible)

        # Add stretch before
        layout.addStretch()
        # Preview/Run buttons
        button_layout = qtw.QHBoxLayout()
        self.preview_button = qtw.QPushButton('Preview', clicked=self.on_preview_button_clicked)  # noqa
        button_layout.addWidget(self.preview_button)
        self.run_button = qtw.QPushButton('Run', clicked=self.on_run_button_clicked)  # noqa
        button_layout.addWidget(self.run_button)
        layout.addLayout(button_layout)

    # TODO: implement preview functionality!
    @qtc.pyqtSlot()
    def on_preview_button_clicked(self) -> None:
        """Previews the analysis to be performed by forNMA."""
        print('Settings from Input Selection:')
        print(self.input_selection_layout.retrieveSettings())
        print('Settings from Basic Settings:')
        print(self.basic_settings_layout.retrieveSettings())
        print(f'Remove errors: {self.remove_errors_checkbox.isChecked()}')
        print(f'Fast detection: {self.fast_detection_checkbox.isChecked()}')
        advanced_settings_enabled = self.enable_advanced_settings_checkbox.isChecked()
        print(f'Enable advanced settings: {advanced_settings_enabled}')
        print('Settings from Advanced Settings:')
        advanced_settings = self.advanced_settings_layout.retrieveSettings() if advanced_settings_enabled else {}
        print(advanced_settings)

    # TODO: implement run functionality!
    @qtc.pyqtSlot()
    def on_run_button_clicked(self) -> Tuple[Dict, Dict, Dict, bool, bool]:
        """Runs the analysis to be performed by forNMA."""
        input_settings = self.input_selection_layout.retrieveSettings()
        basic_settings = self.basic_settings_layout.retrieveSettings()
        advanced_settings_enabled = self.enable_advanced_settings_checkbox.isChecked()
        advanced_settings = self.advanced_settings_layout.retrieveSettings() if advanced_settings_enabled else {}
        remove_errors = self.remove_errors_checkbox.isChecked()
        fast_detection = self.fast_detection_checkbox.isChecked()
        return input_settings, basic_settings, advanced_settings, remove_errors, fast_detection
