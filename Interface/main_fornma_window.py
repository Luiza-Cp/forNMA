"""main_fornma_window.py - file describing the main forNMA interface."""

from __future__ import annotations

import sys
from functools import partial
from typing import Any

import pandas as pd
from PyQt5 import QtWidgets as qtw, QtCore as qtc


class ForNMAMainWindow(qtw.QMainWindow):
    """Class representing the forNMA's main interface."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
            flags: qtc.Qt.QWindowFlags | qtc.Qt.WindowType = qtc.Qt.WindowFlags(),
    ) -> None:
        """Initializes a ForNMAMainWindow instance."""
        super().__init__(parent=parent, flags=flags)

        self.widget = ExperimentWidget()
        self.setCentralWidget(self.widget)


class ExperimentWidget(qtw.QWidget):
    """Class representing a widget where the main forNMA's experiment is set."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an ExperimentWidget instance."""
        super().__init__(parent=parent)  # noqa

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)
        self.set_experiment_dialog = None  # Placeholder for SetExperimentDialog

        self.experiment_table = qtw.QTableView()
        self.model = PandasModel()
        self.experiment_table.setModel(self.model)
        self.delegate = Delegate(self.experiment_table)
        self.experiment_table.setItemDelegateForColumn(1, self.delegate)
        layout.addWidget(self.experiment_table)  # noqa

        self.set_experiment_button = qtw.QPushButton("Set experiment")
        self.set_experiment_button.clicked.connect(self.set_experiment)  # noqa
        layout.addWidget(self.set_experiment_button)  # noqa

    def set_experiment(self) -> None:
        """Opens a SetExperimentDialog and returns its value to the interface."""
        dialog = SetExperimentDialog(self)
        if dialog.exec() == qtw.QDialog.Accepted:
            self.write_to_table(data=dialog.as_table())

    def write_to_table(
            self,
            data: pd.DataFrame,
    ) -> None:
        """Writes the data to the experiment table."""
        self.model.refresh_data(new_data=data)
        self.experiment_table.horizontalHeader().setSectionResizeMode(qtw.QHeaderView.Stretch)
        self.experiment_table.resizeColumnsToContents()


class SetExperimentDialog(qtw.QWizard):
    """Class representing a dialog wizard used to set the current experiment value."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a SetExperimentDialog instance."""
        super().__init__(parent=parent)  # noqa
        self.data = None

        # ### PAGE ONE
        self.channel_page = LabelPage(label_name='Channel')
        self.addPage(self.channel_page)

        # ### PAGE TWO
        self.group_page = LabelPage(label_name='Group')
        self.addPage(self.group_page)

    def as_table(self) -> pd.DataFrame:
        """Returns the data collected from the dialog pages."""
        channels = self.channel_page.get_labels()
        groups = self.group_page.get_labels()
        if not channels and not groups:  # No info received
            return pd.DataFrame()
        return pd.DataFrame(data={'Group': groups}, columns=['Group'] + [f'Channel: {channel}' for channel in channels])


class LabelPage(qtw.QWizardPage):
    """Class representing a list of labels that can expand or contract when clicking buttons."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
            label_name: str = '',
    ) -> None:
        """Initializes a LabelList instance."""
        super().__init__(parent=parent)  # noqa

        self.line_edits = []

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.add_button = qtw.QPushButton(f'Add {label_name}')
        self.add_button.clicked.connect(self.add)  # noqa
        layout.addWidget(self.add_button)  # noqa

        layout.addStretch()

    def get_labels(self) -> list[str]:
        """Returns the labels currently in the LabelList. Ignores line edits with empty strings in them."""
        labels = []
        for line_edit in self.line_edits:
            label_text = line_edit.text()
            if label_text:
                labels.append(label_text)
        return labels

    def add(self) -> None:
        """Adds a DeletableLabel to the LabelList."""
        label = DeletableLabel()
        self.layout().insertWidget(len(self.line_edits), label)
        self.line_edits.append(label.line_edit)
        label.deleted.connect(partial(self.remove, label))

    def remove(
            self,
            label: DeletableLabel,
    ) -> None:
        """Removes the DeletableLabel from the LabelList."""
        self.line_edits.remove(label.line_edit)
        self.layout().removeWidget(label)
        label.setParent(None)


class DeletableLabel(qtw.QWidget):
    """Class representing a QLineEdit with a QPushButton that deletes it."""
    deleted = qtc.pyqtSignal(name='lineEditDeleted')

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DeletableLineEdit instance."""
        super().__init__(parent=parent)  # noqa

        layout = qtw.QHBoxLayout()
        self.setLayout(layout)

        self.line_edit = qtw.QLineEdit()
        layout.addWidget(self.line_edit)  # noqa

        self.delete_button = qtw.QPushButton()
        self.delete_button.setIcon(self.style().standardIcon(getattr(qtw.QStyle, "SP_DialogDiscardButton")))
        layout.addWidget(self.delete_button)  # noqa
        self.delete_button.clicked.connect(self.deleted.emit)  # noqa


class PandasModel(qtc.QAbstractTableModel):
    def __init__(
            self,
            data: pd.DataFrame = None,
    ) -> None:
        super().__init__()
        self._data = data or pd.DataFrame()

    def flags(
        self,
        index: qtc.QModelIndex | qtc. QPersistentModelIndex,
    ) -> int:
        if index.column() == 0:
            return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsSelectable
        else:
            return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsSelectable | qtc.Qt.ItemIsEditable

    def rowCount(  # noqa
            self,
            parent: qtc.QModelIndex = None,
    ) -> int:
        return self._data.shape[0]

    def columnCount(  # noqa
            self,
            parent: qtc.QModelIndex = None,
    ) -> int:
        return self._data.shape[1]

    def data(
        self,
        index: qtc.QModelIndex | qtc.QPersistentModelIndex,
        role: int = qtc.Qt.DisplayRole,
    ) -> str | None:
        value = str(self._data.iloc[index.row(), index.column()])  # Ignore falsy values like np.nan
        if index.isValid() and role == qtc.Qt.DisplayRole:
            return value

    def setData(
            self,
            index: qtc.QModelIndex | qtc.QPersistentModelIndex,
            value: Any,
            role: int = qtc.Qt.DisplayRole,
    ) -> bool:
        if index.isValid() and role == qtc.Qt.DisplayRole:
            self._data.iloc[index.row(), index.column()] = value
            return True
        return False

    def headerData(
        self,
        idx: int,
        orientation: qtc.Qt.Orientation,
        role: int = qtc.Qt.DisplayRole,
    ) -> str | None:
        if orientation == qtc.Qt.Horizontal and role == qtc.Qt.DisplayRole:
            return self._data.columns[idx]
        elif orientation == qtc.Qt.Vertical and role == qtc.Qt.DisplayRole:
            return self._data.index[idx]
        else:
            return None

    def refresh_data(
            self,
            new_data: pd.DataFrame,
    ) -> None:
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class Delegate(qtw.QItemDelegate):
    def __init__(self, parent=None):
        qtw.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        editor = qtw.QPushButton(parent)
        return editor

    def setEditorData(self, editor, index):
        model_value = index.model().data(index, qtc.Qt.EditRole)
        current_index = editor.findText(model_value)
        if current_index > 0:
            editor.setCurrentIndex(current_index)

    def setModelData(self, editor, model, index):
        editor_value = editor.currentText()
        model.setData(index, editor_value, qtc.Qt.EditRole)


def fornma_interface_main():
    """Initializes the forNMA's interface in the main loop."""
    app = qtw.QApplication(sys.argv)
    window = ForNMAMainWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    fornma_interface_main()
