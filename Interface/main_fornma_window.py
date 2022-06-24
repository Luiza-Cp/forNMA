"""main_fornma_window.py - file describing the main forNMA interface."""

from __future__ import annotations

import sys

from PySide6 import QtWidgets as qtw

from Interface.tabs import AnalysisParameters, AnalysisWidget, ExperimentDataParameters, ExperimentDataWidget


class ForNMAMainWindow(qtw.QMainWindow):
    """Class representing forNMA's main interface."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ForNMAMainWindow instance."""
        super().__init__(parent=parent)
        self.setMinimumSize(800, 600)

        # MAIN WIDGET
        self.main_widget = qtw.QWidget()
        self.setCentralWidget(self.main_widget)

        layout = qtw.QHBoxLayout()
        self.main_widget.setLayout(layout)

        # LEFT COLUMN
        self.stack = qtw.QStackedWidget()
        layout.addWidget(self.stack)

        self.data_params = ExperimentDataParameters()
        self.stack.addWidget(self.data_params)

        self.analysis_params = AnalysisParameters()
        self.stack.addWidget(self.analysis_params)

        # RIGHT COLUMN
        self.tabs = qtw.QTabWidget()
        layout.addWidget(self.tabs)

        self.data_tab = ExperimentDataWidget()
        self.tabs.addTab(self.data_tab, "Data")

        self.analysis_tab = AnalysisWidget()
        self.tabs.addTab(self.analysis_tab, "Analysis")

        # CONFIG
        self.tabs.currentChanged.connect(self.stack.setCurrentIndex)  # noqa
        layout.setStretch(0, 1)  # Use 1/4 of the available space for the left column
        layout.setStretch(1, 3)  # Use 3/4 of the available space for the right column


def fornma_interface_main():
    """Initializes the forNMA's interface in the main loop."""
    app = qtw.QApplication(sys.argv)
    window = ForNMAMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    fornma_interface_main()
