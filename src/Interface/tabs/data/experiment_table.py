"""
Interface/tabs/data/experiment_table.py - contains the widgets used to
define the experiment table in forNMA's "Data" tab.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6 import QtCore as qtc, QtWidgets as qtw

from src.Interface.custom_widgets import FolderSelectButton


class ExperimentTableWidget(qtw.QTableView):
    """Class representing a table where the experiment is described (channels/groups and their respective paths)."""
    pathsChanged = qtc.Signal(str)
    dataChanged = qtc.Signal()

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an ExperimentTableWidget instance."""
        super().__init__(parent=parent)

        self._model = ExperimentTableModel()
        self._channels = None
        self._groups = None
        self.setModel(self._model)
        self._model.dataChanged.connect(self.on_model_data_changed)  # noqa

    def set_experiment(
            self,
            channels: list[str],
            groups: list[str],
    ) -> None:
        """Sets the table layout, given the channels and groups list."""
        if not channels and not groups:  # No info received, do nothing
            return
        self._channels = channels
        self._groups = groups
        # Sets the model data
        self._model.set_data_from_lists(channels=channels, groups=groups)
        # Sets the buttons for the channel columns
        for row_index in range(self.nrows):
            for column_index in range(1, self.ncols):  # Skip first column
                index = self._model.index(row_index, column_index)
                button = FolderSelectButton(parent=self, index=index)
                self.setIndexWidget(index, button)
                button.folderSelected.connect(self._model.setData)
        self.horizontalHeader().setSectionResizeMode(qtw.QHeaderView.Stretch)

    @property
    def nrows(self) -> int:
        """Returns the number of rows in the Model."""
        return self._model.nrows

    @property
    def ncols(self) -> int:
        """Returns the number of columns in the Model."""
        return self._model.ncols

    @property
    def channel_names(self) -> list[str]:
        """Returns the channel names from the ExperimentTable."""
        return self._channels

    def is_defined(self) -> bool:
        """Returns whether the ExperimentTable id defined, i.e. has channels on its columns and groups on its rows."""
        return self.nrows > 0 and self.ncols > 1

    def path_data(self) -> list[dict[str, str]]:
        """Returns the path data as a dictionary."""
        model_data = self._model.as_dataframe().set_index('Group')
        return [
            {
                'channel': channel,
                'group': group,
                'path': model_data.at[group, channel],
            }
            for channel in self._channels
            for group in self._groups
        ]

    def paths_are_filled(self) -> bool:
        """Returns True if all paths in the current ExperimentTable have been selected."""
        paths = [data['path'] for data in self.path_data()]
        if not paths:
            return False
        return all(paths)

    @qtc.Slot(qtc.QModelIndex, qtc.QModelIndex, list)
    def on_model_data_changed(
            self,
            top_left: qtc.QModelIndex,      # These parameters are not used in the method,       # noqa
            bottom_right: qtc.QModelIndex,  # but are present in the model's dataChanged signal  # noqa
            roles: list[int],               # so we must add them here                           # noqa
    ) -> None:
        """Emits a signal containing a formatted string whenever the underlying model's data changes."""
        text = self._model.as_textbox()
        self.pathsChanged.emit(text)
        self.dataChanged.emit()
        self.horizontalHeader().setSectionResizeMode(qtw.QHeaderView.Stretch)


class ExperimentTableModel(qtc.QAbstractTableModel):
    """Model used for the ExperimentTableWidget."""
    def __init__(
            self,
            data: pd.DataFrame = None,
    ) -> None:
        """Initializes an ExperimentTableModel."""
        super().__init__()
        self._data = data or pd.DataFrame()

    def as_dataframe(self) -> pd.DataFrame:
        """Returns the DataFrame representation of the Model's data."""
        return self._data

    def as_textbox(self) -> str:
        """Returns a string version of the data contained in the Model."""
        s = 'Selected Folders:\n\n'
        for index, row in self._data.iterrows():
            group_name, *channels = row
            s += f'Group: {group_name}\n\n'
            for channel_label, channel_path in zip(self._data.columns[1:], channels):
                s += f'  -> {channel_label}: {channel_path or "UNDEFINED"}\n'
            s += '-----\n\n'
        return s[:-1]  # Remove the last newline

    @property
    def nrows(self) -> int:
        """Returns the number of rows in the Model."""
        return self._data.shape[0]

    @property
    def ncols(self) -> int:
        """Returns the number of columns in the Model."""
        return self._data.shape[1]

    def flags(
            self,
            index: qtc.QModelIndex | qtc. QPersistentModelIndex,
    ) -> int:
        """Returns the model's flags."""
        if index.column() == 0:
            return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsSelectable
        else:
            return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsSelectable | qtc.Qt.ItemIsEditable

    def rowCount(  # noqa
            self,
            parent: qtc.QModelIndex = None,
    ) -> int:
        """Returns the number of rows in the model."""
        return self._data.shape[0]

    def columnCount(  # noqa
            self,
            parent: qtc.QModelIndex = None,
    ) -> int:
        """Returns the number of columns in the model."""
        return self._data.shape[1]

    def data(
            self,
            index: qtc.QModelIndex | qtc.QPersistentModelIndex,
            role: int = qtc.Qt.DisplayRole,
    ) -> str | None:
        """Returns the model's data, at the given index and for the specific role."""
        if index.isValid():
            if role == qtc.Qt.DisplayRole:  # Display on the view as plain text
                value = self._data.iloc[index.row(), index.column()]
                return str(value)
            if role == qtc.Qt.EditRole:  # Edit on the view (i.e. a PushButton)
                value = self._data.iloc[index.row(), index.column()]
                return str(value)

    def setData(
            self,
            index: qtc.QModelIndex | qtc.QPersistentModelIndex,
            value: Any,
            role: int = qtc.Qt.DisplayRole,
    ) -> bool:
        """Sets the model's data, at the given index and for the specific role."""
        if index.isValid():
            if role == qtc.Qt.DisplayRole:
                self._data.iloc[index.row(), index.column()] = value
            elif role == qtc.Qt.EditRole:
                self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [qtc.Qt.DisplayRole, qtc.Qt.EditRole])  # noqa
            return True
        return False

    def headerData(
            self,
            idx: int,
            orientation: qtc.Qt.Orientation,
            role: int = qtc.Qt.DisplayRole,
    ) -> str | None:
        """Returns the model's header data (column names and row indices)."""
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
        """Completely replaces the underlying pandas DataFrame of the model."""
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

    def set_data_from_lists(
            self,
            channels: list[str],
            groups: list[str],
    ) -> None:
        data = {channel: '' for channel in channels}
        data['Group'] = groups
        columns = ['Group'] + channels
        new_data = pd.DataFrame(data=data, columns=columns, dtype=str)
        self.refresh_data(new_data=new_data)
