"""experiment_table.py - module bundling the necessary widgets for forNMA's ExperimentTable."""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6 import QtCore as qtc, QtWidgets as qtw

from Interface.helpers import FolderSelectButton


class ExperimentTableWidget(qtw.QTableView):
    """Class representing a table where the experiment is described (channels/groups and their respective paths)."""
    pathsChanged = qtc.Signal(str)

    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes an ExperimentTableWidget instance."""
        super().__init__(parent=parent)

        self._model = ExperimentTableModel()
        self.setModel(self._model)
        self._model.dataChanged.connect(self.on_model_data_changed)

    def set_experiment(
            self,
            channels: list[str],
            groups: list[str],
    ) -> None:
        """Sets the table layout, given the channels and groups list."""
        if not channels and not groups:  # No info received, do nothing
            return
        channel_labels = [f'Channel {channel}' for channel in channels]
        # Sets the model data
        data = {channel: '' for channel in channel_labels}
        data['Group'] = groups
        columns = ['Group'] + channel_labels
        data = pd.DataFrame(data=data, columns=columns, dtype=str)
        self._model.refresh_data(new_data=data)
        # Sets the buttons for the channel columns
        for row_index in range(data.shape[0]):
            for column_index in range(1, data.shape[1]):  # Skip first column
                index = self._model.index(row_index, column_index)
                button = FolderSelectButton(parent=self, index=index)
                button.folderSelected.connect(self._model.setData)
                self.setIndexWidget(index, button)
        # Sets the table header
        self.horizontalHeader().setSectionResizeMode(qtw.QHeaderView.Stretch)
        self.resizeColumnsToContents()

    @qtc.Slot(pd.DataFrame)
    def on_model_data_changed(
            self,
            data: pd.DataFrame,
    ) -> None:
        """Emits a signal containing a formatted string whenever the underlying model's data changes."""
        s = ''
        for index, row in data.iterrows():
            group_name, *channels = row
            s += f'Group: {group_name}\n'
            for channel_label, channel_path in zip(data.columns[1:], channels):
                s += f'  -> {channel_label}: {channel_path or "UNDEFINED"}\n'
            s += '-----\n'
        self.pathsChanged.emit(s[:-1])


class ExperimentTableModel(qtc.QAbstractTableModel):
    """Model used for the ExperimentTableWidget."""
    dataChanged = qtc.Signal(pd.DataFrame)

    def __init__(
            self,
            data: pd.DataFrame = None,
    ) -> None:
        """Initializes an ExperimentTableModel."""
        super().__init__()
        self._data = data or pd.DataFrame()

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
            self.dataChanged.emit(self._data)
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
