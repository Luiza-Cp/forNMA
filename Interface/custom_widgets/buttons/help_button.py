"""helpers/help_button.py - module containing a button that opens a "Help" dialog upon being clicked."""
from __future__ import annotations

from PySide6 import QtWidgets as qtw

from Interface import ForNMAParameter


def ForNMAHelpButton(fornma_id: str = None):
    """Interface for creating a HelpButton instance from a forNMA ID."""
    if fornma_id is not None:
        fornma_params = ForNMAParameter(fornma_id=fornma_id)
        return HelpButton(
            tooltip_text=fornma_params.tooltip_text,
            help_title=fornma_params.name,
            help_message=fornma_params.help_message,
        )
    return HelpButton()


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

        self.clicked.connect(self.display_help_message)  # noqa

    def display_help_message(self) -> None:
        """Displays the help message in a textbox."""
        qtw.QMessageBox.information(self, f"Help: {self._help_title}", self._help_message)

    @classmethod
    def from_fornma_parameter(
        cls,
        fornma_parameter: ForNMAParameter,
    ) -> HelpButton:
        """Returns an instance of HelpButton constructed from a ForNMAParameter instance."""
        return cls(
            tooltip_text=fornma_parameter.tooltip_text,
            help_title=fornma_parameter.name,
            help_message=fornma_parameter.help_message,
        )
