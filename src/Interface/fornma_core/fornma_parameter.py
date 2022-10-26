"""Interface/fornma_core/fornma_parameter.py - module defining the ForNMAParameter interface."""
from __future__ import annotations

from .fornma_blueprints import (
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


class ForNMAParameter:
    """
    Class bundling forNMA information for a given forNMA ID.
    Meant to be created and accessed in any place in the code.
    """
    def __init__(
            self,
            fornma_id: str,
    ) -> None:
        """Sets the default value of the mutable parameters of ForNMAParameter instances."""
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
