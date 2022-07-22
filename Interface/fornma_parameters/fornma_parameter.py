"""fornma_parameters/fornma_parameter.py - module defining the ForNMAParameter interface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Interface.fornma_parameters import (
    get_fornma_help_message,
    get_fornma_numeric_limits,
    get_fornma_label,
    get_fornma_name,
    get_fornma_tooltip, get_fornma_value,
)

_INSTANCES = {}


def ForNMAParameter(fornma_id: str) -> ForNMAParameter:
    """Interface for getting ForNMAParameter instances. Avoid re-creating the same instance for a given ID."""
    global _INSTANCES
    if (instance := _INSTANCES.get(fornma_id)) is None:
        instance = _ForNMAParameter(_fornma_id=fornma_id)
        _INSTANCES[fornma_id] = instance
    return instance


@dataclass
class _ForNMAParameter:
    """
    Class bundling forNMA information for a given forNMA ID.
    Meant to be created and accessed in any place in the code.
    """
    _fornma_id: str = ""

    def __post_init__(self) -> None:
        """Sets the default value of the mutable parameters of ForNMAParameter instances."""
        self.name = get_fornma_name(fornma_id=self._fornma_id)
        self.label = get_fornma_label(fornma_id=self._fornma_id)
        self.tooltip_text = get_fornma_tooltip(fornma_id=self._fornma_id)
        self.help_message = get_fornma_help_message(fornma_id=self._fornma_id)
        self.numeric_limits = get_fornma_numeric_limits(fornma_id=self._fornma_id)
        self.value = get_fornma_value(fornma_id=self._fornma_id)

    def set_value(
            self,
            new_value: Any,
    ) -> None:
        """Sets the parameter value."""
        self.value = new_value
