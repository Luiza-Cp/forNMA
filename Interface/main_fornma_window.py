"""main_fornma_window.py - file describing the main forNMA interface."""

from __future__ import annotations

import sys

from PySide6 import QtWidgets as qtw

from Interface.tabs import AnalysisParameters, AnalysisWidget, ExperimentDataParameters, ExperimentDataWidget

DEBUG = True


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
        left_column = qtw.QVBoxLayout()
        layout.addLayout(left_column)

        self.stack = qtw.QStackedWidget()
        left_column.addWidget(self.stack)
        # Page 01
        self.data_params = ExperimentDataParameters()
        self.stack.addWidget(self.data_params)
        # Page 02
        self.analysis_params = AnalysisParameters()
        self.stack.addWidget(self.analysis_params)
        # Run button
        self.run_button = qtw.QPushButton("Run forNMA")
        left_column.addWidget(self.run_button)

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

    def debug(self) -> None:
        """Starts up the forNMA interface in debug mode."""
        # Simulates selecting the channels and groups names from the "Set experiment..." button
        channels = ['Red', 'Green', 'Phase']
        groups = ['Control', 'TMZ']
        self.data_tab.experiment_table.set_experiment(channels=channels, groups=groups)
        # Simulates selecting the channel/group paths on the ExperimentTable by clicking in each button
        for column_idx, channel_name in enumerate(channels, 1):
            for row_idx, group_name in enumerate(groups):
                value = f'path/to/{channel_name.lower()}/{group_name.lower()}'
                index = self.data_tab.experiment_table.model().index(row_idx, column_idx)  # Gets the index
                self.data_tab.experiment_table.model().setData(index, value)  # Sets model data
                self.data_tab.experiment_table.indexWidget(index).set_icon(True)  # Sets button icon to "OK"


def fornma_interface_main(debug: bool):
    """Initializes the forNMA's interface in the main loop."""
    app = qtw.QApplication(sys.argv)
    window = ForNMAMainWindow()
    window.show()
    if debug is True:
        window.debug()
    sys.exit(app.exec())


if __name__ == '__main__':
    fornma_interface_main(debug=DEBUG)
