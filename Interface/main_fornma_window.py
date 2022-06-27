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
        # Layout
        layout = qtw.QHBoxLayout()
        self.main_widget.setLayout(layout)

        # LEFT COLUMN
        self.stack = qtw.QStackedWidget()
        layout.addWidget(self.stack)
        # Page 01
        self.data_params = ExperimentDataParameters()
        self.stack.addWidget(self.data_params)
        # Page 02
        self.analysis_params = AnalysisParameters()
        self.stack.addWidget(self.analysis_params)

        # RIGHT COLUMN
        self.tabs = qtw.QTabWidget()
        layout.addWidget(self.tabs)
        # Page 01
        self.data_tab = ExperimentDataWidget(parameters=self.data_params)
        self.tabs.addTab(self.data_tab, "Data")
        # Page 02
        self.analysis_tab = AnalysisWidget()
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.setTabEnabled(1, False)  # Analysis tab starts disabled

        # CONFIG
        self.data_tab.dataChanged.connect(self.on_data_tab_changed)  # noqa
        self.tabs.tabBarClicked.connect(self.on_tab_bar_clicked)  # noqa
        self.tabs.currentChanged.connect(self.stack.setCurrentIndex)  # noqa
        layout.setStretch(0, 1)  # Use 1/4 of the available space for the left column
        layout.setStretch(1, 3)  # Use 3/4 of the available space for the right column

    def on_data_tab_changed(self) -> None:
        """Enables or disables the Analysis tab whenever the content of the Data tab is updated."""
        if not self.data_tab.has_at_least_one_path_button():
            self.tabs.setTabEnabled(1, False)
        elif not self.data_tab.all_paths_are_defined():
            self.tabs.setTabEnabled(1, False)
        else:
            self.tabs.setTabEnabled(1, True)
            self.analysis_params.set_channel_values(self.data_tab.channel_names)

    def on_tab_bar_clicked(
            self,
            index: int,
    ) -> None:
        """Displays useful messages whenever the tab bar is clicked."""
        if index == -1:  # clicked on disabled tab
            if not self.data_tab.has_at_least_one_path_button():
                qtw.QMessageBox.information(self, "No experiment table", "Please create an experiment table")
            elif not self.data_tab.all_paths_are_defined():
                qtw.QMessageBox.information(self, "Undefined paths", "Please define a path for all channels and groups")


def fornma_interface_main():
    """Initializes the forNMA's interface in the main loop."""
    app = qtw.QApplication(sys.argv)
    window = ForNMAMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    fornma_interface_main()
