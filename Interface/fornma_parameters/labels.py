"""
templates/labels.py - defines the labels ("translations") between each widget's
internal identifier string and its user-friendly version.
"""

_NAMES = {  # forNMA ID -> label
    'channel_with_nuclei': "Channel with Nuclei",
    'magnification': "Image Magnification",
    'pixel_size': "Pixel Size (µm)",
    'threshold': "Threshold type",
    'offset': "Image Offset (px)",
    'blur': "Smooth",
    'adjust_size': "Adjust Size",
    'shape': "Shape",
    'eccentricity': "Eccentricity",
    'cut_edges': "Cut Edges",
    'size': "Size",
    'radius': "Radius",
    'rescale_intensity': "Rescale Intensity",
    'remove_bg': "Remove Background",
    'radius_bg': "Rolling Ball",
    'weakly_labeled': "Weakly labeled",
    'find_low_intensity_nucleus': "Find Low Intensity Nuclei",
}

_DEFAULT_NAME = "<NO NAME FOUND>"


def get_fornma_name(fornma_id: str) -> str:
    """Returns the name for the given forNMA ID."""
    return _NAMES.get(fornma_id, _DEFAULT_NAME)


_LABELS = {  # forNMA ID -> label
    'channel_with_nuclei': "Select the with Nuclei:",
    'magnification': "Select Image Magnification:",
    'pixel_size': "Select Pixel Size (µm):",
    'threshold': "Select threshold type:",
    'offset': "Select the image offset:",
    'blur': "Select the smoothness:",
    'adjust_size': "Adjust the size:",
    'shape': "Set shape:",
    'eccentricity': "Set eccentricity:",
    'cut_edges': "Set cut edges:",
    'size': "Set size:",
    'radius': "Set radius:",
    'rescale_intensity': "Set rescale intensity:",
    'remove_bg': "Set remove background:",
    'radius_bg': "Set rolling ball:",
    'weakly_labeled': "Weakly labeled?",
    'find_low_intensity_nucleus': "Find Low Intensity Nuclei?",
}

_DEFAULT_LABEL = "<NO LABEL FOUND>"


def get_fornma_label(fornma_id: str) -> str:
    """Returns the descriptive label for the given forNMA ID."""
    return _LABELS.get(fornma_id, _DEFAULT_LABEL)
