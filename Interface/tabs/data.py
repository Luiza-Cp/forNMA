"""main_fornma_window.py - file describing the main forNMA interface."""

from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.utils import ExperimentTableWidget, SetExperimentDialog


class ExperimentDataWidget(qtw.QWidget):
    """Class representing a widget where the main forNMA's data is set."""
    dataChanged = qtc.Signal()

    def __init__(
            self,
            parameters: ExperimentDataParameters = None,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an ExperimentDataWidget instance."""
        super().__init__(parent=parent)
        self.parameters = parameters

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self.set_experiment_dialog = None  # Placeholder for SetExperimentDialog

        self.experiment_table = ExperimentTableWidget()
        layout.addWidget(self.experiment_table)

        self.set_experiment_button = qtw.QPushButton("Set experiment data ...")
        self.set_experiment_button.clicked.connect(self.set_experiment)  # noqa
        layout.addWidget(self.set_experiment_button)

        self.experiment_table.pathsChanged.connect(self.parameters.setPaths)
        self.experiment_table.dataChanged.connect(self.dataChanged)

    @property
    def channel_names(self) -> list[str]:
        """Returns the names of the channels defined in the ExperimentTable."""
        return self.experiment_table.channel_names

    def set_experiment(self) -> None:
        """Opens a SetExperimentDialog and returns its value to the interface."""
        dialog = SetExperimentDialog(self)
        if dialog.exec() == qtw.QDialog.Accepted:
            self.experiment_table.set_experiment(channels=dialog.channels, groups=dialog.groups)

    def has_at_least_one_path_button(self) -> bool:
        """Returns whether the experiment table has at least one FolderSelectButton in it."""
        return self.experiment_table.is_defined()

    def all_paths_are_defined(self) -> bool:
        """Returns whether the experiment table has at least one FolderSelectButton in it."""
        return self.experiment_table.paths_are_filled()


class ExperimentDataParameters(qtw.QWidget):
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        super().__init__(parent=parent)
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.label = qtw.QLabel('Welcome to forNMA!')
        self.label.setStyleSheet('QLabel {font-size: 24px}')
        self.label.setAlignment(qtc.Qt.AlignCenter)  # noqa
        layout.addWidget(self.label)

        self.paths_label = qtw.QLabel("")
        self.paths_label.setWordWrap(True)
        layout.addWidget(self.paths_label)

    @qtc.Slot(str)
    def setPaths(
            self,
            paths: str,
    ) -> None:
        """Sets the received paths onto the label."""
        self.paths_label.setText(paths)
