from typing import Dict, Optional

from PyQt5 import QtCore as qtc, QtGui as qtg, QtWidgets as qtw  # noqa


class InputTableWidget(qtw.QWidget):
    """
    Class representing a table containing information of the input files for analysis.
    Meant to be used as a tab in ForNMATabbedWidget.
    """
    column_names = [
        'Channel 1',
        'Channel 2',
        'Name',
        'Time',
        'Treatment'
    ]
    rowAdded = qtc.pyqtSignal(int, str, str, str, str, str)

    def __init__(
            self,
            parent: Optional[qtw.QWidget] = None,
            row_count: int = 0,
            column_count: int = 5,
    ) -> None:
        """Initializes an InputTableWidget instance."""
        super().__init__(parent=parent)

        self.menu = None  # Placeholder

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Time checkbox
        self.time_checkbox = qtw.QCheckBox('Use time column')
        layout.addWidget(self.time_checkbox)

        # Treatment checkbox
        self.treatment_checkbox = qtw.QCheckBox('Use treatment column')
        layout.addWidget(self.treatment_checkbox)

        # Table
        self.table = qtw.QTableWidget()
        layout.addWidget(self.table)

        # Table setup
        self.table.setRowCount(row_count)
        self.table.setColumnCount(column_count)
        self.table.setHorizontalHeaderLabels(self.column_names)
        self.create_all_table_items()
        self.set_column_as_read_only(column_name='Channel 1')
        self.set_column_as_read_only(column_name='Channel 2')

        self.table.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.right_click_menu)

        # Connections
        self.time_checkbox.toggled.connect(self.toggle_time_column)
        self.treatment_checkbox.toggled.connect(self.toggle_treatment_column)
        self.rowAdded.connect(self.on_row_added)

    def right_click_menu(
            self,
            point: qtc.QPoint,
    ) -> None:
        """Implements the menu that appears whenever the user right-clicks on the table."""
        row_position = point.y()
        self.menu = qtw.QMenu()
        delete_action = qtw.QAction('Delete')
        delete_action.triggered.connect(lambda: self.delete_row(row_position))
        self.menu.addAction(delete_action)
        self.menu.exec_(qtg.QCursor.pos())

    def delete_row(
            self,
            row_position: int,
    ) -> None:
        """Deletes a row from the table."""
        row_index = self.table.rowAt(row_position)
        confirm_message_box = qtw.QMessageBox(  # noqa
            text=f'Confirm row deletion',
            informativeText=f'Are you sure you want to delete row {row_index + 1}? This action cannot be undone.',
            standardButtons=qtw.QMessageBox.Ok | qtw.QMessageBox.No,
        )
        confirm_message_box.setDefaultButton(qtw.QMessageBox.No)
        if confirm_message_box.exec_() == qtw.QMessageBox.Ok:
            self.table.removeRow(row_index)

    def create_all_table_items(self) -> None:
        """Populates the table with items containing empty strings."""
        for row_index in range(self.table.rowCount()):
            for column_index in range(self.table.columnCount()):
                self.setItem(row_index, column_index, qtw.QTableWidgetItem(''))

    def set_column_as_read_only(
            self,
            column_name: str,
    ) -> None:
        """Given a column name, sets all items in the column as read-only."""
        column_index = self.get_column_index_from_name(column_name=column_name)
        self.table.setItemDelegateForColumn(column_index, ReadOnlyDelegate(self))

    def get_column_index_from_name(
            self,
            column_name: str,
    ) -> int:
        """Given a column name, returns its index in the table (raises a ValueError if the column name is not found)."""
        try:
            column_index = self.column_names.index(column_name)
        except ValueError:  # column not found, re-raising error
            raise ValueError(f'Column not found in table: {column_name}')
        return column_index

    @qtc.pyqtSlot(dict)
    def add_row_from_dict(
            self,
            row_dict: Dict[str, str],
    ) -> None:
        """Adds the data from the row_dict as a new row to the table."""
        self.add_row(**row_dict)

    def add_row(
            self,
            channel_1: str,
            channel_2: str,
            name: str = '',
            time: str = '',
            treatment: str = '',
    ) -> None:
        """Adds the data as a new row to the table."""
        if time:
            self.time_checkbox.setChecked(True)
        if treatment:
            self.treatment_checkbox.setChecked(True)
        self.table.insertRow(last_row := self.table.rowCount())
        self.rowAdded.emit(last_row, channel_1, channel_2, name, time, treatment)

    @qtc.pyqtSlot(int, str, str, str, str, str)
    def on_row_added(
            self,
            last_row: int,
            channel_1: str,
            channel_2: str,
            name: str,
            time: str,
            treatment: str,
    ) -> None:
        """Updates the table UI whenever a new row is added onto it."""
        self.table.setItem(last_row, 0, qtw.QTableWidgetItem(channel_1))
        self.table.setItem(last_row, 1, qtw.QTableWidgetItem(channel_2))
        self.table.setItem(last_row, 2, qtw.QTableWidgetItem(name))
        self.table.setItem(last_row, 3, qtw.QTableWidgetItem(time))
        self.table.setItem(last_row, 4, qtw.QTableWidgetItem(treatment))
        self.toggle_time_column(toggle=self.time_checkbox.isChecked())
        self.toggle_treatment_column(toggle=self.treatment_checkbox.isChecked())

    @qtc.pyqtSlot(bool)
    def toggle_time_column(
            self,
            toggle: bool,
    ) -> None:
        """
        Activates/deactivates the time column, based on the toggle boolean value.
        The boolean value is meant to be sent from a QCheckbox checked() signal.
        """
        self.toggle_column(column_name='Time', toggle=toggle)

    @qtc.pyqtSlot(bool)
    def toggle_treatment_column(
            self,
            toggle: bool,
    ) -> None:
        """
        Activates/deactivates the treatment column, based on the toggle boolean value.
        The boolean value is meant to be sent from a QCheckbox checked() signal.
        """
        self.toggle_column(column_name='Treatment', toggle=toggle)

    def toggle_column(
            self,
            toggle: bool,
            column_name: str,
    ) -> None:
        """
        Activates/deactivates the treatment column items and header, based on the toggle boolean value.
        The boolean value is meant to be sent from a QCheckbox checked() signal.
        """
        self.toggle_items(column_name=column_name, toggle=toggle)
        self.toggle_header(column_name=column_name, toggle=toggle)

    def toggle_items(
            self,
            toggle: bool,
            column_name: str,
    ) -> None:
        """
        Activates/deactivates a column's items given its index, and based on the toggle boolean value.
        The boolean value is meant to be sent from a QCheckbox checked() signal.
        """
        column_index = self.get_column_index_from_name(column_name=column_name)
        for row_index in range(self.table.rowCount()):
            if (item := self.table.item(row_index, column_index)) is not None:
                for flag in (qtc.Qt.ItemIsEditable, qtc.Qt.ItemIsEnabled):
                    if toggle is False:
                        item.setFlags(item.flags() & ~flag)  # noqa
                    else:
                        item.setFlags(item.flags() | flag)  # noqa

    def toggle_header(
            self,
            toggle: bool,
            column_name: str,
    ) -> None:
        """
        Activates/deactivates a column's header given its index, and based on the toggle boolean value.
        The boolean value is meant to be sent from a QCheckbox checked() signal.
        """
        column_index = self.get_column_index_from_name(column_name=column_name)
        header_item = self.table.horizontalHeaderItem(column_index)
        for flag in (qtc.Qt.ItemIsEnabled,):
            if toggle is False:
                header_item.setFlags(header_item.flags() & ~flag)  # noqa
            else:
                header_item.setFlags(header_item.flags() | flag)  # noqa


class ReadOnlyDelegate(qtw.QStyledItemDelegate):
    """
    Turns a QTableItem non-editable (read-only).
    source: https://stackoverflow.com/questions/56882925/change-editability-for-individual-cells-of-qtablewidget
    """
    def createEditor(
            self,
            parent: qtw.QWidget,
            option: qtw.QStyleOptionViewItem,
            index: qtc.QModelIndex,
    ) -> None:
        """Always returns None in order to make an item non-editable (read-only)."""
