"""forNMA_main_window.py - GUI frontend for forNMA analysis."""
import sys
import webbrowser
from typing import Optional

from PyQt5 import QtCore as qtc, QtGui as qtg, QtWidgets as qtw  # noqa

from src.interface.forNMA_tabbed_widget import ForNMATabbedWidget
from src.interface.helpers.exception_handler import ExceptionHandler
from src.interface.settings_widget import SettingsWidget


class ForNMAMainWindow(qtw.QMainWindow):
    """Class representing forNMA's main interface window."""
    default_statusbar_text = 'forNMA is ready!'

    def __init__(
            self,
            parent: Optional[qtw.QWidget] = None,
    ) -> None:
        """Initializes a ForNMAMainWindow instance."""
        super().__init__(parent=parent)

        # Application attributes
        self.setWindowTitle('forNMA Analysis')
        self.setMinimumSize(960, 600)
        self.threadpool = qtc.QThreadPool(self)

        # Left DockWidget
        self.left_dock_widget = qtw.QDockWidget('Settings')
        self.addDockWidget(qtc.Qt.LeftDockWidgetArea, self.left_dock_widget)

        # Add Settings widget to left DockWidget
        self.settings_widget = SettingsWidget()
        self.left_dock_widget.setWidget(self.settings_widget)
        self.left_dock_widget.setMinimumWidth(400)

        # ForNMATabbedWidget placed as the GUI's CentralWidget
        self.central_widget = ForNMATabbedWidget()
        self.setCentralWidget(self.central_widget)

        # MenuBar
        file_menu = self.menuBar().addMenu('File')
        file_menu.addAction('Quit forNMA', self.closeEvent)
        view_menu = self.menuBar().addMenu('View')
        view_menu.addAction('View settings', self.set_settings_widget_visible)
        help_menu = self.menuBar().addMenu('Help')
        help_menu.addAction('Online documentation...', self.open_online_documentation)

        # ToolBar
        experiment_toolbar = self.addToolBar('Help')
        experiment_toolbar.setIconSize(qtc.QSize(36, 36))
        experiment_toolbar.addAction(qtg.QIcon(''), 'Open online documentation', self.open_online_documentation)

        # StatusBar
        self.status_message_widget = qtw.QLabel(self.default_statusbar_text)  # starts with an empty string
        self.statusBar().addWidget(self.status_message_widget)

        # Connect SettingsWidget's InputSelectionWidget to ForNMATabbedWidget's InputTableWidget
        # TODO: simplify/abstract this!
        self.settings_widget.folderSelected.connect(self.central_widget.input_table_tab.add_row_from_dict)

    @qtc.pyqtSlot()
    def set_settings_widget_visible(self) -> None:
        """Sets the settings widgets visible, useful if it has been closed."""
        self.settings_widget.setVisible(True)

    @qtc.pyqtSlot(str)
    def set_status_message(
            self,
            text: str = '',
    ) -> None:
        """Updates the status bar spinbox widget with a new text. Can be used as a slot from other widgets/threads."""
        self.status_message_widget.setText(text)

    @staticmethod
    def open_online_documentation() -> None:
        """Opens forNMA online documentation."""
        # TODO: actually write the documentation, then link it here
        webbrowser.open('http://ufrgs.br/labsinal')


# create a global instance of ExceptionHandler to register the exception hook
# comment out this line for making exceptions display on the console again
qt_exception_hook = ExceptionHandler()

if __name__ == '__main__':
    # The lines below used to be in a main function, but it might be better if they are in the global scope.
    # See discussion at: https://stackoverflow.com/questions/51834981/pyside2-with-built-in-multiprocessing.

    # Creates the QApplication
    app = qtw.QApplication(sys.argv)

    # TODO: create resource file, then load it here
    # # Sets the global QApplication style by reading QSS from the resources file
    # stream = qtc.QFile(":/style/style")
    # stream.open(qtc.QIODevice.ReadOnly)
    # app.setStyleSheet(qtc.QTextStream(stream).readAll())

    # Displays GUI
    fornma_gui = ForNMAMainWindow()
    fornma_gui.show()
    sys.exit(app.exec_())
