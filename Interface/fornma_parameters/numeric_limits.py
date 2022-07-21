"""
templates/numeric_limits.py - module defining the min/max/step values for forNMA parameters.
"""

_NUMERIC_LIMITS = {  # forNMA ID -> limit dict
    'magnification': {
        'minimum': 0,
        'maximum': 1000,
        'singleStep': 5,
        'value': 20,
    },
    'pixel_size': {
        'minimum': 0.0001,
        'maximum': 1_000.0,
        'singleStep': 0.01,
        'value': 0.5,
    },
    'blur': {
        'minimum': 0.0,
        'maximum': 100.0,
        'singleStep': 12.0,
        'value': 0.05,
    },
    'adjust_size': {
        'minimum': -1_000.0,
        'maximum': 1_000.0,
        'singleStep': 0.05,
        'value': 0.0,
    },
    'shape': {
        'minimum': 0.0,
        'maximum': 1.0,
        'singleStep': 0.01,
        'value': 0.88,
    },
    'eccentricity': {
        'minimum': 0.0,
        'maximum': 1.0,
        'singleStep': 0.01,
        'value': 0.0,
    },
    'cut_edges': {
        'minimum': 0.0,
        'maximum': 1.0,
        'singleStep': 0.01,
        'value': 0.5,
    },
}

_DEFAULT_NUMERIC_LIMITS = {
    'minimum': 0.0,
    'maximum': 1.0,
    'singleStep': 0.01,
    'value': 0.5,
}


def get_fornma_numeric_limits(fornma_id: str) -> dict[str, int | float]:
    """Returns the limit values for the given forNMA ID."""
    return _NUMERIC_LIMITS.get(fornma_id, _DEFAULT_NUMERIC_LIMITS)
