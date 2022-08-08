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
