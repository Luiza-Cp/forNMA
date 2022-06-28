"""
helpers/spoiler.py - contains the CollapsableButton widget, used to dynamically show/hide other widgets.

Source:
  - https://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt
"""
from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw


class CollapsableButton(qtw.QWidget):
    """Widget representing a "collapsable" button, which reveals widgets upon being clicked."""
    def __init__(
            self,
            title: str = '',
            animation_duration: int = 300,
            widget_to_hide: qtw.QWidget = None,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a Spoiler instance."""
        super().__init__(parent=parent)
        self.widget_to_hide = widget_to_hide

        # Layout
        self.main_layout = qtw.QGridLayout()
        self.setLayout(self.main_layout)
        # Don't waste space
        self.main_layout.setVerticalSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # ### First row
        row = 0
        # Toggle button
        self.toggle_button = qtw.QToolButton()
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(qtc.Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(qtc.Qt.RightArrow)
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self.start_animation)  # noqa
        self.main_layout.addWidget(self.toggle_button, row, 0, 1, 1)
        # Header line
        self.header_line = qtw.QFrame()
        self.header_line.setFrameShape(qtw.QFrame.HLine)
        self.header_line.setFrameShadow(qtw.QFrame.Sunken)
        self.header_line.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Maximum)
        self.main_layout.addWidget(self.header_line, row, 2, 1, 1)

        # ### Second row
        row += 1
        # Content area
        self.content_area = qtw.QScrollArea()
        self.content_area.setStyleSheet("QScrollArea { background-color: white; border: none; }")
        self.content_area.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed)
        # Start out collapsed
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.main_layout.addWidget(self.content_area, row, 0, 1, 3)

        # Toggle animation - let the entire widget grow and shrink with its content
        self.animation_duration = animation_duration
        self.toggle_animation = qtc.QParallelAnimationGroup()
        self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self, b"minimumHeight"))
        self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self, b"maximumHeight"))
        self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self.content_area, b"maximumHeight"))

        if self.widget_to_hide is not None:
            self.set_content_layout(self.widget_to_hide.layout())

    def start_animation(
            self,
            checked: bool,
    ) -> None:
        """Starts the animation."""
        arrow_type = qtc.Qt.DownArrow if checked else qtc.Qt.RightArrow
        direction = qtc.QAbstractAnimation.Forward if checked else qtc.QAbstractAnimation.Backward
        self.toggle_button.setArrowType(arrow_type)
        self.toggle_animation.setDirection(direction)
        self.toggle_animation.start()

    def set_content_layout(
            self,
            content_layout: qtw.QLayout,
    ) -> None:
        """Sets the content layout to the collapsable area.."""
        self.content_area.destroy()
        self.content_area.setLayout(content_layout)
        collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        content_height = content_layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount() - 1):
            spoiler_animation = self.toggle_animation.animationAt(i)
            spoiler_animation.setDuration(self.animation_duration)
            spoiler_animation.setStartValue(collapsed_height)
            spoiler_animation.setEndValue(collapsed_height + content_height)
        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(self.animation_duration)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


# class CollapsibleWidget(qtw.QWidget):
#     """
#     Class representing a widget with a collapsible area underneath a clickable spinbox.
#     source: https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt/52617714#52617714
#     """
#     def __init__(
#             self,
#             content_layout: Optional[qtw.QLayout],
#             title: str = "",
#             parent: Optional[qtw.QWidget] = None
#     ) -> None:
#         """Initializes a CollapsibleWidget instance."""
#         super().__init__(parent=parent)
#
#         # Layout
#         layout = qtw.QVBoxLayout(self)
#         layout.setSpacing(0)
#         layout.setContentsMargins(0, 0, 0, 0)
#         self.setLayout(layout)
#
#         # Toggle button
#         self.toggle_button = qtw.QToolButton(
#             text=title,  # noqa
#             checkable=True,  # noqa
#             checked=True,  # noqa
#             # TODO: set stylesheet on resource file, not directly into code
#             styleSheet="QToolButton { border: none; }",  # noqa
#             toolButtonStyle=qtc.Qt.ToolButtonTextBesideIcon,  # noqa
#             arrowType=qtc.Qt.RightArrow,  # noqa
#             released=self.on_toggle_button_released,  # noqa
#         )
#         layout.addWidget(self.toggle_button)
#
#         # Content area
#         self.content_area = qtw.QScrollArea(maximumHeight=0, minimumHeight=0)  # noqa
#         self.content_area.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed)
#         self.content_area.setFrameShape(qtw.QFrame.NoFrame)
#         layout.addWidget(self.content_area)
#
#         # Toggle animation  # TODO: animations are needed? Should they be improved or removed?
#         self.toggle_animation = qtc.QParallelAnimationGroup(self)
#         self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self, b"minimumHeight"))
#         self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self, b"maximumHeight"))
#         self.toggle_animation.addAnimation(qtc.QPropertyAnimation(self.content_area, b"maximumHeight"))
#
#         # Add content layout to content area
#         if content_layout is not None:
#             self.setContentLayout(layout=content_layout)
#
#     @qtc.Slot()
#     def click(self) -> None:
#         """Convenience method for clicking the CollapsibleWidget's toggle button."""
#         return self.toggle_button.click()
#
#     @qtc.Slot()
#     def on_toggle_button_released(self) -> None:
#         """Expands/shrinks the content under the button, whenever it is clicked and released."""
#         if self.toggle_button.isChecked():
#             self.toggle_button.setArrowType(qtc.Qt.RightArrow)
#             self.toggle_animation.setDirection(qtc.QAbstractAnimation.Backward)
#         else:
#             self.toggle_button.setArrowType(qtc.Qt.DownArrow)
#             self.toggle_animation.setDirection(qtc.QAbstractAnimation.Forward)
#         self.toggle_animation.start()
#
#     def setContentLayout(  # noqa
#             self,
#             layout: qtw.QLayout,
#     ) -> None:
#         """Sets the given layout as the collapsible content under the widget's header."""
#         if (current_layout := self.content_area.layout()) is not None:
#             current_layout.setParent(None)  # noqa  # deletes current content area layout, if it exists
#         self.content_area.setLayout(layout)
#         collapsed_height = (self.sizeHint().height() - self.content_area.maximumHeight())
#         content_height = layout.sizeHint().height()
#         for i in range(self.toggle_animation.animationCount()):
#             animation = self.toggle_animation.animationAt(i)
#             animation.setDuration(200)
#             animation.setStartValue(collapsed_height)
#             animation.setEndValue(collapsed_height + content_height)
#         content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
#         content_animation.setDuration(200)
#         content_animation.setStartValue(0)
#         content_animation.setEndValue(content_height)
