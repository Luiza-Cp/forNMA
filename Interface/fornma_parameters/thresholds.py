"""templates/thresholds.py - contains information of the threshold types and their parameters."""

_THRESHOLDS = {  # threshold name -> uses offset (True/False)
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
_DEFAULT_THRESHOLD = 'Triangle'
_DEFAULT_USES_OFFSET = _THRESHOLDS.get(_DEFAULT_THRESHOLD, False)


def get_threshold_names() -> list[str]:
    """Returns a list of all available thresholds."""
    return list(_THRESHOLDS.keys())


def get_default_threshold() -> str:
    """Returns the name of the default threshold."""
    return _DEFAULT_THRESHOLD


def threshold_has_offset(threshold_name: str) -> bool:
    """Returns whether a given threshold name utilizes an offset parameter or not."""
    return _THRESHOLDS.get(threshold_name, _DEFAULT_USES_OFFSET)
