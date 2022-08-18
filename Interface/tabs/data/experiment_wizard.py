"""
Interface/tabs/data/experiment_wizard.py - contains the widgets of the dialog ("wizard") window
used to set the experiment table's layout.
"""
from __future__ import annotations

from PyQt5 import QtCore as qtc, QtWidgets as qtw


class ExperimentWizard(qtw.QWizard):
    """Class representing a wizard used to set the current experiment value."""
    def __init__(
            self,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a ExperimentWizard instance."""
        super().__init__(parent=parent)
        self.data = None

        # ### PAGE ONE
        self.channel_page = ExperimentPage(name='Channel')
        self.addPage(self.channel_page)

        # ### PAGE TWO
        self.group_page = ExperimentPage(name='Group')
        self.addPage(self.group_page)

    @property
    def channels(self) -> list[str]:
        """Returns the name of the channels in the channel page."""
        return self.channel_page.get_labels()

    @property
    def groups(self) -> list[str]:
        """Returns the name of the groups in the channel page."""
        return self.group_page.get_labels()


class ExperimentPage(qtw.QWizardPage):
    """
    Class representing one of the pages in the ExperimentWizard.
    Contains a list of labels that can expand or contract when the corresponding button is clicked.
    """
    def __init__(
            self,
            parent: qtw.QWidget = None,
            name: str = '',
    ) -> None:
        """Initializes a ExperimentPage instance."""
        super().__init__(parent=parent)

        self.line_edits = []

        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        self.add_button = qtw.QPushButton(f'Add {name}')
        self.add_button.clicked.connect(self.add)
        layout.addWidget(self.add_button)

        layout.addStretch()

    def get_labels(self) -> list[str]:
        """Returns the labels currently in the ExperimentPage. Ignores line edits with empty strings in them."""
        labels = []
        for line_edit in self.line_edits:
            label_text = line_edit.text()
            if label_text:
                labels.append(label_text)
        return labels

    def add(self) -> None:
        """Adds a DeletableLabel to the ExperimentPage."""
        index = len(self.line_edits)
        label = DeletableLabel(index=index)
        self.layout().insertWidget(index, label)
        self.line_edits.append(label.line_edit)
        label.deleteClicked.connect(self.remove)

    def remove(
            self,
            index: int,
    ) -> None:
        """Removes the DeletableLabel from the ExperimentPage."""
        label = self.line_edits[index]
        self.line_edits.remove(label.line_edit)
        self.layout().removeWidget(label)
        label.setParent(None)


class DeletableLabel(qtw.QWidget):
    """Class representing a QLineEdit with a QPushButton responsible for deleting it."""
    deleteClicked = qtc.pyqtSignal(int)

    def __init__(
            self,
            index: int,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DeletableLineEdit instance."""
        super().__init__(parent=parent)
        self.index = index

        layout = qtw.QHBoxLayout()
        self.setLayout(layout)

        self.line_edit = qtw.QLineEdit()
        layout.addWidget(self.line_edit)

        self.delete_button = qtw.QPushButton()
        self.delete_button.setIcon(self.style().standardIcon(getattr(qtw.QStyle, "SP_DialogDiscardButton")))
        layout.addWidget(self.delete_button)

        # Alias
        self.delete_button.clicked.connect(self.on_delete_clicked)

    def on_delete_clicked(self) -> None:
        """Emits the DeletableLabel's index, so that the listener widget can delete it."""
        self.deleteClicked.emit(self.index)
