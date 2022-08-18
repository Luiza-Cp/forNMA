"""Interface/runner/runner.py - defines a Runner object used to run a function in a separate thread."""
from __future__ import annotations

import random
import traceback
from typing import Callable

import pandas as pd
from PyQt5 import QtCore as qtc

from Interface.types import ForNMAReturnDict


def fornma_mock_function(
        callback: qtc.pyqtSignal,
        *args,
        **kwargs,
) -> ForNMAReturnDict:
    """A mock function that simulates executing forNMA."""
    for i in range(100):
        callback.emit({
            'type': 'progress',
            'message': '',
            'data': [i],
        })
        callback.emit({
            'type': 'log',
            'message': f'i equals to {i} right now!',
            'data': [],
        })
        if random.random() < 0.5:
            callback.emit({
                'type': 'warning',
                'message': f'Something bad happened at iteration {i}...',
                'data': ['bad', 'data', 'here'],
            })
        if random.random() < 0.0:
            raise ValueError('Bad Things!')
    return {
        'status': 'ok',
        'message': 'forNMA finished executing successfully!',
        'data': [
            pd.DataFrame({
                'Area': [1, 2, 3],
                'Roundness': [4, 5, 9],
            }),
        ],
    }


class Runner(qtc.QRunnable):
    """Worker that executes a function in a separate thread."""
    def __init__(self, func: Callable, *args, **kwargs) -> None:
        super().__init__()
        self.signals = RunnerSignals()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.kwargs['callback'] = self.signals.callback

    def run(self) -> None:
        """Runs the Worker thread."""
        self.signals.started.emit()
        try:
            return_value = self.func(*self.args, **self.kwargs)
        except Exception as error:
            trace = traceback.format_exc()
            self.signals.error.emit((error, trace))
        else:
            self.signals.success.emit(return_value)
        finally:
            self.signals.finished.emit()


class RunnerSignals(qtc.QObject):
    """
    Defines the signals available from a running worker thread. Supported signals are:
    - Started: Worker has started its execution. Nothing is emitted.
    - Finished: Worker has done executing (either naturally or by an Exception). Nothing is emitted.
    - Success: Worker finished executing without errors. Emits ???.
    - Error: an Exception was raised. Emits a tuple containing an Exception object and the traceback as a string.
    - Callback: Signal passed onto the function. Emits anything that the function wants to signal back to the interface.
    """
    started = qtc.pyqtSignal()
    callback = qtc.pyqtSignal(object)
    error = qtc.pyqtSignal(object)
    success = qtc.pyqtSignal(object)
    finished = qtc.pyqtSignal()
