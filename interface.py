"""interface.py - GUI frontend for 53BP1 analysis."""
import webbrowser
import sys
import traceback
from typing import Any, Dict, Tuple

from PySide2.QtCore import QThreadPool, Qt, Slot
from PySide2.QtWidgets import (QApplication, QCheckBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox, QPushButton, QSlider, QSpinBox, QVBoxLayout,
                               QWidget, QAction)
from PySide2.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas, NavigationToolbar2QT as Navbar
from matplotlib.pyplot import Figure

from plotter import Plotter
from worker import Worker

# PLACEHOLDER: replace with import of main function from 53BP1 analysis code
FUNC = sum


class GUI(QMainWindow):
    """Class representing the 53BP1 Analysis GUI as a whole."""

    title = 'font-size: 16pt; font-weight: 600; text-align: center'
    subtitle = 'font-weight: 600'

    def __init__(self) -> None:
        """Init method of GUI class. Sets up the entire interface."""
        super().__init__(parent=None)

        # ### MAIN APP SETUP

        # --Application attributes--
        self.setWindowTitle('53BP1 Analysis')
        self.threadpool = QThreadPool(self)

        # --Central widget--
        self.frame = QWidget(self)
        self.setCentralWidget(self.frame)

        # --Main layout--
        main_layout = QHBoxLayout()
        self.frame.setLayout(main_layout)

        # --Left column (parameters)--
        left_column = QVBoxLayout()
        main_layout.addLayout(left_column)

        # --Right column (plot)--
        right_column = QVBoxLayout()
        main_layout.addLayout(right_column)

        # Status bar
        self.status_text = QLabel("Application is ready")
        self.statusBar().addWidget(self.status_text, 1)

        # Top menu
        self.file_menu = self.menuBar().addMenu("File")
        load_file_action = self.create_action("Save plot", slot=self.on_menu_save, tip="Save the plot")
        quit_action = self.create_action("Quit", slot=self.on_menu_close, tip="Close the application")
        self.add_actions(self.file_menu, (load_file_action, None, quit_action))
        self.help_menu = self.menuBar().addMenu("Help")
        about_action = self.create_action("About", slot=self.on_menu_about, tip='About 53BP1 Analysis')
        website_action = self.create_action("Website", slot=self.on_menu_web, tip='Visit our website')
        self.add_actions(self.help_menu, (about_action, website_action))

        # ### LEFT COLUMN

        # --Title--
        self.title = QLabel(self, text='53BP1 Analysis', styleSheet=self.title)
        left_column.addWidget(self.title)

        # --Input frame--
        self.input_inner_frame, self.input_outer_frame = self.get_inner_outer_frame(text='Input selection')
        # Load data line edit
        self.load_data_line = QLineEdit(self, placeholderText='Enter folder here')
        self.input_inner_frame.layout().addWidget(self.load_data_line, 0, 0)  # noqa
        # Load data button
        self.load_data_button = QPushButton(self, text='Select folder...')
        self.load_data_button.clicked.connect(self.load_data)  # noqa
        self.input_inner_frame.layout().addWidget(self.load_data_button, 0, 1)  # noqa
        left_column.addWidget(self.input_outer_frame)

        # --Parameters frame--
        self.params_inner_frame, self.params_outer_frame = self.get_inner_outer_frame(text='Analysis parameters')
        # Parameter 01
        self.param_01_label = QLabel(self, text='Parameter 01')
        self.params_inner_frame.layout().addWidget(self.param_01_label, 0, 0)  # noqa
        self.param_01_spinbox = QSpinBox(self, minimum=0, value=5, maximum=100, singleStep=1)
        self.params_inner_frame.layout().addWidget(self.param_01_spinbox, 0, 1)  # noqa
        # Parameter 02
        self.param_02_label = QLabel(self, text='Parameter 02')
        self.params_inner_frame.layout().addWidget(self.param_02_label, 1, 0)  # noqa
        self.param_02_spinbox = QSpinBox(self, minimum=0, value=5, maximum=100, singleStep=1)
        self.params_inner_frame.layout().addWidget(self.param_02_spinbox, 1, 1)  # noqa
        # Parameter 03
        self.param_03_label = QLabel(self, text='Parameter 03')
        self.params_inner_frame.layout().addWidget(self.param_03_label, 2, 0)  # noqa
        self.param_03_spinbox = QSpinBox(self, minimum=0, value=5, maximum=100, singleStep=1)
        self.params_inner_frame.layout().addWidget(self.param_03_spinbox, 2, 1)  # noqa
        # Checkbox 01
        self.checkbox_01 = QCheckBox(self, text='Checkbox 01')
        self.params_inner_frame.layout().addWidget(self.checkbox_01, 3, 0)  # noqa
        # Checkbox 02
        self.checkbox_02 = QCheckBox(self, text='Checkbox 02')
        self.params_inner_frame.layout().addWidget(self.checkbox_02, 3, 1)  # noqa
        left_column.addWidget(self.params_outer_frame)

        # ### RIGHT COLUMN

        # --Plot frame--
        self.plot_frame = QFrame(self, frameShape=QFrame.Box)
        plot_grid = QGridLayout()
        self.plot_frame.setLayout(plot_grid)
        # Vertical slider
        self.vertical_slider = QSlider(Qt.Vertical, minimum=1, maximum=100, value=20, tracking=True,
                                       tickPosition=QSlider.TicksBothSides)
        self.vertical_slider.valueChanged.connect(self.on_slider_moved)  # noqa
        plot_grid.addWidget(self.vertical_slider, 0, 0)
        # Figure
        self.fig = Figure((5.0, 4.0), dpi=100)
        self.axes = self.fig.add_subplot(111)
        self.canvas = Canvas(self.fig)
        self.canvas.setParent(self.plot_frame)
        plot_grid.addWidget(self.canvas, 0, 1)
        # Horizontal slider
        self.horizontal_slider = QSlider(Qt.Horizontal, minimum=1, maximum=100, value=20, tracking=True,
                                         tickPosition=QSlider.TicksBothSides)
        self.horizontal_slider.valueChanged.connect(self.on_slider_moved)  # noqa
        plot_grid.addWidget(self.horizontal_slider, 1, 1)
        right_column.addWidget(self.plot_frame)
        # Start position for vertical/horizontal lines
        self.vertical_line = self.axes.axvline(0.2)
        self.horizontal_line = self.axes.axhline(0.2)
        # Matplotlib toolbar
        self.mpl_toolbar = Navbar(self.canvas, self.plot_frame)
        right_column.addWidget(self.mpl_toolbar)

        # Add stretch to plot only
        main_layout.setStretch(1, 10)

    def get_inner_outer_frame(self, text: str) -> Tuple[QFrame, QFrame]:
        """Returns a neatly-formatted tuple of QFrames: an inner QFrame encapsulated by an outer QFrame."""
        outer_frame = QFrame(self)
        outer_frame.setLayout(QVBoxLayout())
        outer_frame.layout().addWidget(QLabel(self, text=text, styleSheet=self.subtitle))
        inner_frame = QFrame(self, frameShape=QFrame.Box)
        inner_frame.setLayout(QGridLayout())
        outer_frame.layout().addWidget(inner_frame)
        return inner_frame, outer_frame

    def on_slider_moved(self):
        """Recalculates and redraws the gates on the figure whenever the sliders are moved."""
        self.axes.clear()
        xlim = self.axes.get_xlim()
        ylim = self.axes.get_ylim()
        self.vertical_line = self.axes.axvline((xlim[1] - xlim[0]) * (self.horizontal_slider.value() / 100))
        self.horizontal_line = self.axes.axhline((ylim[1] - ylim[0]) * (self.vertical_slider.value() / 100))
        self.canvas.draw()

    def load_data(self) -> None:
        """Opens a file dialog, prompting the user to select the data (Excel spreadsheet) to load."""
        query = QFileDialog.getExistingDirectory(self, 'Select input folder', options=QFileDialog.DontUseNativeDialog)
        if query:
            self.load_data_line.setText(query)

    def run_analysis(self) -> None:
        """Runs 53BP1 analysis on a worker thread."""
        try:
            self.setup_before_running()
            settings = self.get_gui_parameters()
        except Exception as e:
            self.raise_main_thread_error(e)
        else:
            self.worker_run(settings=settings)

    def get_gui_parameters(self) -> Dict[str, Any]:
        """Bundles the information and parameters selected by the user into a single dictionary and then returns it."""
        return {
            'path': self.load_data_line.text(),
            'param_01': self.param_01_spinbox.value(),
            'param_02': self.param_02_spinbox.value(),
            'param_03': self.param_03_spinbox.value(),
            'checkbox_01': self.checkbox_01.isChecked(),
            'checkbox_02': self.checkbox_02.isChecked(),
        }

    def worker_run(self, settings: Dict[str, Any]) -> None:
        """Runs Worker thread through QThreadPool after instantiating and connecting it."""
        worker = Worker(func=FUNC, **settings)
        worker.add_callbacks()
        self.connect_worker(worker=worker)
        self.threadpool.start(worker)

    def connect_worker(self, worker: Worker) -> None:
        """Hooks up worker signals to interface methods."""
        worker.signals.progress.connect(self.worker_progress_updated)
        worker.signals.warning.connect(self.worker_small_sample_size_warning)
        worker.signals.finished.connect(self.worker_has_finished)
        worker.signals.success.connect(self.worker_raised_no_exceptions)
        worker.signals.error.connect(self.worker_raised_exception)

    def setup_before_running(self) -> None:
        """Called before 53BP1 analysis starts. Disables the analysis button."""
        # If needed, other stuff can be done here
        self.analyse_button.setDisabled(True)

    @Slot(int)
    def worker_progress_updated(self, number: int) -> None:
        """Updates 53BP1 analysis progress counter."""
        # If needed, other stuff can be done here
        self.progress_bar.setValue(number)

    def worker_raised_exception(self, exception_tuple: Tuple[Exception, str]) -> None:
        """Called if an error is raised during 53BP1 analysis. Shows the error in a message box."""
        # If needed, other stuff can be done here
        self.raise_worker_thread_error(exception_tuple)

    def worker_raised_no_exceptions(self, plotter: Plotter, results: Any) -> None:
        """Called if no errors are raised during the 53BP1 analysis. Processes the results from the analysis."""
        # If needed, other stuff can be done here
        self.analyse_button.setEnabled(True)
        plotter.plot_nma(ax=self.nma_ax, results=results)

    def worker_has_finished(self) -> None:
        """Called when 53BP1 analysis finishes running (regardless of errors). Restores label on the plot
        button and removes the axis lines from the histogram"""
        # If needed, other stuff can be done here
        self.canvas.draw()

    def raise_main_thread_error(self, error: Exception) -> None:
        """Generic function for catching errors in the main GUI thread and re-raising them as properly formatted
        message boxes."""
        name = f'{error.__class__.__name__}:\n{error}'
        trace = traceback.format_exc()
        self.show_error_message(name=name, trace=trace)

    def raise_worker_thread_error(self, exception_tuple: Tuple[Exception, str]) -> None:
        """Generic function for catching errors in the worker thread and re-raising them as properly formatted
        message boxes."""
        error, trace = exception_tuple
        name = f'{error.__class__.__name__}:\n{error}'
        self.show_error_message(name=name, trace=trace)

    def show_error_message(self, name: str, trace: str) -> None:
        """Shows a given error as a message box in front of the GUI."""
        box = QMessageBox(self, windowTitle='An error occurred!', text=name, detailedText=trace)
        box.exec_()

    # From: https://gist.github.com/holesond/b4f9db4b24eca00ef8b01a96c6e53a03

    def create_action(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(f":/{icon}.png"))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)  # noqa
        if checkable:
            action.setCheckable(True)
        return action

    @staticmethod
    def add_actions(target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def on_menu_save(self):
        path, ext = QFileDialog.getSaveFileName(self, 'Save file', '', "*.png", options=QFileDialog.DontUseNativeDialog)
        if path:
            self.canvas.print_figure(path, dpi=100)
            self.statusBar().showMessage(f'Saved to {path}', 2000)

    def on_menu_close(self):
        self.close()

    def on_menu_about(self):
        msg = "53BP1 analysis\nDeveloped By Luiza Cherobini Pereira and Juliano Luiz Faccioni at LabSinal/UFRGS, 2020."
        QMessageBox.about(self, "About", msg)

    @staticmethod
    def on_menu_web():
        webbrowser.open('http://ufrgs.br/labsinal')


def main() -> None:
    """Entry point for the 53BP1 Analysis GUI."""
    app = QApplication()
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
