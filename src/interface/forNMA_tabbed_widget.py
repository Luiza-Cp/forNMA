from typing import Optional

from PyQt5 import QtWidgets as qtw  # noqa


class ForNMATabbedWidget(qtw.QTabWidget):
    """Class representing tabbed widget placed in the center of forNMA's interface."""
    def __init__(
            self,
            parent: Optional[qtw.QWidget] = None,
    ):
        """Initializes an ForNMATabbedWidget instance."""
        super().__init__(parent=parent)

        # Main tab
        self.main_tab = qtw.QWidget()
        self.addTab(self.main_tab, 'Main')

        # Errors tab
        self.errors_tab = qtw.QWidget()
        self.addTab(self.errors_tab, 'Errors')
        self.setTabEnabled(1, False)

        # Analysis tab
        self.analysis_tab = qtw.QWidget()
        self.addTab(self.analysis_tab, 'Analysis')
        self.setTabEnabled(2, False)
