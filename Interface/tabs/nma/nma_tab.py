"""Interface/tabs/nma/nma_tab.py - contains the top-level widgets used in forNMA's "NMA" tab."""
from __future__ import annotations

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import LogAreaWidget, RowLayout


class NMAParametersWidget(qtw.QWidget):
    """
    Class representing the widget on the left-hand side of the "NMA" tab,
    where the settings for the NMA analysis are set.
    """
    fileListChanged = qtc.pyqtSignal(object)  # List of file names

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a NMAParametersWidget."""
        super().__init__(parent=parent)
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.title = qtw.QLabel('Welcome to NMA!')
        self.title.setStyleSheet('QLabel {font-size: 24px}')
        self.title.setAlignment(qtc.Qt.AlignCenter)
        layout.addWidget(self.title)

        self.label = qtw.QLabel('In order to perform NMA, please select the forNMA output files:')
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        self.file_list = qtw.QListWidget()
        self.file_list.setSelectionMode(qtw.QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.file_list)

        # Buttons
        self.remove_button = qtw.QPushButton('Remove highlighted files')
        self.remove_button.clicked.connect(self.remove_highlighted_files)
        self.add_button = qtw.QPushButton('Add files...')
        self.add_button.clicked.connect(self.add_files)
        self.run_button = qtw.QPushButton('Run NMA')
        # Button row
        button_row = RowLayout(widgets=[self.remove_button, self.add_button, 'stretch', self.run_button])
        layout.addLayout(button_row)

    def get_file_names(self) -> list[str]:
        """Returns the current file names in the file list."""
        return [
            self.file_list.item(i).text()
            for i in range(self.file_list.count())
        ]

    def remove_highlighted_files(self) -> None:
        """Removes the highlighted files from the file list."""
        indices_to_remove = [
            i
            for i in range(self.file_list.count())
            if self.file_list.item(i).isSelected()
        ]
        for i in reversed(indices_to_remove):
            item = self.file_list.takeItem(i)
            del item
        self.fileListChanged.emit(self.get_file_names())

    def add_files(self) -> None:
        """Selects files and adds them to the file list."""
        files, _ = qtw.QFileDialog.getOpenFileNames(self, "Select files", filter='Table files (*.xlsx *.csv)')
        existing_files = self.get_file_names()
        for file in files:
            if file not in existing_files:
                self.file_list.addItem(file)
        self.fileListChanged.emit(self.get_file_names())


class NMAAreaWidget(qtw.QWidget):
    """
    Class representing the widget on the right-hand side of the "NMA" tab,
    where the NMA plots are displayed.
    """
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a NMAAreaWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Log Area
        self.log_area = LogAreaWidget(default_text='Select the files for NMA analysis on the left')
        layout.addWidget(self.log_area)

        # Aliases
        self.write_default_text = self.log_area.write_default_text
        self.write_message = self.log_area.write_message
