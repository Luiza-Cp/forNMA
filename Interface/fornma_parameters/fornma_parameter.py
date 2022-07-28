"""fornma_parameters/fornma_parameter.py - module defining the ForNMAParameter interface."""
from __future__ import annotations

from PySide6 import QtCore as qtc

from Interface.fornma_parameters import (
    get_fornma_dtype,
    get_fornma_help_message,
    get_fornma_numeric_limits,
    get_fornma_label,
    get_fornma_name,
    get_fornma_tooltip,
    get_fornma_text_options,
    get_fornma_value,
    validate_fornma_id,
)

_INSTANCES = {}


def ForNMAParameter(fornma_id: str) -> ForNMAParameter:
    """Interface for getting ForNMAParameter instances. Avoid re-creating the same instance for a given ID."""
    global _INSTANCES
    if (instance := _INSTANCES.get(fornma_id)) is None:
        instance = _ForNMAParameter(fornma_id=fornma_id)
        _INSTANCES[fornma_id] = instance
    return instance


class _ForNMAParameter:
    """
    Class bundling forNMA information for a given forNMA ID.
    Meant to be created and accessed in any place in the code.
    """
    def __init__(
            self,
            fornma_id: str,
            parent: qtc.QObject = None,
    ) -> None:
        """Sets the default value of the mutable parameters of ForNMAParameter instances."""
        super().__init__(parent=parent)
        validate_fornma_id(fornma_id=fornma_id)
        self._fornma_id = fornma_id
        # Text
        self.name = get_fornma_name(fornma_id=self._fornma_id)
        self.label = get_fornma_label(fornma_id=self._fornma_id)
        self.tooltip_text = get_fornma_tooltip(fornma_id=self._fornma_id)
        self.help_message = get_fornma_help_message(fornma_id=self._fornma_id)
        # Data
        self.dtype = get_fornma_dtype(fornma_id=self._fornma_id)
        self.text_options = get_fornma_text_options(fornma_id=self._fornma_id)
        self.numeric_limits = get_fornma_numeric_limits(fornma_id=self._fornma_id)
        self.value = get_fornma_value(fornma_id=self._fornma_id)
