from functools import partial
from typing import Dict, Optional

from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa


class FolderInputDialog(qtw.QDialog):
    """
    Class representing a dialog box that asks for input folders.
    Meant to be created by the InputSelectionLayout.
    """
    row_dict = {}

    def __init__(self, *args, **kwargs):
        """Initializes a FolderInputDialog instance."""
        super().__init__(*args, **kwargs)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Channel 1 line edit
        self.channel_1_line_edit = qtw.QLineEdit(  # noqa
            text=self.row_dict.setdefault('channel_1', ''),
            objectName='channel_1',
            textChanged=self.update_row_dict
        )

        # Channel 1 folder
        self.channel_1_button = qtw.QPushButton(  # noqa
            'Channel 1',
            clicked=partial(self.get_folder, self.channel_1_line_edit),
        )

        # Add channel 1 widgets to layout (inverse order)
        layout.addWidget(self.channel_1_button)
        layout.addWidget(self.channel_1_line_edit)

        # Channel 2 line edit
        self.channel_2_line_edit = qtw.QLineEdit(  # noqa
            text=self.row_dict.setdefault('channel_2', ''),
            objectName='channel_2',
            textChanged=self.update_row_dict
        )

        # Channel 2 folder button
        self.channel_2_button = qtw.QPushButton(  # noqa
            'Channel 2 (optional)',
            clicked=partial(self.get_folder, self.channel_2_line_edit),
        )

        # Add channel 2 widgets to layout (inverse order)
        layout.addWidget(self.channel_2_button)
        layout.addWidget(self.channel_2_line_edit)

        # Select name label
        layout.addWidget(qtw.QLabel('Name (optional)'))

        # Select name line edit
        self.name_line_edit = qtw.QLineEdit(  # noqa
            text=self.row_dict.setdefault('name', ''),
            objectName='name',
            textChanged=self.update_row_dict
        )
        layout.addWidget(self.name_line_edit)

        # Select time label
        layout.addWidget(qtw.QLabel('Time (optional)'))

        # Select time line edit
        self.time_line_edit = qtw.QLineEdit(  # noqa
            text=self.row_dict.setdefault('time', ''),
            objectName='time',
            textChanged=self.update_row_dict
        )
        layout.addWidget(self.time_line_edit)

        # Select treatment label
        layout.addWidget(qtw.QLabel('Treatment (optional)'))

        # Select treatment line edit
        self.treatment_line_edit = qtw.QLineEdit(  # noqa
            text=self.row_dict.setdefault('treatment', ''),
            objectName='treatment',
            textChanged=self.update_row_dict
        )
        layout.addWidget(self.treatment_line_edit)

        # Accept/reject button layout
        button_layout = qtw.QHBoxLayout()
        layout.addLayout(button_layout)

        # Reject button
        self.reject_button = qtw.QPushButton('Cancel', clicked=self.reject)  # noqa
        button_layout.addWidget(self.reject_button)

        # Accept button
        self.accept_button = qtw.QPushButton('Ok', clicked=self.accept)  # noqa
        button_layout.addWidget(self.accept_button)

    @qtc.pyqtSlot()
    def get_folder(
            self,
            line_edit: qtw.QLineEdit,
    ) -> None:
        """Asks the user for a folder and sets its path onto the line edit."""
        query = qtw.QFileDialog.getExistingDirectory(
            None,
            'Select folder',
            options=qtw.QFileDialog.DontUseNativeDialog
        )
        line_edit.setText(query)

    @qtc.pyqtSlot(str)
    def update_row_dict(
            self,
            text: str,
    ) -> None:
        """Updates the row dict whenever a line edit's value is changed."""
        key = self.sender().objectName()
        self.row_dict[key] = text

    def exec_(self) -> Optional[Dict[str, str]]:
        """
        Overridden method from qtw.QDialog.
        Executes the dialog box and returns a dictionary of the dialog's values, if it was accepted.
        """
        if super().exec_() == qtw.QDialog.Accepted:
            self.check_channel_1()
            return self.row_dict.copy()  # do not further modify the row_dict
        return None

    def check_channel_1(self) -> None:
        """Raises a ValueError if the Channel 1 folder path has not been chosen."""
        if 'channel_1' not in self.row_dict or self.row_dict['channel_1'] == '':
            raise ValueError('Channel 1 path cannot be empty!')
