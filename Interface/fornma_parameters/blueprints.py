"""fornma_parameters/blueprint.py - module containing a blueprint for creating all of forNMA's parameters."""
from __future__ import annotations

from typing import Any, Type

# Threshold values -> has offset?
_THRESHOLD_HAS_OFFSET = {
    'Isodata': False,
    'Li': False,
    'Mean': False,
    'Minimum': False,
    'Median': False,
    'Multi-otsu': False,
    'Otsu': False,
    'Triangle': False,
    'Yen': False,
    'Local Mean': True,
    'Local Gaussian': True,
}
_DEFAULT_THRESHOLD = "Triangle"
_DEFAULT_HAS_OFFSET = _THRESHOLD_HAS_OFFSET.get(_DEFAULT_THRESHOLD, False)

_DEFAULT_NAME = "<NO NAME FOUND>"
_DEFAULT_LABEL = "<NO LABEL FOUND>"
_DEFAULT_TOOLTIP = "<NO TOOLTIP TEXT FOUND>"
_DEFAULT_HELP_MESSAGE = "<NO HELP MESSAGE FOUND>"
_DEFAULT_NUMERIC_LIMITS = {
    'minimum': 0.0,
    'maximum': 1.0,
    'singleStep': 0.01,
    'value': 0.5,
}
_DEFAULT_TEXT_OPTIONS = {
    'some_text': False,
    'other_text': True,
    'yet_another_text': True,
    'value': False,
}


_FORNMA_BLUEPRINT = {
    'channel_with_nuclei': {
        'text': {
            'name': "Channel with Nuclei",
            'label': "Select the channel with nuclei:",
            'tooltip': "TOOLTIP for channel with nuclei",
            'help': "HELP MESSAGE for channel with nuclei",
        },
        'data': {
            'dtype': str,
            'wtype': 'combobox',
            # Options and value start empty because the values come from user input
            'options': [],
            'value': "",
        }
    },
    'magnification': {
        'text': {
            'name': "Magnification",
            'label': "Select the image magnification:",
            'tooltip': "TOOLTIP for magnification",
            'help': "HELP MESSAGE for magnification",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 1000,
                'singleStep': 5,
                'value': (value := 20),
            },
            'value': value,
        },
    },
    'pixel_size': {
        'text': {
            'name': "Pixel Size",
            'label': "Select the pixel size (µm):",
            'tooltip': "TOOLTIP for pixel size",
            'help': "HELP MESSAGE for pixel size",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0001,
                'maximum': 1_000.0,
                'singleStep': 0.01,
                'value': (value := 0.5),
            },
            'value': value,
        },
    },
    'threshold': {
        'text': {
            'name': "Threshold Type",
            'label': "Select the threshold strategy:",
            'tooltip': "TOOLTIP for threshold",
            'help': "HELP MESSAGE for threshold",
        },
        'data': {
            'dtype': str,
            'wtype': 'combobox',
            'options': {
                'Isodata': {'has_offset': False},
                'Li': {'has_offset': False},
                'Mean': {'has_offset': False},
                'Minimum': {'has_offset': False},
                'Median': {'has_offset': False},
                'Multi-otsu': {'has_offset': False},
                'Otsu': {'has_offset': False},
                'Triangle': {'has_offset': False},
                'Yen': {'has_offset': False},
                'Local Mean': {'has_offset': True},
                'Local Gaussian': {'has_offset': True},
            },
            'value': _DEFAULT_THRESHOLD,
        },
    },
    'offset': {
        'text': {
            'name': "Threshold Offset",
            'label': "Set the offset:",
            'tooltip': "TOOLTIP for offset",
            'help': "HELP MESSAGE for offset",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.05,
                'value': (value := 0.5),
            },
            'value': value,
        },
    },
    'blur': {
        'text': {
            'name': "Smooth",
            'label': "Set the smoothness:",
            'tooltip': "TOOLTIP for blur",
            'help': "HELP MESSAGE for blur",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 100.0,
                'singleStep': 0.05,
                'value': (value := 12.0),
            },
            'value': value,
        },
    },
    'adjust_size': {
        'text': {
            'name': "Adjust Size",
            'label': "Set the adjust size value:",
            'tooltip': "TOOLTIP for adjust_size",
            'help': "HELP MESSAGE for adjust_size",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': -1_000.0,
                'maximum': 1_000.0,
                'singleStep': 0.05,
                'value': (value := 0.0),
            },
            'value': value,
        },
    },
    'shape': {
        'text': {
            'name': "Shape",
            'label': "Set the shape value:",
            'tooltip': "TOOLTIP for shape",
            'help': "HELP MESSAGE for shape",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': (value := 0.88),
            },
            'value': value,
        },
    },
    'eccentricity': {
        'text': {
            'name': "Eccentricity",
            'label': "Set the eccentricity value:",
            'tooltip': "TOOLTIP for eccentricity",
            'help': "HELP MESSAGE for eccentricity",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': (value := 0.0),
            },
            'value': value,
        },
    },
    'cut_edges': {
        'text': {
            'name': "Cut Edges",
            'label': "Set the cut edges value:",
            'tooltip': "TOOLTIP for cut edges",
            'help': "HELP MESSAGE for cut edges",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': (value := 0.5),
            },
            'value': value,
        },
    },
    'min_size': {
        'text': {
            'name': "Min Size",
            'label': "Set the min size",
            'tooltip': "TOOLTIP for min size",
            'help': "HELP MESSAGE for min size",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': (value := 0.2),
            },
            'value': value,
        },
    },
    'max_size': {
        'text': {
            'name': "Max Size",
            'label': "Set the max size",
            'tooltip': "TOOLTIP for max size",
            'help': "HELP MESSAGE for max size",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': (value := 0.8),
            },
            'value': value,
        },
    },
    'min_radius': {
        'text': {
            'name': "Min Size",
            'label': "Set the min radius",
            'tooltip': "TOOLTIP for min radius",
            'help': "HELP MESSAGE for min radius",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': (value := 0.2),
            },
            'value': value,
        },
    },
    'max_radius': {
        'text': {
            'name': "Max Size",
            'label': "Set the max radius",
            'tooltip': "TOOLTIP for max radius",
            'help': "HELP MESSAGE for max radius",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': (value := 0.8),
            },
            'value': value,
        },
    },
    'rescale_intensity': {
        'text': {
            'name': "Rescale Intensity",
            'label': "Rescale intensity?",
            'tooltip': "TOOLTIP for rescale_intensity",
            'help': "HELP MESSAGE for rescale_intensity",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'remove_background': {
        'text': {
            'name': "Remove Background",
            'label': "Remove background?",
            'tooltip': "TOOLTIP for remove_background",
            'help': "HELP MESSAGE for remove_background",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'radius_bg': {
        'text': {
            'name': "Rolling Ball",
            'label': "Radius rolling-ball",
            'tooltip': "TOOLTIP for radius_bg",
            'help': "HELP MESSAGE for radius_bg",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 500.0,
                'singleStep': 1,
                'value': (value := 10.0),
            },
            'value': value,
        },
    },
    'weakly_labeled': {
        'text': {
            'name': "Weakly Labeled",
            'label': "Images are weakly labeled?",
            'tooltip': "TOOLTIP for weakly_labeled",
            'help': "HELP MESSAGE for weakly_labeled",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'find_low_intensity_nucleus': {
        'text': {
            'name': "Find Low Intensity Nuclei",
            'label': "Find low intensity nuclei?",
            'tooltip': "TOOLTIP for find_low_intensity_nucleus",
            'help': "HELP MESSAGE for find_low_intensity_nucleus",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
}
_CELLPOSE_BLUEPRINT = {
    'diameter': {
        'text': {
            'name': "Nuclear Diameter",
            'label': "Select the nuclear diameter:",
            'tooltip': "TOOLTIP for diameter",
            'help': "HELP MESSAGE for diameter",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 1000,
                'singleStep': 5,
                'value': (value := 20),
            },
            'value': value,
        },
    },
    'flow_threshold': {
        'text': {
            'name': "Flow Threshold",
            'label': "Select the flow threshold:",
            'tooltip': "TOOLTIP for flow_threshold",
            'help': "HELP MESSAGE for flow_threshold",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1000.0,
                'singleStep': 0.5,
                'value': (value := 20.0),
            },
            'value': value,
        },
    },
    'mask_threshold': {
        'text': {
            'name': "Mask Threshold",
            'label': "Select the mask threshold:",
            'tooltip': "TOOLTIP for mask_threshold",
            'help': "HELP MESSAGE for mask_threshold",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 1000.0,
                'singleStep': 0.5,
                'value': (value := 20.0),
            },
            'value': value,
        },
    },
    'cellpose_rescale_intensity': {  # TODO: confirmar se são parâmetros separados ou não
        'text': {
            'name': "Rescale Intensity",
            'label': "Rescale intensity?",
            'tooltip': "TOOLTIP for rescale_intensity",
            'help': "HELP MESSAGE for rescale_intensity",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'cellpose_remove_background': {  # TODO: confirmar se são parâmetros separados ou não
        'text': {
            'name': "Remove Background",
            'label': "Remove background?",
            'tooltip': "TOOLTIP for remove_background",
            'help': "HELP MESSAGE for remove_background",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'use_gpu': {
        'text': {
            'name': "Run in GPU",
            'label': "Run in GPU?",
            'tooltip': "TOOLTIP for use_gpu",
            'help': "HELP MESSAGE for use_gpu",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
}
_CHANNELS_BLUEPRINT = {
    'match_hist': {
        'text': {
            'name': "Match Histograms",
            'label': "Match histograms?",
            'tooltip': "TOOLTIP for match histograms",
            'help': "HELP MESSAGE for match histograms",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'channel_rescale_intensity': {
        'text': {
            'name': "Rescale Intensity",
            'label': "Rescale Intensity?",
            'tooltip': "TOOLTIP for rescale intensity",
            'help': "HELP MESSAGE for rescale intensity",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'remove_bg': {
        'text': {
            'name': "Remove Background",
            'label': "Remove Background?",
            'tooltip': "TOOLTIP for remove bg",
            'help': "HELP MESSAGE for remove bg",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'channel_radius_bg': {
        'text': {
            'name': "Rolling Ball",
            'label': "Radius rolling-ball",
            'tooltip': "TOOLTIP for radius_bg",
            'help': "HELP MESSAGE for radius_bg",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 500,
                'singleStep': 1,
                'value': (value := 10),
            },
            'value': value,
        },
    },
    'wants_ktr': {
        'text': {
            'name': "Translocation",
            'label': "Use KTR translocation?",
            'tooltip': "TOOLTIP for wants_ktr",
            'help': "HELP MESSAGE for wants KTR",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'ring_size': {
        'text': {
            'name': "Ring Size",
            'label': "Select ring size:",
            'tooltip': "TOOLTIP for ring size",
            'help': "HELP MESSAGE for ring size",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 500,
                'singleStep': 1,
                'value': (value := 10),
            },
            'value': value,
        },
    },
    'use_ellipse': {
        'text': {
            'name': "Use Ellipse",
            'label': "Use ellipse?",
            'tooltip': "TOOLTIP for use_ellipse",
            'help': "HELP MESSAGE for use_ellipse",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'wants_foci': {
        'text': {
            'name': "Foci",
            'label': "Use Foci?",
            'tooltip': "TOOLTIP for wants_foci",
            'help': "HELP MESSAGE for wants FOCI",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'foci_min_size': {
        'text': {
            'name': "Min Size",
            'label': "Select Foci min size:",
            'tooltip': "TOOLTIP for foci min size",
            'help': "HELP MESSAGE for foci min size",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 500,
                'singleStep': 1,
                'value': (value := 10),
            },
            'value': value,
        },
    },
    'foci_max_size': {
        'text': {
            'name': "Max Size",
            'label': "Select Foci max size:",
            'tooltip': "TOOLTIP for foci max size",
            'help': "HELP MESSAGE for foci max size",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 500,
                'singleStep': 1,
                'value': (value := 100),
            },
            'value': value,
        },
    },
    'foci_min_int': {
        'text': {
            'name': "Min Intensity",
            'label': "Select Foci min intensity:",
            'tooltip': "TOOLTIP for foci min intensity",
            'help': "HELP MESSAGE for foci min intensity",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 500,
                'singleStep': 1,
                'value': (value := 10),
            },
            'value': value,
        },
    },
    'foci_max_int': {
        'text': {
            'name': "Max Intensity",
            'label': "Select Foci max intensity:",
            'tooltip': "TOOLTIP for foci max intensity",
            'help': "HELP MESSAGE for foci max intensity",
        },
        'data': {
            'dtype': int,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0,
                'maximum': 500,
                'singleStep': 1,
                'value': (value := 100),
            },
            'value': value,
        },
    },
    'foci_proeminence': {  # TODO: typo aqui
        'text': {
            'name': "Prominence",
            'label': "Select Foci prominence:",
            'tooltip': "TOOLTIP for foci prominence",
            'help': "HELP MESSAGE for foci prominence",
        },
        'data': {
            'dtype': float,
            'wtype': 'spinbox',
            'limits': {
                'minimum': 0.0,
                'maximum': 10.0,
                'singleStep': 0.05,
                'value': (value := 1.0),
            },
            'value': value,
        },
    },
}


_BLUEPRINTS = dict(**_FORNMA_BLUEPRINT, **_CELLPOSE_BLUEPRINT, **_CHANNELS_BLUEPRINT)


# MAIN FUNCTIONS --------------------------------------------------------------

def validate_fornma_id(fornma_id: str) -> None:
    """Raises a ValueError if the forNMA ID is not valid."""
    if fornma_id not in _BLUEPRINTS:
        raise ValueError(f"forNMA ID {fornma_id} not found in blueprint file.")


def _get_from_dict(
        fornma_id: str,
        dict_name: str,
        key: str,
        default: Any,
) -> Any:
    """Returns the text parameter for the given forNMA ID."""
    return _BLUEPRINTS.get(fornma_id, {}).get(dict_name, {}).get(key, default)


# TEXT DICT -------------------------------------------------------------------

def _get_from_text_dict(
        fornma_id: str,
        key: str,
        default: Any,
) -> str:
    """Returns the text parameter for the given forNMA ID."""
    return _get_from_dict(fornma_id=fornma_id, dict_name='text', key=key, default=default)


def get_fornma_name(fornma_id: str) -> str:
    """Returns the parameter name for the given forNMA ID."""
    return _get_from_text_dict(fornma_id=fornma_id, key='name', default=_DEFAULT_NAME)


def get_fornma_label(fornma_id: str) -> str:
    """Returns the descriptive label for the given forNMA ID."""
    return _get_from_text_dict(fornma_id=fornma_id, key='label', default=_DEFAULT_LABEL)


def get_fornma_tooltip(fornma_id: str) -> str:
    """Returns the tooltip text for the given forNMA ID."""
    return _get_from_text_dict(fornma_id=fornma_id, key='tooltip', default=_DEFAULT_TOOLTIP)


def get_fornma_help_message(fornma_id: str) -> str:
    """Returns the help message for the given forNMA ID."""
    return _get_from_text_dict(fornma_id=fornma_id, key='help', default=_DEFAULT_HELP_MESSAGE)


# DATA DICT -------------------------------------------------------------------

def _get_from_data_dict(
        fornma_id: str,
        key: str,
        default: Any,
) -> Any:
    """Returns the data parameter for the given forNMA ID."""
    return _get_from_dict(fornma_id=fornma_id, dict_name='data', key=key, default=default)


def get_fornma_text_options(fornma_id: str) -> dict[str, int | float]:
    """Returns the text options for the given forNMA ID."""
    return _get_from_data_dict(fornma_id=fornma_id, key='options', default=_DEFAULT_TEXT_OPTIONS)


def get_fornma_numeric_limits(fornma_id: str) -> dict[str, int | float]:
    """Returns the limit values for the given forNMA ID."""
    return _get_from_data_dict(fornma_id=fornma_id, key='limits', default=_DEFAULT_NUMERIC_LIMITS)


def get_fornma_value(fornma_id: str) -> dict[str, int | float]:
    """Returns the value for the given forNMA ID."""
    return _get_from_data_dict(fornma_id=fornma_id, key='value', default=None)


def get_fornma_dtype(fornma_id: str) -> Type[int] | Type[float] | Type[str] | Type[bool]:
    """Returns the data type of the value for the given forNMA ID."""
    return _get_from_data_dict(fornma_id=fornma_id, key='dtype', default=None)


# THRESHOLDS ------------------------------------------------------------------

def get_default_threshold() -> str:
    """Returns the name of the default threshold."""
    return _DEFAULT_THRESHOLD


def _get_threshold_options() -> dict[str, dict]:
    """Returns a dictionary of the threshold options."""
    return _get_from_data_dict(fornma_id='threshold', key='options', default={})


def get_threshold_names() -> list[str]:
    """Returns a list of all available thresholds."""
    thresholds = _get_threshold_options()
    return list(thresholds.keys())


def threshold_has_offset(threshold_name: str) -> bool:
    """Returns whether a given threshold name utilizes an offset parameter or not."""
    thresholds = _get_threshold_options()
    return thresholds.get(threshold_name, {}).get('has_offset', _DEFAULT_HAS_OFFSET)
