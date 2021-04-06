from typing import Optional

from PyQt5 import QtWidgets as qtw  # noqa

from src.interface.input_table_widget import InputTableWidget


class ForNMATabbedWidget(qtw.QTabWidget):
    """Class representing tabbed widget placed in the center of forNMA's interface."""
    def __init__(
            self,
            parent: Optional[qtw.QWidget] = None,
    ):
        """Initializes an ForNMATabbedWidget instance."""
        super().__init__(parent=parent)

        # Input table tab
        self.input_table_tab = InputTableWidget()
        self.addTab(self.input_table_tab, 'Input data')

        # Images tab
        self.images_tab = qtw.QWidget()
        self.addTab(self.images_tab, 'Images')
        self.setTabEnabled(1, False)

        # Errors tab
        self.errors_tab = qtw.QWidget()
        self.addTab(self.errors_tab, 'Errors')
        self.setTabEnabled(2, False)

        # Analysis tab
        self.analysis_tab = qtw.QWidget()
        self.addTab(self.analysis_tab, 'Analysis')
        self.setTabEnabled(3, False)
