from PyQt5 import QtWidgets as qtw  # noqa

from src.interface.helpers.int_combo_box import IntComboBox
from src.interface.layouts.key_grid_layout import KeyGridLayout


class InputSelectionLayout(KeyGridLayout):
    """
    Class representing a layout for selecting user input.
    Meant to be added to as a collapsible layout under forNMA's SettingsWidget.
    """
    nuclear_detection_combobox_items = [
        'Channel 1',
        'Channel 2',
    ]
    magnification_combobox_items = [
        '5',
        '10',
        '20',
        '60',
        '100',
    ]
    pixel_size_spinbox_values = {
        'minimum':    0.001,
        'maximum':    1.000,
        'singleStep': 0.010,
        'value':      0.500,
    }

    def __init__(self):
        """Initializes a InputSelectionLayout instance."""
        super().__init__()

        # Load data button
        self.load_button = qtw.QPushButton('Load data...', clicked=self.on_load_button_clicked)  # noqa
        self.addWidget(self.load_button, self.next_row, 0, 1, 2)

        # Load data spinbox
        self.load_label = qtw.QLabel('')
        self.addWidget(self.load_label, self.next_row, 0, 1, 2)

        # Nuclear detection combobox
        self.addWidget(qtw.QLabel('Nuclear detection'), self.next_row, 0, 1, 2)
        self.nuclear_detection_combobox = qtw.QComboBox(objectName='nuclear detection')  # noqa
        for item in self.nuclear_detection_combobox_items:
            self.nuclear_detection_combobox.addItem(item)
        self.addKeyWidget(self.nuclear_detection_combobox, self.next_row, 1, 1, 1)

        # Magnification combobox
        self.addWidget(qtw.QLabel('Magnification'), self.next_row, 0, 1, 2)
        self.magnification_combobox = IntComboBox(objectName='magnification')  # noqa
        for item in self.magnification_combobox_items:
            self.magnification_combobox.addItem(item)
        self.addKeyWidget(self.magnification_combobox, self.next_row, 1, 1, 1)

        # Pixel size spinbox
        self.addWidget(qtw.QLabel('Pixel size'), self.next_row, 0, 1, 2)
        self.pixel_size_spinbox = qtw.QDoubleSpinBox(objectName='pixel size', **self.pixel_size_spinbox_values)  # noqa
        self.addKeyWidget(self.pixel_size_spinbox, self.next_row, 1, 1, 1)

    # TODO: implement proper input handling!
    def on_load_button_clicked(self) -> None:
        """Prompts the user to select a folder for the forNMA analysis"""
        query = qtw.QFileDialog.getExistingDirectory(None, 'Select folder', options=qtw.QFileDialog.DontUseNativeDialog)
        if query:
            self.load_label.setText(query)
