from typing import Optional

from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa


class InputTableWidget(qtw.QTableWidget):
    """
    Class representing a table containing information of the input files for analysis.
    Meant to be used as a tab in ForNMATabbedWidget.
    """
    def __init__(
            self,
            parent: Optional[qtw.QWidget] = None,
    ):
        """Initializes an InputTableWidget instance."""
        super().__init__(parent=parent)

        self.setRowCount(0)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['Folder name', 'Channel', 'Time', 'Treatment'])
