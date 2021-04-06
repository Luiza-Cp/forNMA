import sys
import traceback
from types import TracebackType
from typing import Type

from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa


# -----
# CODE RELATED TO LOGGING AND ERROR HANDLING IN PYQT5
# SOURCE: https://timlehr.com/python-exception-hooks-with-qt-message-box/
# -----


class ExceptionHandler(qtc.QObject):
    """Class that catches all exceptions not directly handled by ForNMAMainWindow."""
    exceptionCaught = qtc.pyqtSignal(object, object, object)

    def __init__(self) -> None:
        """Initialization method for ExceptionHandler class."""
        super().__init__()
        sys.excepthook = self.exception_hook  # Hooks the exception_hook() method to the system's exception hook
        self.exceptionCaught.connect(self.handle_exception)  # noqa

    def exception_hook(
            self,
            exc_type: Type[BaseException],
            exc_value: BaseException,
            exc_traceback: TracebackType
    ) -> None:
        """Function handling all Exceptions. It is triggered each time an exception occurs."""
        if issubclass(exc_type, KeyboardInterrupt):
            # ignore KeyboardInterrupt to support console applications
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        if issubclass(exc_type, Warning):
            # ignore Warnings (especially useful for random PyQt5 warnings like qt.qpa.xcb: QXcbConnection: ...)
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            self.exceptionCaught.emit(exc_type, exc_value, exc_traceback)  # noqa

    @qtc.pyqtSlot(object, object, object)
    def handle_exception(
            self,
            exc_type: Type[BaseException],
            exc_value: BaseException,
            exc_traceback: TracebackType
    ) -> None:
        """
        Handles the exception by passing it to a message box or the default sys.__excepthook__,
        depending on whether a QApplication instance is available or not.
        """
        if qtw.QApplication.instance() is not None:
            self.show_error_message_box(exc_type, exc_value, exc_traceback)
        else:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

    @staticmethod
    def show_error_message_box(
            exc_type: Type[BaseException],
            exc_value: BaseException,
            exc_traceback: TracebackType
    ) -> None:
        """Displays the exception message in the default Error Message Box."""
        trace = "".join(traceback.format_tb(exc_traceback))
        exc_value = str(exc_value).replace('<', '&lt;').replace('>', '&gt;')  # escape potential < and > characters
        html_message = (
            f'<font size ="+1"><b>{exc_value}</b></font>\n\n\nFull stack traceback:\n'
            f'{trace}{exc_type.__name__}: {exc_value}'.replace('\n', '<br>')
        )
        errorbox = qtw.QErrorMessage.qtHandler()
        errorbox.setMinimumSize(300, 300)
        errorbox.setWindowTitle('An error occurred!')
        errorbox.showMessage(html_message)
