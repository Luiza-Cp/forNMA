"""helpers/tooltip_layout.py - module defining a layout that adds a tooltip and a top label to any given widget."""

from PySide6 import QtGui as qtg, QtWidgets as qtw


class ToolTipLayout(qtw.QGridLayout):  # TODO: can be improved
    """Widget representing a grid layout with a tooltip to the left, and an optional label at the top."""
    def __init__(
            self,
            widget: qtw.QWidget,
            widget_name: str,
            top_label: str = None,
            parent: qtw.QWidget = None,
    ) -> None:
        """Adds the widget to the Layout, including a tooltip."""
        super().__init__(parent=parent)
        self.tooltip_text = self.get_tooltip_from_widget_name(widget_name=widget_name)

        self.tooltip_button = qtw.QToolButton()
        self.tooltip_button.setIcon(self.get_tooltip_icon())
        self.tooltip_button.setToolTip(self.tooltip_text)
        self.tooltip_button.clicked.connect(self.display_tooltip_information)  # noqa

        widget_row = 0
        if top_label is not None:
            self.addWidget(qtw.QLabel(top_label), widget_row, 0, 1, 2)
            widget_row += 1
        self.addWidget(self.tooltip_button, 1, 0, 1, 1)
        self.addWidget(widget, 1, 1, 1, 1)

    @staticmethod
    def get_tooltip_from_widget_name(widget_name: str) -> str:
        """Returns the appropriate tooltip, given the widget name."""
        return getattr(ToolTips, widget_name + '_text')

    def display_tooltip_information(self) -> None:
        """Displays the tooltip information in a textbox."""
        parent = self.parent()
        while not isinstance(parent, qtw.QWidget):
            parent = parent.parent()
        qtw.QMessageBox.information(parent, "Help", self.tooltip_text)

    def get_tooltip_icon(self) -> qtg.QIcon | qtg.QPixmap:
        """Returns the tooltip button's icon."""
        return self.tooltip_button.style().standardIcon(getattr(qtw.QStyle, "SP_TitleBarContextHelpButton"))


class ToolTips:
    """Class defining the existing tooltip text in forNMA's interface."""
    channel_with_nuclei_text = "This is the channel with nuclei text."
    magnification_text = "No tooltip yet!"
