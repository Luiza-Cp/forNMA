"""helpers/double_slider_widget.py - module containing a slider widget that uses floating point values."""

from __future__ import annotations

from PySide6 import QtCore as qtc, QtWidgets as qtw


class SliderSpinBox(qtw.QWidget):
    valueChanged = qtc.Signal(object)  # int | float
    """
    Class representing a layout containing a slider widget and a spinbox to its side,
    which both displays and selects the current widget value.
    """
    def __init__(
            self,
            minimum: int | float = 0.0,
            maximum: int | float = 1.0,
            singleStep: int | float = 0.05,
            value: int | float = 0.5,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a SliderSpinBox instance."""
        super().__init__(parent=parent)

        # Layout
        layout = qtw.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Slider
        self.slider = AutoSlider(minimum=minimum, maximum=maximum, singleStep=singleStep, value=value)
        layout.addWidget(self.slider)

        # Spinbox
        self.spinbox = AutoSpinBox(minimum=minimum, maximum=maximum, singleStep=singleStep, value=value)
        layout.addWidget(self.spinbox)

        # Connect slider to label
        self.slider.doubleValueChanged.connect(self.on_value_changed)  # noqa
        self.spinbox.valueChanged.connect(self.on_value_changed)  # noqa

    def on_value_changed(
            self,
            new_value: float | int,
    ) -> None:
        """Updates the slider value whenever the spinbox value changes, and emits it."""
        if (sender := self.sender()) == self.slider:
            self.spinbox.blockSignals(True)
            self.spinbox.setValue(new_value)
            self.spinbox.blockSignals(False)
        elif sender == self.spinbox:
            self.slider.blockSignals(True)
            self.slider.setValue(new_value)
            self.slider.blockSignals(False)
        self.valueChanged.emit(new_value)


class DoubleSliderLabeledLayout(qtw.QHBoxLayout):
    """
    Class representing a layout containing a DoubleSliderWidget and a label to its side,
    that displays the currently selected value.
    """
    def __init__(
            self,
            left_label: str = None,
            minimum: int | float = 0.0,
            maximum: int | float = 1.0,
            step: int | float = 0.05,
            value: int | float = 0.5,
            enabled: bool = False,
            parent: qtw.QWidget = None,
    ) -> None:
        """Initializes a DoubleSliderLabeledLayout instance."""
        super().__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)

        # Optional left label
        self.left_label = None
        if left_label is not None:
            self.left_label = qtw.QLabel(left_label)
            self.addWidget(self.left_label)
            self.left_label.setEnabled(enabled)

        # Slider
        self.slider = DoubleSlider()
        self.addWidget(self.slider)
        # Slider params
        self.slider.setMaximum(maximum)
        self.slider.setMinimum(minimum)
        self.slider.setSingleStep(step)
        self.slider.setValue(value)
        self.slider.setEnabled(enabled)

        # Label
        self.label = qtw.QLabel()
        self.addWidget(self.label)
        # Label params
        self.label.setText(f'{value:.2f}')
        self.label.setEnabled(enabled)

        # Connect slider to label
        self.slider.doubleValueChanged.connect(self.on_slider_value_changed)

    def on_slider_value_changed(
            self,
            value: float,
    ) -> None:
        """Writes the current slider value to the label, whenever it changes."""
        self.label.setText(f'{value:.2f}')

    @qtc.Slot(bool)
    def setEnabled(
            self,
            enabled: bool,
    ) -> None:
        """Slot for setting the slider and label state to enabled/disabled."""
        if self.left_label is not None:
            self.left_label.setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.label.setEnabled(enabled)


class DoubleSlider(qtw.QSlider):
    """
    A QSlider that works with float values, instead of integers.
    source: https://stackoverflow.com/questions/42820380/use-float-for-qslider
    """
    doubleValueChanged = qtc.Signal(float)

    def __init__(
            self,
            decimals: int = 3,
            orientation: qtc.Qt.Orientation = qtc.Qt.Horizontal,
    ) -> None:
        """Initializes a DoubleSlider instance."""
        super().__init__(orientation=orientation)
        self._multi = 10 ** decimals
        self.valueChanged.connect(self.emitDoubleValueChanged)  # noqa

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


def AutoSpinBox(
        minimum: int | float = 0.0,
        maximum: int | float = 1.0,
        singleStep: int | float = 0.05,
        value: int | float = 0.5,
) -> qtw.QDoubleSpinBox | qtw.QSpinBox:
    """Returns the proper spinbox class depending on the type of the input parameters."""
    spinbox = qtw.QSpinBox()
    if any(isinstance(v, float) for v in [minimum, maximum, singleStep, value]):  # User wants to use floats
        spinbox = qtw.QDoubleSpinBox()
    spinbox.setMinimum(minimum)
    spinbox.setMaximum(maximum)
    spinbox.setSingleStep(singleStep)
    spinbox.setValue(value)
    return spinbox


def AutoSlider(
        minimum: int | float = 0.0,
        maximum: int | float = 1.0,
        singleStep: int | float = 0.05,
        value: int | float = 0.5,
) -> qtw.QSlider | DoubleSlider:
    """Returns the proper slider class depending on the type of the input parameters."""
    slider = qtw.QSlider()
    if any(isinstance(v, float) for v in [minimum, maximum, singleStep, value]):  # User wants to use floats
        slider = DoubleSlider()
    slider.setMinimum(minimum)
    slider.setMaximum(maximum)
    slider.setSingleStep(singleStep)
    slider.setValue(value)
    return slider
