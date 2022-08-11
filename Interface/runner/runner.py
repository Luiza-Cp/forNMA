"""worker.py - defines a Worker thread object."""
from __future__ import annotations

import traceback
import random
import time
from typing import Callable

import pandas as pd
from PySide6.QtCore import QObject, QRunnable, Signal, Slot



def fornma_mock_function(callback: Signal) -> pd.DataFrame():
    """A mock function that simulates executing forNMA."""
    for i in range(100):
        callback.emit({'type': 'progress', 'data': i})
        # time.sleep(random.randint(1, 5))
        raise ValueError('Bad')
    return pd.DataFrame({
        'foo': [1, 2, 3],
        'bar': [4, 5, 9],
    })


class Runner(QRunnable):
    """Worker that executes a function in a separate thread."""
    def __init__(self, func: Callable, *args, **kwargs) -> None:
        super().__init__()
        self.signals = RunnerSignals()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.kwargs['callback'] = self.signals.callback

    @Slot()
    def run(self) -> None:
        """Runs the Worker thread."""
        try:
            return_value = self.func(*self.args, **self.kwargs)
        except Exception as error:
            trace = traceback.format_exc()
            self.signals.error.emit((error, trace))  # noqa
        else:
            self.signals.success.emit(return_value)  # noqa
        finally:
            self.signals.finished.emit()  # noqa


class RunnerSignals(QObject):
    """
    Defines the signals available from a running worker thread. Supported signals are:
    - Finished: Worker has done executing (either naturally or by an Exception). Nothing is emitted.
    - Success: Worker finished executing without errors. Emits ???.
    - Error: an Exception was raised. Emits a tuple containing an Exception object and the traceback as a string.
    - Callback: Signal passed onto the function. Emits anything that the function wants to signal back to the interface.
    """
    finished = Signal()
    success = Signal(object)
    error = Signal(object)
    callback = Signal(object)
