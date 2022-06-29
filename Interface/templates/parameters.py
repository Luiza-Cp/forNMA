class NumericLimits:
    """
    Class defining min/max/step values for parameters. Also defines their default value.
    limits are meant to be accessed with the "get" class method.
    """
    _limits = {  # parameter name -> limit dict
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
    _default_limit = {
        'minimum': 0.0,
        'maximum': 1.0,
        'singleStep': 0.01,
        'value': 0.5,
    }

    @classmethod
    def get(
            cls,
            parameter_name: str,
    ) -> dict[str, int | float]:
        """Returns the limit values for the given parameter name."""
        return cls._limits.get(parameter_name, cls._default_limit)


class ToolTipText:
    """
    Class defining the tooltip text for different parameters.
    Tooltip text is meant to be accessed with the "get" class method.
    """
    _tooltips = {  # parameter name -> tooltip text
        'channel_with_nuclei': "This is the channel with nuclei text.",
        'magnification': "No tooltip yet!",
        'pixel_size': "Tooltip",
        'threshold': "Tooltip",
        'offset': "tooltip",
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
    _default_tooltip = "<NO TOOLTIP TEXT FOUND>"

    @classmethod
    def get(
            cls,
            parameter_name: str,
    ) -> str:
        """Returns the tooltip text for the given parameter name."""
        return cls._tooltips.get(parameter_name, cls._default_tooltip)


class ThresholdTypes:
    """
    Class defining the existing threshold. Also defines their default value.
    limits are meant to be accessed with the "get" class method.
    """
    _thresholds = {  # threshold name -> uses offset?
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
    default_threshold = 'Triangle'
    _default_uses_offset = False

    @classmethod
    def get_names(
            cls,
    ) -> list[str]:
        """Returns a list of all available threshold types."""
        return list(cls._thresholds.keys())

    @classmethod
    def get(
            cls,
            threshold_name: str,
    ) -> bool:
        """Returns whether a given threshold name utilizes an offset parameter or not."""
        return cls._thresholds.get(threshold_name, cls._default_uses_offset)
