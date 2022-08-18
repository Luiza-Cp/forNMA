"""
Interface/custom_widgets/buttons/help_button.py - module containing a button that opens a
"Help" dialog upon being clicked.
"""
from __future__ import annotations

from PyQt5 import QtWidgets as qtw


class HelpButton(qtw.QToolButton):
    """Class representing a button that displays a help message when clicked."""
    def __init__(
            self,
            tooltip_text: str = "",
            help_title: str = "",
            help_message: str = "",
            parent: qtw.QWidget = None,
    ):
        """Initializes a HelpMessageButton widget."""
        super().__init__(parent=parent)
        self._tooltip_text = tooltip_text
        self._help_title = help_title
        self._help_message = help_message

        self.setIcon(self.style().standardIcon(getattr(qtw.QStyle, "SP_TitleBarContextHelpButton")))
        self.setToolTip(self._tooltip_text)

        self.clicked.connect(self.display_help_message)

    def display_help_message(self) -> None:
        """Displays the help message in a textbox."""
        qtw.QMessageBox.information(self, f"Help: {self._help_title}", self._help_message)
