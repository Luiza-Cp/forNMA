"""
Interface/main_fornma_window.py - file describing the main forNMA interface.
Execute this file directly to run forNMA's interface.
"""
from __future__ import annotations

import pprint
import sys
from typing import Type

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.custom_widgets import DraggableCanvasWidget, SlidingStackedWidget
from Interface.runner import Runner, fornma_mock_function
from Interface.tabs import (
    DataAreaWidget, DataParametersWidget,  # Data Tab
    AnalysisAreaWidget, AnalysisParametersWidget,  # Analysis Tab
    NMAAreaWidget, NMAParametersWidget,  # NMA Tab
)
from Interface.types import ForNMAEmitDict, ForNMAReturnDict

_DEBUG = True


class ForNMAMainWindow(qtw.QMainWindow):
    """Class representing forNMA's main interface."""
    _current_params = {}

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ForNMAMainWindow instance."""
        super().__init__(parent=parent)
        self.setMinimumSize(1200, 800)

        self.threadpool = qtc.QThreadPool(self)
        self._canvas_window = None  # Placeholder

        # MAIN WIDGET
        self.main_widget = qtw.QWidget()
        self.setCentralWidget(self.main_widget)
        # Layout
        layout = qtw.QHBoxLayout()
        self.main_widget.setLayout(layout)

        # LEFT COLUMN
        self.stack = SlidingStackedWidget()
        layout.addWidget(self.stack)
        # Stack 01
        self.data_params = DataParametersWidget()
        self.stack.addWidget(self.data_params)
        # Stack 02
        self.analysis_params = AnalysisParametersWidget()
        self.stack.addWidget(self.analysis_params)
        # Stack 03
        self.nma_params = NMAParametersWidget()
        self.stack.addWidget(self.nma_params)

        # RIGHT COLUMN
        self.tabs = qtw.QTabWidget()
        layout.addWidget(self.tabs)
        # Tab 01
        self.data_area = DataAreaWidget()
        self.tabs.addTab(self.data_area, "Data")
        # Tab 02
        self.analysis_area = AnalysisAreaWidget()
        self.tabs.addTab(self.analysis_area, "Analysis")
        self.tabs.setTabEnabled(1, False)  # Analysis tab starts disabled
        # Tab 03
        self.nma_area = NMAAreaWidget()
        self.tabs.addTab(self.nma_area, "NMA")

        # Establish connections across widgets
        self.data_area.pathsChanged.connect(self.data_params.setPaths)
        self.data_area.dataChanged.connect(self.on_data_tab_changed)
        self.tabs.tabBarClicked.connect(self.on_tab_bar_clicked)  # noqa
        self.tabs.currentChanged.connect(self.stack.slideInIndex)  # noqa
        self.analysis_params.segmentationParamsChanged.connect(self.on_analysis_params_changed)
        self.analysis_params.detectionParamsChanged.connect(self.on_analysis_params_changed)
        self.analysis_params.preview_button.clicked.connect(self.on_preview_button_clicked)
        self.analysis_params.run_button.clicked.connect(self.on_run_button_clicked)

        # Set column sizes
        layout.setStretch(0, 4)  # Use 4/10 of the available space for the left column
        layout.setStretch(1, 6)  # Use 6/10 of the available space for the right column

    # CONNECTIONS --------------------------------------------------------------
    def on_data_tab_changed(self) -> None:
        """Enables or disables the Analysis tab whenever the content of the Data tab is updated."""
        if not self.data_area.has_at_least_one_path_button():
            self.tabs.setTabEnabled(1, False)
        elif not self.data_area.all_paths_are_defined():
            self.tabs.setTabEnabled(1, False)
        else:
            self.tabs.setTabEnabled(1, True)
            self.analysis_params.channelsSet.emit(self.data_area.channel_names)

    def on_tab_bar_clicked(
            self,
            index: int,
    ) -> None:
        """Displays useful messages whenever a disabled tab in the bar is clicked."""
        if index == -1:  # clicked on disabled tab
            if not self.data_area.has_at_least_one_path_button():
                qtw.QMessageBox.information(self, "No experiment table", "Please create an experiment table")
            elif not self.data_area.all_paths_are_defined():
                qtw.QMessageBox.information(self, "Undefined paths", "Please define a path for all channels and groups")

    def on_analysis_params_changed(
            self,
            new_segmentation_params: dict,
    ) -> None:
        """Updates the current_params dictionary whenever one of the underlying parameter changes."""
        self._current_params.update(new_segmentation_params)
        self.analysis_params.setText(self._current_params)

    def on_preview_button_clicked(self) -> None:
        """Runs fornma in Preview mode."""
        params = self._current_params.copy()
        params['preview'] = True
        # ##### MUDAR AQUI - pegar o dicionário de params e passar para a função do forNMA
        print(f"RUNNING FORNMA WITH PARAMETERS: {pprint.pformat(self._current_params)}")

    def on_run_button_clicked(self) -> None:
        """Runs fornma in Run mode."""
        params = self._current_params.copy()
        runner = Runner(func=fornma_mock_function, kwargs=params)
        runner.signals.started.connect(self.on_fornma_started_signal)
        runner.signals.callback.connect(self.on_fornma_callback_received)
        runner.signals.error.connect(self.on_fornma_error_signal)
        runner.signals.success.connect(self.on_fornma_success_signal)
        runner.signals.finished.connect(self.on_fornma_finished_signal)
        self.threadpool.start(runner)

    # RUN ----------------------------------------------------------------------
    def on_fornma_started_signal(self) -> None:
        """Handles the started signal emitted by forNMA's runner."""
        self.analysis_area.reset_log()
        self.analysis_area.write_title('forNMA started Executing!')

    def on_fornma_callback_received(
            self,
            callback: ForNMAEmitDict,
    ) -> None:
        """Handles the callback received by forNMA's runner."""
        _type = callback['type']
        if _type == 'progress':
            progress = callback['data'].pop()
            self.analysis_area.update_progress_bar(progress)
        elif _type == 'log':
            self.analysis_area.write_message(message=callback['message'])
            for thing in callback['data']:
                self.analysis_area.write_message(message=thing)
        elif _type == 'warning':
            self.analysis_area.write_warning(message=callback['message'])
            for thing in callback['data']:
                self.analysis_area.write_warning(message=thing)
        else:
            print(f'Unhandled callback: {callback}')

    def on_fornma_error_signal(
            self,
            exception_tuple: tuple[Type[Exception], str],
    ) -> None:
        """Handles the error signal emitted by forNMA's runner."""
        exception, trace = exception_tuple
        message = f'forNMA reached an error during execution:\n{exception}\n\nFullTraceback:\n{trace}'
        qtw.QMessageBox.critical(self, 'Error!', message, qtw.QMessageBox.Ok)  # noqa

    def on_fornma_success_signal(
            self,
            return_value: ForNMAReturnDict,
    ) -> None:
        """Handles the success signal emitted by forNMA's runner (containing the return value)."""
        self._canvas_window = DraggableCanvasWidget(data=return_value['data'].pop())
        if self._canvas_window.exec() == qtw.QDialog.Accepted:
            data = self._canvas_window.get_data()
            message = f'{return_value["message"]}\n\nFiltered Data:\n\n{data}'
            qtw.QMessageBox.information(self, 'Success!', message, qtw.QMessageBox.Ok)
        else:
            qtw.QMessageBox.information(self, 'Aborted!', 'User decided to cancel operation.', qtw.QMessageBox.Ok)

    def on_fornma_finished_signal(self) -> None:
        """Handles the finished signal emitted by forNMA's runner."""
        self.analysis_area.write_title('forNMA finished Executing!')
        self.analysis_area.reset_progress_bar()
        qtc.QTimer.singleShot(5_000, self.analysis_area.write_default_text)

    # DEBUG --------------------------------------------------------------------
    def debug(self) -> None:
        """Starts up forNMA's interface in debug mode."""
        # Simulates selecting the channels and groups names from the "Set experiment..." button
        channels = ['Red', 'Green', 'Phase']
        groups = ['Control', 'TMZ']
        self.data_area.experiment_table.set_experiment(channels=channels, groups=groups)
        # Simulates selecting the channel/group paths on the ExperimentTable by clicking in each button
        for column_idx, channel_name in enumerate(channels, 1):
            for row_idx, group_name in enumerate(groups):
                value = f'path/to/{channel_name.lower()}/{group_name.lower()}'
                index = self.data_area.experiment_table.model().index(row_idx, column_idx)  # Gets the index
                self.data_area.experiment_table.model().setData(index, value)  # Sets model data
                self.data_area.experiment_table.indexWidget(index).set_icon(True)  # Sets button icon to "OK"
                self.data_area.experiment_table.indexWidget(index).set_tooltip(value)  # Sets button icon to "OK"


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
