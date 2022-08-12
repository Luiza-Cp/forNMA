"""worker.py - defines a Worker thread object."""
from __future__ import annotations

import random
import time
import traceback
from typing import Callable

import pandas as pd
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from Interface import ForNMAReturnDict


def fornma_mock_function(
        callback: Signal,
        *args,
        **kwargs,
) -> ForNMAReturnDict:
    """A mock function that simulates executing forNMA."""
    for i in range(100):
        callback.emit({  # noqa
            'type': 'progress',
            'message': '',
            'data': [i],
        })
        callback.emit({  # noqa
            'type': 'log',
            'message': f'i equals to {i} right now!',
            'data': [],
        })
        if random.random() < 0.5:
            callback.emit({  # noqa
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
                'foo': [1, 2, 3],
                'bar': [4, 5, 9],
            }),
        ],
    }


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
        self.signals.started.emit()  # noqa
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
    - Started: Worker has started its execution. Nothing is emitted.
    - Finished: Worker has done executing (either naturally or by an Exception). Nothing is emitted.
    - Success: Worker finished executing without errors. Emits ???.
    - Error: an Exception was raised. Emits a tuple containing an Exception object and the traceback as a string.
    - Callback: Signal passed onto the function. Emits anything that the function wants to signal back to the interface.
    """
    started = Signal()
    callback = Signal(object)
    error = Signal(object)
    success = Signal(object)
    finished = Signal()
