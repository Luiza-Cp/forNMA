"""templates/tooltips.py - defines the text used in the tooltips."""


_TOOLTIPS = {  # forNMA ID -> tooltip text
    'channel_with_nuclei': "This is the channel with nuclei text.",
    'magnification': "Tooltip Magnification",
    'pixel_size': "Tooltip for pixel size - no info yet!",
    'threshold': "Tooltip for threshold...",
    'offset': "tooltip! for the offset",
    'blur': "This is smooth + blur",
    'adjust_size': "ADJUST SIZE tooltip",
    'shape': "SHAPE tooltip",
    'eccentricity': "eccentricity tooltip",
    'cut_edges': "cut_edges tooltip",
    'size': "SIZE MIN MAX tooltip",
    'radius': "RADIUS MIN MAX tooltip",
    'rescale_intensity': "Rescale???",
    'remove_bg': "Remove???",
    'radius_bg': "Rolling ball",
    'weakly_labeled': "These are some weakly labeled stuff",
    'find_low_intensity_nucleus': "Let's try to find them!",
}

_DEFAULT_TOOLTIP = "<NO TOOLTIP TEXT FOUND>"


def get_fornma_tooltip(fornma_id: str) -> str:
    """Returns the tooltip text for the given forNMA ID."""
    return _TOOLTIPS.get(fornma_id, _DEFAULT_TOOLTIP)
