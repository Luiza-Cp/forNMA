from PyQt5 import QtCore as qtc, QtWidgets as qtw  # noqa

from src.interface.layouts.key_grid_layout import KeyGridLayout
from src.interface.helpers.slider_widgets import SliderWidgets


class AdvancedSettingsLayout(KeyGridLayout):
    """
    Class representing a layout for selecting advanced settings.
    Meant to be added to as a collapsible layout under forNMA's SettingsWidget.
    """
    threshold_names = [
        'triangle',
        'isodata',
        'li',
        'mean',
        'median',
        'minimum',
        'otsu',
        'multiotsu',
        'yen',
        'local mean',
        'local gaussian',
    ]
    thresholds_with_offset = [
        'local mean',
        'local_gaussian',
    ]
    offset_spinbox_values = {
        'minimum': 0,
        'maximum': 10,
        'singleStep': 1,
        'value': 2,
    }
    blur_slider_values = {
        'minimum': 0,
        'maximum': 20,
        'singleStep': 1,
        'value': 12,
    }
    adjust_size_slider_values = {
        'minimum': -50,
        'maximum': 50,
        'singleStep': 1,
        'value': 0,
    }
    cut_edges_slider_values = {
        'minimum': 0.0,
        'maximum': 1.0,
        'singleStep': 0.01,
        'value': 0.70,
    }
    shape_slider_values = {
        'minimum': 0.0,
        'maximum': 1.0,
        'singleStep': 0.01,
        'value': 0.88,
    }
    eccentricity_slider_values = {
        'minimum': 0.0,
        'maximum': 1.0,
        'singleStep': 0.01,
        'value': 0.5,
    }

    def __init__(self):
        """Initializes a AdvancedSettingsLayout instance."""
        super().__init__()

        # Threshold label
        self.addWidget(qtw.QLabel('threshold'), self.next_row, 0, 1, 1)

        # Threshold combobox
        self.threshold_combobox = qtw.QComboBox(objectName='threshold')  # noqa
        for threshold_name in self.threshold_names:
            self.threshold_combobox.addItem(threshold_name)
        self.addKeyWidget(self.threshold_combobox, self.current_row, 1, 1, 1)

        # Offset label
        self.offset_label = qtw.QLabel('offset', enabled=False)  # noqa
        self.addWidget(self.offset_label, self.next_row, 0, 1, 1)

        # Offset spinbox
        self.offset_spinbox = qtw.QSpinBox(objectName='offset', enabled=False, **self.offset_spinbox_values)  # noqa
        self.addKeyWidget(self.offset_spinbox, self.current_row, 1, 1, 1)

        # Blur slider
        self.blur_slider, self.blur_checkbox, self.blur_spinbox = SliderWidgets(
            dtype='int',
            label='Blur',
            slider_name='blur',
            **self.blur_slider_values,
        ).items()
        self.addWidget(self.blur_checkbox, self.next_row, 0, 1, 1)
        self.addWidget(self.blur_spinbox, self.current_row, 1, 1, 1)
        self.addKeyWidget(self.blur_slider, self.next_row, 0, 1, 2)

        # Adjust size slider
        self.adjust_size_slider, self.adjust_size_checkbox, self.adjust_size_spinbox = SliderWidgets(
            dtype='int',
            label='Adjust size',
            slider_name='adjust_size',
            **self.adjust_size_slider_values,
        ).items()
        self.addWidget(self.adjust_size_checkbox, self.next_row, 0, 1, 1)
        self.addWidget(self.adjust_size_spinbox, self.current_row, 1, 1, 1)
        self.addKeyWidget(self.adjust_size_slider, self.next_row, 0, 1, 2)

        # Cut edges slider
        self.cut_edges_slider, self.cut_edges_checkbox, self.cut_edges_spinbox = SliderWidgets(
            dtype='float',
            label='Cut edges',
            slider_name='cut_edges',
            **self.cut_edges_slider_values,
        ).items()
        self.addWidget(self.cut_edges_checkbox, self.next_row, 0, 1, 1)
        self.addWidget(self.cut_edges_spinbox, self.current_row, 1, 1, 1)
        self.addKeyWidget(self.cut_edges_slider, self.next_row, 0, 1, 2)

        # Shape slider
        self.shape_slider, self.shape_checkbox, self.shape_spinbox = SliderWidgets(
            dtype='float',
            label='Shape',
            slider_name='shape',
            **self.shape_slider_values,
        ).items()
        self.addWidget(self.shape_checkbox, self.next_row, 0, 1, 1)
        self.addWidget(self.shape_spinbox, self.current_row, 1, 1, 1)
        self.addKeyWidget(self.shape_slider, self.next_row, 0, 1, 2)

        # Eccentricity slider
        self.eccentricity_slider, self.eccentricity_checkbox, self.eccentricity_spinbox = SliderWidgets(
            dtype='float',
            label='Eccentricity',
            slider_name='eccentricity',
            **self.eccentricity_slider_values,
        ).items()
        self.addWidget(self.eccentricity_checkbox, self.next_row, 0, 1, 1)
        self.addWidget(self.eccentricity_spinbox, self.current_row, 1, 1, 1)
        self.addKeyWidget(self.eccentricity_slider, self.next_row, 0, 1, 2)

        # TODO: add these parameters below to the interface!
        # # Size min/max
        # self.advanced_settings_form.addRow('Size filter (pixels)', None)  # noqa
        # self.max_size_spinbox = qtw.QSpinBox(minimum=0, maximum=1_000_000, singleStep=1, value=0)  # noqa
        # self.advanced_settings_form.addRow('Max:', self.max_size_spinbox)
        # self.min_size_spinbox = qtw.QSpinBox(minimum=0, maximum=1_000_000, singleStep=1, value=0)  # noqa
        # self.advanced_settings_form.addRow('Min:', self.min_size_spinbox)
        # # Radius min/max
        # self.advanced_settings_form.addRow('Radius filter (pixels)', None)  # noqa
        # self.max_radius_spinbox = qtw.QSpinBox(minimum=0, maximum=1_000_000, singleStep=1, value=0)  # noqa
        # self.advanced_settings_form.addRow('Max:', self.max_radius_spinbox)
        # self.min_radius_spinbox = qtw.QSpinBox(minimum=0, maximum=1_000_000, singleStep=1, value=0)  # noqa
        # self.advanced_settings_form.addRow('Min:', self.min_radius_spinbox)

        # Connections
        self.threshold_combobox.currentTextChanged.connect(self.on_threshold_combobox_current_text_changed)

    @qtc.pyqtSlot(str)
    def on_threshold_combobox_current_text_changed(
            self,
            current_value: str,
    ) -> None:
        """Enables or disables the offset label and spinbox, based on the currently selected threshold."""
        if current_value in self.thresholds_with_offset:
            self.offset_spinbox.setEnabled(True)
            self.offset_label.setEnabled(True)
        else:
            self.offset_spinbox.setEnabled(False)
            self.offset_label.setEnabled(False)
