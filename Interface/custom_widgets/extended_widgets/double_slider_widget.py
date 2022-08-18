"""
Interface/custom_widgets/extended_widgets/double_slider_widget.py - contains a slider widget
that accepts floating point values.
"""
from __future__ import annotations

from PyQt5 import QtCore as qtc, QtWidgets as qtw


class DoubleSlider(qtw.QSlider):
    """
    A QSlider that works with float values, instead of integers.
    source: https://stackoverflow.com/questions/42820380/use-float-for-qslider
    """
    doubleValueChanged = qtc.pyqtSignal(float)

    def __init__(
            self,
            decimals: int = 3,
            orientation: qtc.Qt.Orientation = qtc.Qt.Horizontal,
            minimum: float = None,
            maximum: float = None,
            singleStep: float = None,
            value: float = None,
    ) -> None:
        """Initializes a DoubleSlider instance."""
        super().__init__(orientation)
        self._multi = 10 ** decimals
        self.valueChanged.connect(self.emitDoubleValueChanged)
        if minimum is not None:
            self.setMinimum(minimum)
        if maximum is not None:
            self.setMaximum(maximum)
        if singleStep is not None:
            self.setSingleStep(singleStep)
        if value is not None:
            self.setValue(value)


    def emitDoubleValueChanged(self) -> None:  # noqa
        """Signal that emits an appropriately scaled float value."""
        value = float(super().value())/self._multi
        self.doubleValueChanged.emit(value)

    def value(self) -> float:
        """Returns the current value as a float."""
        return float(super().value()) / self._multi

    def setValue(
            self,
            value: float,
    ) -> None:
        """Sets the current value on the slider."""
        super().setValue(int(value * self._multi))

    def setMinimum(
            self,
            value: float,
    ) -> None:
        """Sets the minimum value on the slider."""
        return super().setMinimum(int(value * self._multi))

    def setMaximum(
            self,
            value: float,
    ) -> None:
        """Sets the maximum value on the slider."""
        return super().setMaximum(int(value * self._multi))

    def singleStep(self) -> float:
        """Returns the single step value on the slider."""
        return float(super().singleStep()) / self._multi

    def setSingleStep(
            self,
            value: float,
    ) -> None:
        """Sets the single step value on the slider."""
        return super().setSingleStep(int(value * self._multi))
