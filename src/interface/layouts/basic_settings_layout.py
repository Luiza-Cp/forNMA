from PyQt5 import QtWidgets as qtw  # noqa

from src.interface.layouts.key_grid_layout import KeyGridLayout


class BasicSettingsLayout(KeyGridLayout):
    """
    Class representing a layout for selecting basic settings.
    Meant to be added to as a collapsible layout under forNMA's SettingsWidget.
    """
    def __init__(self):
        """Initializes a BasicSettingsLayout instance."""
        super().__init__()

        # Wants foci checkbox
        self.wants_foci_checkbox = qtw.QCheckBox('Foci', objectName='wants_foci')  # noqa
        self.addKeyWidget(self.wants_foci_checkbox, self.next_row, 0, 1, 2)

        # Foci channel layout
        foci_buttons_layout = qtw.QHBoxLayout()
        self.addLayout(foci_buttons_layout, self.next_row, 0, 1, 2)

        # Foci channel buttons
        self.foci_channel_1_button = qtw.QRadioButton('Channel 1', enabled=False)  # noqa
        self.foci_channel_2_button = qtw.QRadioButton('Channel 2', enabled=False, objectName='foci_channel2')  # noqa
        self.flagAsKeyWidget(self.foci_channel_2_button)

        # Foci channel button group
        self.foci_channel_radio_button_group = qtw.QButtonGroup()
        for cyto_ring_button in (self.foci_channel_1_button, self.foci_channel_2_button):
            foci_buttons_layout.addWidget(cyto_ring_button)
            self.foci_channel_radio_button_group.addButton(cyto_ring_button)
            self.wants_foci_checkbox.toggled.connect(cyto_ring_button.setEnabled)

        # Wants cytoplasmic ring checkbox
        self.wants_cyto_ring_checkbox = qtw.QCheckBox('Cytoplasmic Ring', objectName='wants_ktr')  # noqa
        self.addKeyWidget(self.wants_cyto_ring_checkbox, self.next_row, 0, 1, 2)

        # Cytoplasmic ring channel layout
        cyto_ring_buttons_layout = qtw.QHBoxLayout()
        self.addLayout(cyto_ring_buttons_layout, self.next_row, 0, 1, 2)

        # Cytoplasmic ring channel buttons
        self.cyto_ring_channel_1_button = qtw.QRadioButton('Channel 1', enabled=False)  # noqa
        self.cyto_ring_channel_2_button = qtw.QRadioButton('Channel 2', enabled=False, objectName='ktr_channel2')  # noqa
        self.flagAsKeyWidget(self.cyto_ring_channel_2_button)

        # Cytoplasmic ring channel button group
        self.cyto_ring_channel_radio_button_group = qtw.QButtonGroup()
        for cyto_ring_button in (self.cyto_ring_channel_1_button, self.cyto_ring_channel_2_button):
            cyto_ring_buttons_layout.addWidget(cyto_ring_button)
            self.cyto_ring_channel_radio_button_group.addButton(cyto_ring_button)
            self.wants_cyto_ring_checkbox.toggled.connect(cyto_ring_button.setEnabled)
