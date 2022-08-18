"""Interface/tabs/data/data_tab.py - contains the top-level widgets used in forNMA's "Data" tab."""
from __future__ import annotations

from PyQt5 import QtCore as qtc, QtWidgets as qtw

from .experiment_table import ExperimentTableWidget
from .experiment_wizard import ExperimentWizard


class DataParametersWidget(qtw.QWidget):
    """
    Class representing the widget on the left-hand side of the "data" tab,
    where the paths to forNMA's folders are displayed.
    """
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DataParametersWidget."""
        super().__init__(parent=parent)
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.welcome_label = qtw.QLabel('Welcome to forNMA!')
        self.welcome_label.setStyleSheet('QLabel {font-size: 24px}')
        self.welcome_label.setAlignment(qtc.Qt.AlignCenter)
        layout.addWidget(self.welcome_label)

        self.paths_label = qtw.QLabel("")
        self.paths_label.setStyleSheet('QLabel {font-size: 16px}')
        self.paths_label.setWordWrap(True)
        layout.addWidget(self.paths_label)

        layout.addStretch()

    def setPaths(
            self,
            paths: str,
    ) -> None:
        """Sets the received paths onto the label."""
        self.paths_label.setText(paths)


class DataAreaWidget(qtw.QWidget):
    """
    Class representing the widget on the right-hand side of the "data" tab,
    where the path to the forNMA's folders are set.
    """

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DataAreaWidget instance."""
        super().__init__(parent=parent)

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self.set_experiment_dialog = None  # Placeholder for SetExperimentDialog

        self.experiment_table = ExperimentTableWidget()
        layout.addWidget(self.experiment_table)

        self.set_experiment_button = qtw.QPushButton("Set experiment data ...")
        self.set_experiment_button.clicked.connect(self.set_experiment)
        layout.addWidget(self.set_experiment_button)

        # aliases
        self.pathsChanged = self.experiment_table.pathsChanged
        self.dataChanged = self.experiment_table.dataChanged

    @property
    def channel_names(self) -> list[str]:
        """Returns the names of the channels defined in the ExperimentTable."""
        return self.experiment_table.channel_names

    def set_experiment(self) -> None:
        """Opens a SetExperimentDialog and returns its value to the interface."""
        experiment_wizard = ExperimentWizard(self)
        if experiment_wizard.exec() == qtw.QDialog.Accepted:
            self.experiment_table.set_experiment(channels=experiment_wizard.channels, groups=experiment_wizard.groups)

    def has_at_least_one_path_button(self) -> bool:
        """Returns whether the experiment table has at least one FolderSelectButton in it."""
        return self.experiment_table.is_defined()

    def all_paths_are_defined(self) -> bool:
        """Returns whether the experiment table has at least one FolderSelectButton in it."""
        return self.experiment_table.paths_are_filled()
