"""helpers/folder_select_button.py - module containing a widget used to select a folder by clicking a button."""

from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw


class FolderSelectButton(qtw.QPushButton):
    """
    Class representing a button used to select a folder.
    Upon clicking the button, a folder selection dialog appears, and the selected folder is emitted.
    Additionally, it is able to store and emit a model's index.
    """
    folderSelected = qtc.Signal(qtc.QModelIndex, str)

    def __init__(
            self,
            parent: qtw.QWidget = None,
            index: qtc.QModelIndex = None,
    ) -> None:
        """Initializes a FolderSelectButton."""
        super().__init__(parent=parent)
        self.index = index
        self.set_icon(checked=False)
        self.set_tooltip(path='')
        self.clicked.connect(self.select_folder)  # noqa

    def select_folder(self) -> None:
        """Opens a FileDialog and emits a Signal containing the file path."""
        folder_path = qtw.QFileDialog.getExistingDirectory(self.parent(), "Select folder", "..") or ''
        self.set_icon(checked=bool(folder_path))
        self.set_tooltip(path=folder_path)
        self.folderSelected.emit(self.index, folder_path)

    def set_icon(
            self,
            checked: bool,
    ) -> None:
        """Sets the icon on the editor, given the checked boolean flag."""
        if checked is True:
            self.setIcon(self.style().standardIcon(getattr(qtw.QStyle, "SP_DialogOkButton")))
        else:
            self.setIcon(self.style().standardIcon(getattr(qtw.QStyle, "SP_DialogNoButton")))

    def set_tooltip(
            self,
            path: str,
    ) -> None:
        """Sets the tooltip text of the button."""
        if not path:
            self.setToolTip('Click to select folder...')
        else:
            self.setToolTip(f'Selected folder:\n{path}')
