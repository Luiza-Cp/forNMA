from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa


class DoubleSlider(qtw.QSlider):
    """
    A QSlider that works with float values, instead of integers.
    source: https://stackoverflow.com/questions/42820380/use-float-for-qslider
    """
    doubleValueChanged = qtc.pyqtSignal(float)

    def __init__(
            self,
            decimals: int = 3,
            *args,
            **kwargs,
    ) -> None:
        """Initializes a DoubleSlider instance."""
        super().__init__(*args, **kwargs)
        self._multi = 10 ** decimals
        self.valueChanged.connect(self.emitDoubleValueChanged)

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
        return super().setMinimum(value * self._multi)

    def setMaximum(
            self,
            value: float,
    ) -> None:
        """Sets the maximum value on the slider."""
        return super().setMaximum(value * self._multi)

    def singleStep(self) -> float:
        """Returns the single step value on the slider."""
        return float(super().singleStep()) / self._multi

    def setSingleStep(
            self,
            value: float,
    ) -> None:
        """Sets the single step value on the slider."""
        return super().setSingleStep(value * self._multi)
