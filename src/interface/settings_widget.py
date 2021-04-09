from typing import Dict, Optional, Tuple

from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa

from src.interface.dialogs.folder_input_dialog import FolderInputDialog
from src.interface.helpers.collapsible_widget import CollapsibleWidget
from src.interface.helpers.scrollable_frame import ScrollableFrame
from src.interface.layouts.advanced_settings_layout import AdvancedSettingsLayout
from src.interface.layouts.basic_settings_layout import BasicSettingsLayout


class SettingsWidget(qtw.QWidget):
    """
    Class representing a vertical menu where the user is able to choose the settings for the forNMA analysis.
    Meant to be used as a DockWidget in the forNMA's interface.
    """
    folderSelected = qtc.pyqtSignal(dict)

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

        # Load data button
        self.load_button = qtw.QPushButton('Load data...', clicked=self.on_load_button_clicked)  # noqa
        layout.addWidget(self.load_button)

        # Scrollable frame
        self.frame = ScrollableFrame()
        layout.addWidget(self.frame)

        # Basic settings
        self.basic_settings_widget = CollapsibleWidget(BasicSettingsLayout(), title='Basic Settings')
        self.frame.layout.addWidget(self.basic_settings_widget)
        # self.basic_settings_widget.click()  # starts open

        # Add some spacing between basic settings and checkboxes
        self.frame.layout.addStretch()

        # Remove errors checkbox
        self.remove_errors_checkbox = qtw.QCheckBox('Remove errors')
        self.frame.layout.addWidget(self.remove_errors_checkbox)

        # Fast detection checkbox
        self.fast_detection_checkbox = qtw.QCheckBox('Fast detection')
        self.frame.layout.addWidget(self.fast_detection_checkbox)

        # Enable advanced settings checkbox
        self.enable_advanced_settings_checkbox = qtw.QCheckBox('Enable advanced settings')
        self.frame.layout.addWidget(self.enable_advanced_settings_checkbox)

        # Advanced settings
        self.advanced_settings_widget = CollapsibleWidget(AdvancedSettingsLayout(), title='Advanced Settings')
        self.advanced_settings_widget.setVisible(False)  # starts hidden
        self.frame.layout.addWidget(self.advanced_settings_widget)

        # Preview/Run buttons layout
        button_layout = qtw.QHBoxLayout()
        layout.addLayout(button_layout)

        # Preview button
        self.preview_button = qtw.QPushButton('Preview', clicked=self.on_preview_button_clicked)  # noqa
        button_layout.addWidget(self.preview_button)

        # Run button
        self.run_button = qtw.QPushButton('Run', clicked=self.on_run_button_clicked)  # noqa
        button_layout.addWidget(self.run_button)

        # Connect enable advanced settings checkbox to advanced settings widget
        self.enable_advanced_settings_checkbox.toggled.connect(self.advanced_settings_widget.setVisible)

    @qtc.pyqtSlot()
    def on_load_button_clicked(self) -> None:
        """Prompts the user to select a folder for the forNMA analysis"""
        dialog = FolderInputDialog()
        if (result := dialog.exec_()) is not None:
            self.folderSelected.emit(result)

    # TODO: implement preview functionality!
    @qtc.pyqtSlot()
    def on_preview_button_clicked(self) -> None:
        """Previews the analysis to be performed by forNMA."""
        print('Basic settings selected:')
        print(self.basic_settings_widget.retrieve_settings())
        print(f'Remove errors: {self.remove_errors_checkbox.isChecked()}')
        print(f'Fast detection: {self.fast_detection_checkbox.isChecked()}')
        advanced_settings_enabled = self.enable_advanced_settings_checkbox.isChecked()
        print(f'Enable advanced settings: {advanced_settings_enabled}')
        print('Advanced settings selected:')
        advanced_settings = self.advanced_settings_widget.retrieve_settings() if advanced_settings_enabled else {}
        print(advanced_settings)

    # TODO: implement run functionality!
    @qtc.pyqtSlot()
    def on_run_button_clicked(self) -> Tuple[Dict, Dict, bool, bool]:
        """Runs the analysis to be performed by forNMA."""
        basic_settings = self.basic_settings_widget.retrieve_settings()
        advanced_settings_enabled = self.enable_advanced_settings_checkbox.isChecked()
        advanced_settings = self.advanced_settings_widget.retrieve_settings() if advanced_settings_enabled else {}
        remove_errors = self.remove_errors_checkbox.isChecked()
        fast_detection = self.fast_detection_checkbox.isChecked()
        return basic_settings, advanced_settings, remove_errors, fast_detection
