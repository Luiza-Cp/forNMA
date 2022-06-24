"""main_fornma_window.py - file describing the main forNMA interface."""

from __future__ import annotations

from PySide6 import QtWidgets as qtw

from Interface.utils import ExperimentTableWidget, SetExperimentDialog


class ExperimentDataParameters(qtw.QWidget):
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        super().__init__(parent=parent)
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.label = qtw.QLabel('DataParameters')
        layout.addWidget(self.label)


class ExperimentDataWidget(qtw.QWidget):
    """Class representing a widget where the main forNMA's data is set."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an ExperimentDataWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self.set_experiment_dialog = None  # Placeholder for SetExperimentDialog

        self.experiment_table = ExperimentTableWidget()
        layout.addWidget(self.experiment_table)

        self.set_experiment_button = qtw.QPushButton("Set experiment data ...")
        self.set_experiment_button.clicked.connect(self.set_experiment)  # noqa
        layout.addWidget(self.set_experiment_button)

        self.paths_label = qtw.QLabel("")
        self.experiment_table.pathsChanged.connect(self.paths_label.setText)
        layout.addWidget(self.paths_label)

    def set_experiment(self) -> None:
        """Opens a SetExperimentDialog and returns its value to the interface."""
        dialog = SetExperimentDialog(self)
        if dialog.exec() == qtw.QDialog.Accepted:
            self.experiment_table.set_experiment(channels=dialog.channels, groups=dialog.groups)
