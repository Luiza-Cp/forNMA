"""templates/help.py - defines the text used as help messages."""


_HELP_MESSAGES = {  # forNMA ID -> help message
    'channel_with_nuclei': "HELP channel",
    'magnification': "HELP Magnification",
    'pixel_size': "HELP with pixels",
    'threshold': "Help across thresholds",
    'offset': "Help offset\nmultiple lines",
    'blur': "HELP blur",
    'adjust_size': "HELP adjust size",
    'shape': "HELP shape",
    'eccentricity': "HELP ecc",
    'cut_edges': "HELP cut",
    'size': "HELP size",
    'radius': "HELP radius",
    'rescale_intensity': "HELP rescale",
    'remove_bg': "HELP",
    'radius_bg': "HELP BG",
    'weakly_labeled': "HELPS WEAK",
    'find_low_intensity_nucleus': "HELP Low Int",
}

_DEFAULT_HELP_MESSAGE = "<NO HELP MESSAGE FOUND>"


def get_fornma_help_message(fornma_id: str) -> str:
    """Returns the help message for the given forNMA ID."""
    return _HELP_MESSAGES.get(fornma_id, _DEFAULT_HELP_MESSAGE)
