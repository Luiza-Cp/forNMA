"""Interface/tabs/data/data_tab.py - contains the top-level widgets used in forNMA's "Data" tab."""
from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw

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


class DataAreaWidget(qtw.QWidget):
    """
    Class representing the widget on the right-hand side of the "data" tab,
    where the path to the forNMA's folders are set.
    """
    dataChanged = qtc.Signal()

    def __init__(
            self,
            parameters_widget: DataParametersWidget = None,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DataAreaWidget instance."""
        super().__init__(parent=parent)
        self.parameters = parameters_widget

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
        experiment_wizard = ExperimentWizard(self)
        if experiment_wizard.exec() == qtw.QDialog.Accepted:
            self.experiment_table.set_experiment(channels=experiment_wizard.channels, groups=experiment_wizard.groups)

    def has_at_least_one_path_button(self) -> bool:
        """Returns whether the experiment table has at least one FolderSelectButton in it."""
        return self.experiment_table.is_defined()

    def all_paths_are_defined(self) -> bool:
        """Returns whether the experiment table has at least one FolderSelectButton in it."""
        return self.experiment_table.paths_are_filled()
