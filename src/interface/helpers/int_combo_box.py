from typing import Union

from PyQt5 import QtWidgets as qtw  # noqa


class IntComboBox(qtw.QComboBox):
    """A combobox which attempts to return an integer from its currentText method."""
    def currentText(self) -> Union[int, str]:
        """Attempts to return the combobox current text as an integer (returns a regular string if this fails)."""
        try:
            return int(super().currentText())
        except ValueError:  # could not convert to integer
            return super().currentText()
