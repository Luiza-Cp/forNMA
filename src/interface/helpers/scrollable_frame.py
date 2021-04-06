from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa


class ScrollableFrame(qtw.QScrollArea):
    """A QScrollArea that has a QFrame inside it."""
    def __init__(
            self,
            *args,
            **kwargs,
    ) -> None:
        """Initializes a ScrollableFrame instance."""
        super().__init__(*args, **kwargs)

        # QScrollArea setup
        self.setWidgetResizable(True)

        # QFrame
        self.frame = qtw.QFrame()
        self.frame.setFrameStyle(1)
        self.setWidget(self.frame)

        # QFrame's layout
        self.frame_layout = qtw.QVBoxLayout()
        self.frame.setLayout(self.frame_layout)

    @property
    def layout(self) -> qtw.QLayout:
        """Returns the layout of the QFrame inside the QScrollArea."""
        return self.frame_layout
