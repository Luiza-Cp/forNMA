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
            'tooltip': "Path to the folder of the chanel where nuclei will be segmented",
            'help': " Is the path to the folder of the chanel where nuclei will be segmented. forNMA uses this path to identify images with stained nuclei. For example in an experiment with DAPI staining, this folder will contain blue channel images.",
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
            'tooltip': "Number identifying the objective magnification",
            'help': "Number identifying the objective magnification",
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
            'tooltip': "Size of one pixel, in micrometers, at the image",
            'help': "Corresponding size of one pixel, in micrometers, at the image. You can obtain this information within your microscope specifications. Although it is not mandatory to add a value here, the pixel size helps forNMA a lot in its measurements.",
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
            'tooltip': "Thresholding method used to differentiate between a nucleus and the image background",
            'help': "Is the thresholding method to be used to differentiate between a nucleus and the image background. There are 9 global thresholds and 2 local thresholds. The local thresholds also require an offset, which is a constant subtracted from weighted mean of neighborhood to calculate the local threshold value. The available thresholds are: Isodata, Li, Mean, Minimum, Median, Multi-otsu, Otsu, Triangle, Yen, Local Mean and Local Gaussian.",
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
            'tooltip': "Value subtracted from the  mean of pixel neighborhood",
            'help': "It is a constant subtracted from weighted mean of neighborhood to calculate the local threshold value.",
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
            'tooltip': "How much you want to smooth the nucleus edge",
            'help': "It is a value of how much the nucleus edges must be smoothed. It blurs the nuclear mask to make the contours more regular or smoother.",
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
            'tooltip': "Reduces or enlarges nucleus contour",
            'help': "Value used to adjust contours to the nucleus edge. Positive values will enlarge the contour in the specified number of pixels and negative values will reduce it.",
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
            'tooltip': "Filters nucleus by its irregularity.",
            'help': "Removes from analysis all nucleus that has irregular shapes. Higher values will be restrictive for more regular nucleus. Try to set lower values if you are working with treatments that affect nuclei shape.",
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
            'tooltip': "Filters nucleus by its eccentricity",
            'help': "Filters nuclei by their eccentricity, which is a value that shows you how 'un-circular' the curve is. Bigger eccentricities are less curved. A circle has an eccentricity of 0, and a ellipse will have an eccentricity of 1.",
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
            'tooltip': "Forces a cut between two nuclei",
            'help': "If active, forces a cut between two nuclei when watershed segmentation was not able to distinguish between two close nuclei. Bigger values will be more restrictive about when to generate a cut.",
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
            'tooltip': "Minimum nucleus area",
            'help': "Minimum area, in pixels, of a nucleus.",
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
            'tooltip': "Maximum nucleus area",
            'help': "Maximum area, in pixels, of a nucleus.",
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
            'name': "Min Radius",
            'label': "Set the min radius",
            'tooltip':  "Minimum nucleus radius",
            'help': "Minimum radius, in pixels, of a nucleus.",
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
            'name': "Max Radius",
            'label': "Set the max radius",
            'tooltip': "Maximum nucleus radius",
            'help': "Maximum radius, in pixels, of a nucleus.",
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
            'tooltip': "Crerates new intensity scale to images",
            'help': "Re-distributes image intensity so the brightest image pixel will be equivalent to the biggest intensity value and the less bright pixel will correspond to the minimum value. This enhances image contrast and is highly recommended for high background images.",
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
            'tooltip': "Background subtraction with rolling-ball algorithm",
            'help': "Applies rolling-ball algorithm for background subtraction. This parameter also requires a rolling-ball radius, that should be set to at least the size of the largest object that is not part of the background.",
        },
        'data': {
            'dtype': bool,
            'wtype': 'checkbox',
            'value': False,
        },
    },
    'radius_bg': {
        'text': {
            'name': "Rolling Ball Radius",
            'label': "Radius rolling-ball",
            'tooltip': "Is the rolling-ball radius used for background subtraction.",
            'help': "Is the rolling-ball radius used for background subtraction. Larger radius takes longer times to process.",
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
            'tooltip': "Activate this function if your nucleus is weakly stained",
            'help': "This parameter is used when nuclei stain is weak and the nuclear edges are not so clear for forNMA to identify. It is responsible for activate some extra functions that will try to identify correctly the nuclear edges.",
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
            'tooltip': "Activate this function if some nuclei are less brighter than others.",
            'help': "This parameter is responsible for executing a loop at images where previous found nucleus are covered and then forNMA tries to find new nucleus at image. It is recommended if some nuclei are way less brighter than others. This function can generate detection errors with squares being drawn around nuclues.",
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
            'tooltip': "Is the nuclei diameter, in pixel",
            'help': "Is the nuclei diameter, in pixel.",
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
            'tooltip': "Flow error threshold",
            'help': "Flow error threshold (all cells with errors below threshold are kept)",
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
            'tooltip': "All pixels with value above threshold kept for masks.",
            'help': "All pixels with value above threshold kept for masks, decrease to find more and larger masks.",
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
            'tooltip': "Allows the Cellpose operations to be performed using GPU.",
            'help': "Allows the Cellpose operations to be performed using GPU.",
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
            'tooltip': "Matches all image histograms.",
            'help': "Matches all image histogram with the first image in order to correct for illumination distortions.",
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
            'tooltip':  "Crerates new intensity scale to images",
            'help': "Re-distributes image intensity so the brightest image pixel will be equivalent to the biggest intensity value and the less bright pixel will correspond to the minimum value. This enhances image contrast and is highly recommended for high background images.",
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
            'tooltip': "Background subtraction with rolling-ball algorithm",
            'help': "Applies rolling-ball algorithm for background subtraction. This parameter also requires a rolling-ball radius, that should be set to at least the size of the largest object that is not part of the background.",
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
            'tooltip': "Is the rolling-ball radius used for background subtraction.",
            'help': "Is the rolling-ball radius used for background subtraction. Larger radius takes longer times to process.",
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
            'label': "Measure translocation?",
            'tooltip': "Activate protein translocation measures at this channel.",
            'help': "If selected, creates a cytoplasmic ring around the nucleus contour to measure fluorescence ratios between nucleus and cytoplasm.",
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
            'tooltip': "Is the cytoplasmic ring size in pixels.",
            'help': "Is the cytoplasmic ring size in pixels.",
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
            'tooltip': "Uses an ellipse around the nucleus instead of just enlarging nucleus.",
            'help': "Instead of enlarging the nuclear contour to create the cytoplasmic ring, uses an ellipse as the cytoplasmic ring, oriented towards nuclei direction. This is recommended in stretched cell lines, where cytoplasm is not equally distributed trough all nuclei edges.",
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
            'label': "Measure Foci?",
            'tooltip': "Counts and measures foci inside the nuclei.",
            'help': "Counts and measures foci inside the nuclei.",
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
            'tooltip': "Minimum number of pixels to consider as a foci",
            'help': "Minimum number of pixels to consider as a foci. If nothing is set, all foci will be included.",
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
            'tooltip': "Maximum number of pixels to consider as a foci",
            'help': "Maximum number of pixels to consider as a foci. If nothing is set, all foci will be included.",
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
            'tooltip': "Minimum mean intensity of a region to be considered a foci.",
            'help': "Minimum mean intensity of a region to be considered a foci.",
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
            'tooltip': "Maximum mean intensity of a region to be considered a foci.",
            'help': "Maximum mean intensity of a region to be considered a foci.",
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
    'foci_proeminence': {  # TODO: typo aqui - I know, mas deixei o parametro errado mesmo kkk
        'text': {
            'name': "Prominence",
            'label': "Select Foci prominence:",
            'tooltip': "Number of times that foci intensity has to be more intense than the nucleus.",
            'help': "Number of times that foci intensity has to be more intense than the nucleus.",
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
