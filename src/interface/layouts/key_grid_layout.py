from typing import Any, Dict

from PyQt5 import QtWidgets as qtw  # noqa


class KeyGridLayout(qtw.QGridLayout):
    """A class representing a layout that knows how to access information from the key_widgets inside of it."""
    attrs_to_extract = [
        'value',
        'currentText',
        'isChecked',
    ]

    def __init__(
            self,
            *args,
            **kwargs,
    ) -> None:
        """Initializes a KeyGridLayout instance."""
        super().__init__(*args, **kwargs)
        self.key_widgets = []
        self.current_row = -1

    @property
    def next_row(self) -> int:
        """Moves one index further on the current row and returns it new value."""
        self.current_row += 1
        return self.current_row

    def addKeyWidget(  # noqa
            self,
            widget: qtw.QWidget,
            *args,
            **kwargs,
    ) -> None:
        """Adds the widget to the layout and internal key widgets list, creating an easy-to-retrieve reference to it."""
        super().addWidget(widget, *args, **kwargs)
        self.flagAsKeyWidget(widget=widget)

    def flagAsKeyWidget(  # noqa
            self,
            widget: qtw.QWidget,
    ) -> None:
        """Adds the widget to the internal key widgets list, creating an easy-to-retrieve reference to it."""
        if widget.objectName() != '':
            self.key_widgets.append(widget)

    def retrieveSettings(self) -> Dict[str, Any]:  # noqa
        """Retrieves the values from each key widget placed in the key widgets list."""
        settings = {}
        for widget in self.key_widgets:
            for attr in self.attrs_to_extract:
                if hasattr(widget, attr):
                    key = widget.objectName()
                    value = getattr(widget, attr)() if widget.isEnabled() else None
                    settings[key] = value
                    break
        return settings
