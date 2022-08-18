"""
Interface/custom_widgets/layouts/row_layout.py - defines a RowLayout used to add rows
of widgets to a single, unobtrusive layout.
"""
from __future__ import annotations

from typing import Iterator, Literal

from PyQt5 import QtCore as qtc, QtWidgets as qtw


class RowLayout(qtw.QHBoxLayout):
    """Class representing a row layout that accepts any numer of widgets. By default, it has no margins."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
            widgets: list[qtw.QWidget | Literal['stretch']] = None,
            stretch: Literal['before', 'after'] = None,
    ) -> None:
        """Initializes a RowLayout instance."""
        self._contained_widgets = []
        widgets = widgets or []
        super().__init__(parent)
        if stretch == 'before':
            self.addStretch()
        for widget in widgets:
            if widget == 'stretch':
                self.addStretch()
            else:  # Assume it's an actual widget
                self.addWidget(widget)
        if stretch == 'after':
            self.addStretch()
        self.setContentsMargins(0, 0, 0, 0)

    def __contains__(
            self,
            widget: qtw.QWidget,
    ) -> bool:
        """Implements the "in" operator by returning whether the given widget is inside the RowLayout."""
        return widget in self._contained_widgets

    def __iter__(self) -> Iterator[qtw.QWidget]:
        """Implements iterating over a RowLayout by iterating over its widgets."""
        return iter(self._contained_widgets)

    def addWidget(
            self,
            widget: qtw.QWidget,
            stretch: int = 0,
            alignment: qtc.Qt.Alignment = qtc.Qt.Alignment(),
            Qt_Alignment=None,
            Qt_AlignmentFlags=None,
            *args,
            **kwargs,
    ) -> None:
        """Adds a Widget to the layout."""
        self._contained_widgets.append(widget)
        return super().addWidget(widget, stretch, alignment)

    def addWidgets(
            self,
            widgets: list[qtw.QWidget],
            stretch: int = 0,
            alignment: qtc.Qt.Alignment = qtc.Qt.Alignment(),
    ) -> None:
        """Adds multiple Widgets to the layout."""
        for widget in widgets:
            self.addWidget(widget, stretch, alignment)
        self._contained_widgets.extend(widgets)
