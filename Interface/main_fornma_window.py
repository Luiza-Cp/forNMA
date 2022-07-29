"""main_fornma_window.py - file describing the main forNMA interface."""

from __future__ import annotations

import pprint
import sys

from PySide6 import QtWidgets as qtw

from Interface.custom_widgets import SlidingStackedWidget
from Interface.tabs import AnalysisAreaWidget, AnalysisParametersWidget, DataAreaWidget, DataParametersWidget

_DEBUG = True


class ForNMAMainWindow(qtw.QMainWindow):
    _current_params = {}
    """Class representing forNMA's main interface."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ForNMAMainWindow instance."""
        super().__init__(parent=parent)
        self.setMinimumSize(1200, 800)

        # MAIN WIDGET
        self.main_widget = qtw.QWidget()
        self.setCentralWidget(self.main_widget)
        # Layout
        layout = qtw.QHBoxLayout()
        self.main_widget.setLayout(layout)

        # LEFT COLUMN
        self.stack = SlidingStackedWidget()
        layout.addWidget(self.stack)
        # Page 01
        self.data_params = DataParametersWidget()
        self.stack.addWidget(self.data_params)
        # Page 02
        self.analysis_params = AnalysisParametersWidget()
        self.stack.addWidget(self.analysis_params)

        # RIGHT COLUMN
        self.tabs = qtw.QTabWidget()
        layout.addWidget(self.tabs)
        # Page 01
        self.data_tab = DataAreaWidget(parameters_widget=self.data_params)
        self.tabs.addTab(self.data_tab, "Data")
        # Page 02
        self.analysis_tab = AnalysisAreaWidget()
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.setTabEnabled(1, False)  # Analysis tab starts disabled

        # CONFIG
        self.data_tab.dataChanged.connect(self.on_data_tab_changed)  # noqa
        self.tabs.tabBarClicked.connect(self.on_tab_bar_clicked)  # noqa
        self.tabs.currentChanged.connect(self.stack.slideInIndex)  # noqa
        self.analysis_params.segmentationParamsChanged.connect(self.on_analysis_params_changed)
        self.analysis_params.detectionParamsChanged.connect(self.on_analysis_params_changed)
        self.analysis_params.preview_button.clicked.connect(self.on_preview_button_clicked)
        self.analysis_params.run_button.clicked.connect(self.on_run_button_clicked)
        layout.setStretch(0, 4)  # Use 4/10 of the available space for the left column
        layout.setStretch(1, 6)  # Use 6/10 of the available space for the right column

    def on_analysis_params_changed(
            self,
            new_segmentation_params: dict,
    ) -> None:
        self._current_params.update(new_segmentation_params)
        self.analysis_params.setText(self._current_params)

    def on_preview_button_clicked(self) -> None:
        params = self._current_params.copy()
        params['preview'] = True
        # ##### MUDAR AQUI - pegar o dicionário de params e passar para a função do forNMA
        print(f"RUNNING FORNMA WITH PARAMETERS: {pprint.pformat(self._current_params)}")

    def on_run_button_clicked(self) -> None:
        params = self._current_params.copy()
        params['preview'] = False
        # ##### MUDAR AQUI - pegar o dicionário de params e passar para a função do forNMA
        print(f"RUNNING FORNMA WITH PARAMETERS: {pprint.pformat(self._current_params)}")

    def on_data_tab_changed(self) -> None:
        """Enables or disables the Analysis tab whenever the content of the Data tab is updated."""
        if not self.data_tab.has_at_least_one_path_button():
            self.tabs.setTabEnabled(1, False)
        elif not self.data_tab.all_paths_are_defined():
            self.tabs.setTabEnabled(1, False)
        else:
            self.tabs.setTabEnabled(1, True)
            self.analysis_params.channelsSet.emit(self.data_tab.channel_names)

    def on_tab_bar_clicked(
            self,
            index: int,
    ) -> None:
        """Displays useful messages whenever a disabled tab in the bar is clicked."""
        if index == -1:  # clicked on disabled tab
            if not self.data_tab.has_at_least_one_path_button():
                qtw.QMessageBox.information(self, "No experiment table", "Please create an experiment table")
            elif not self.data_tab.all_paths_are_defined():
                qtw.QMessageBox.information(self, "Undefined paths", "Please define a path for all channels and groups")

    def debug(self) -> None:
        """Starts up forNMA's interface in debug mode."""
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
                self.data_tab.experiment_table.indexWidget(index).set_tooltip(value)  # Sets button icon to "OK"


def fornma_interface_main(debug: bool):
    """Initializes forNMA's interface in the main loop."""
    app = qtw.QApplication(sys.argv)
    window = ForNMAMainWindow()
    window.show()
    if debug is True:
        window.debug()
    sys.exit(app.exec())


if __name__ == '__main__':
    fornma_interface_main(debug=_DEBUG)
