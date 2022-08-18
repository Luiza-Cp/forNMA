from __future__ import annotations

import matplotlib.backend_bases
import pandas as pd
import seaborn as sns
from PyQt5 import QtWidgets as qtw
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
from matplotlib.lines import Line2D


class DraggableCanvasWidget(qtw.QDialog):
    """Class representing a widget with a DraggableCanvas inside."""
    def __init__(
            self,
            data: pd.DataFrame,
            parent=None,
    ) -> None:
        """Initializes a DraggableCanvasWidget instance."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QVBoxLayout()
        self.setLayout(layout)

        # Canvas etc
        self.canvas = DraggableCanvas(data=data)
        layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, parent=None)
        layout.addWidget(self.toolbar)

        # Buttons in horizontal layout
        button_layout = qtw.QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = qtw.QPushButton('cancel')
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        self.ok_button = qtw.QPushButton('ok')
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        # Add buttons to main layout
        layout.addLayout(button_layout)

    def get_data(self) -> pd.DataFrame:
        """Returns the data selected through the canvas."""
        return self.canvas.get_data()


class DraggableCanvas(FigureCanvas):
    def __init__(
            self,
            data: pd.DataFrame,
            width: int = 5,
            height: int = 4,
            dpi: int = 100,
    ) -> None:
        """Initializes a DraggableCanvas instance."""
        self.data = data
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        # Initial plot
        ax = self.fig.add_subplot(111)
        sns.scatterplot(data=data, ax=ax, x='Roundness', y='Area')
        # Lines
        self.lines = [
            DraggableLine(orientation='h', position=self.data['Area'].quantile(0.05), picker=5),  # lower X-axis
            DraggableLine(orientation='h', position=self.data['Area'].quantile(0.95), picker=5),  # upper X-axis
            DraggableLine(orientation='v', position=self.data['Roundness'].min(), picker=5),  # lower Y-axis
            DraggableLine(orientation='v', position=self.data['Roundness'].quantile(0.95), picker=5),  # upper Y-axis
        ]
        for line in self.lines:
            ax.add_line(line=line)
            self.mpl_connect('pick_event', line.on_clicked)
        self.draw_idle()

    def get_data(self) -> pd.DataFrame:
        """Returns the data in the Canvas, filtered by the position of the lines."""
        horizontal_limits = [line.get_value() for line in self.lines if line.orientation == 'h']
        vertical_limits = [line.get_value() for line in self.lines if line.orientation == 'v']
        return self.data.loc[
            self.data['Area'].between(*sorted(horizontal_limits)) &
            self.data['Roundness'].between(*sorted(vertical_limits))
        ]


class DraggableLine(Line2D):
    """Class representing a line that can be dragged along a matplotlib Axes."""
    _default_x = [-100, 100]
    _default_y = [-100_000, 100_000]

    def __init__(
            self,
            orientation: str,
            position: float,
            *args,
            **kwargs,
    ) -> None:
        """Initializes a DraggableLine instance."""
        self.orientation = orientation
        self.position = position
        self.clicked = False
        if self.orientation == 'h':
            super().__init__(self._default_x, [self.position, self.position], *args, **kwargs)
        elif self.orientation == 'v':
            super().__init__([self.position, self.position], self._default_y, *args, **kwargs)
        else:
            raise ValueError(f'Bad orientation for DraggableLine: {self.orientation}')
        # Connection placeholders
        self.drag_pid = None
        self.release_pid = None

    def on_clicked(
            self,
            event: matplotlib.backend_bases.PickEvent,
    ) -> None:
        """Sets the canvas connections whenever the line is clicked."""
        if event.artist == self:
            self.drag_pid = event.canvas.mpl_connect('motion_notify_event', self.on_dragged)
            self.release_pid = event.canvas.mpl_connect('button_release_event', self.on_released)

    def on_dragged(
            self,
            event: matplotlib.backend_bases.MouseEvent,
    ) -> None:
        """Determines what happens when a line is dragged."""
        if self.orientation == 'h':
            self.set_ydata([event.ydata, event.ydata])
        else:
            self.set_xdata([event.xdata, event.xdata])
        event.canvas.draw_idle()

    def on_released(
            self,
            event: matplotlib.backend_bases.MouseEvent,
    ) -> None:
        """Sets the line state to released."""
        for pid in [self.drag_pid, self.release_pid]:
            event.canvas.mpl_disconnect(pid)

    def get_value(self) -> float:
        """Gets the current value in the line."""
        if self.orientation == 'h':
            return self.get_ydata()[0]
        else:
            return self.get_xdata()[0]
