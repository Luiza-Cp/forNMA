from typing import Any, Dict, Optional

from PySide6 import QtCore as qtc, QtWidgets as qtw


class CollapsibleWidget(qtw.QWidget):
    """
    Class representing a widget with a collapsible area underneath a clickable spinbox.
    source: https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt/52617714#52617714
    """
    def __init__(
            self,
            content_layout: Optional[qtw.QLayout],
            title: str = "",
            parent: Optional[qtw.QWidget] = None
    ) -> None:
        """Initializes a CollapsibleWidget instance."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Toggle button
        self.toggle_button = qtw.QToolButton(
            text=title,  # noqa
            checkable=True,  # noqa
            checked=True,  # noqa
            # TODO: set stylesheet on resource file, not directly into code
            styleSheet="QToolButton { border: none; }",  # noqa
            toolButtonStyle=qtc.Qt.ToolButtonTextBesideIcon,  # noqa
            arrowType=qtc.Qt.RightArrow,  # noqa
            released=self.on_toggle_button_released,  # noqa
        )
        layout.addWidget(self.toggle_button)

        # Content area
        self.content_area = qtw.QScrollArea(maximumHeight=0, minimumHeight=0)  # noqa
        self.content_area.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed)
        self.content_area.setFrameShape(qtw.QFrame.NoFrame)
        layout.addWidget(self.content_area)

        # Toggle animation  # TOREVIEW: animations are needed? Should they be improved or removed?
        self.toggle_animation = qtc.QParallelAnimationGroup(self)
        self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self, b"minimumHeight"))
        self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self, b"maximumHeight"))
        self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self.content_area, b"maximumHeight"))

        # Add content layout to content area
        if content_layout is not None:
            self.setContentLayout(layout=content_layout)

    @qtc.Slot()
    def click(self) -> None:
        """Convenience method for clicking the CollapsibleWidget's toggle button."""
        return self.toggle_button.click()

    @qtc.Slot()
    def on_toggle_button_released(self) -> None:
        """Expands/shrinks the content under the button, whenever it is clicked and released."""
        if self.toggle_button.isChecked():
            self.toggle_button.setArrowType(qtc.Qt.RightArrow)
            self.toggle_animation.setDirection(qtc.QAbstractAnimation.Backward)
        else:
            self.toggle_button.setArrowType(qtc.Qt.DownArrow)
            self.toggle_animation.setDirection(qtc.QAbstractAnimation.Forward)
        self.toggle_animation.start()

    def setContentLayout(  # noqa
            self,
            layout: qtw.QLayout,
    ) -> None:
        """Sets the given layout as the collapsible content under the widget's header."""
        if (current_layout := self.content_area.layout()) is not None:
            current_layout.setParent(None)  # noqa  # deletes current content area layout, if it exists
        self.content_area.setLayout(layout)
        collapsed_height = (self.sizeHint().height() - self.content_area.maximumHeight())
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(200)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)
        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(200)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    def retrieve_settings(self) -> Dict[str, Any]:
        """
        Retrieve the settings contained inside the CollapsibleWidget's KeyGridLayout. Raises a TypeError
        if the layout does not support key setting retrieval (i.e. it is not an instance of KeyGridLayout).
        """
        try:
            return self.content_area.layout().retrieve_key_settings()
        except AttributeError:
            raise TypeError(f'Current layout of type {type(self.layout())} does not support key settings retrieval')
