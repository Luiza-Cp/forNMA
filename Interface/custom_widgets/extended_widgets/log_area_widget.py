"""Interface/custom_widgets/extended_widgets/log_area_widget.py - widget with an area used for logging messages."""
from __future__ import annotations

from PyQt5 import QtWidgets as qtw


class LogAreaWidget(qtw.QTextEdit):
    """Widget used to log messages in a standardized way."""
    def __init__(
            self,
            default_text: str = '',
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a LogAreaWidget."""
        super().__init__(parent)
        self.default_text = default_text
        self.setReadOnly(True)
        self.write_default_text()

    def reset_log(self) -> None:
        """Resets the log area."""
        self.setText("")

    def write_default_text(self) -> None:
        """Resets the log area and writes the default text into it."""
        self.reset_log()
        self.write_title(self.default_text)

    def write_message(
            self,
            message: str,
    ) -> None:
        """Writes the message as a regular message."""
        self.append(f'<span style="font-size:10pt; font-weight:400; color:#232323;">{message}</span>')

    def write_title(
            self,
            message: str,
    ) -> None:
        """Writes the message as a title."""
        self.append(f'<span style="font-size:18pt; font-weight:600; color:#232323;">{message}</span>')

    def write_warning(
            self,
            message: str,
    ) -> None:
        """Writes the message as a warning."""
        self.append(f'<span style="font-size:10pt; font-weight:600; color:#ff3333;">{message}</span>')
