"""fornma_parameters/blueprint.py - module containing a blueprint for creating all of forNMA's parameters."""

_FORNMA_BLUEPRINT = [
    {
        'fornma_id': 'channel_with_nuclei',
        'text': {
            'name': "Channel with Nuclei",
            'label': "Select the channel with nuclei:",
            'tooltip': "TOOLTIP for channel with nuclei",
            'help': "HELP MESSAGE for channel with nuclei",
        },
        'data': {
            'type': str,
            # Value and options start empty because the values come from user input
            'value': "",
            'options': {},
        }
    },
    {
        'fornma_id': 'magnification',
        'text': {
            'name': "Magnification",
            'label': "Select the image magnification:",
            'tooltip': "TOOLTIP for magnification",
            'help': "HELP MESSAGE for magnification",
        },
        'data': {
            'type': int,
            'limits': {
                'minimum': 0,
                'maximum': 1000,
                'singleStep': 5,
                'value': 20,
            },
        },
    },
    {
        'fornma_id': 'pixel_size',
        'text': {
            'name': "Pixel Size",
            'label': "Select the pixel size (µm):",
            'tooltip': "TOOLTIP for pixel size",
            'help': "HELP MESSAGE for pixel size",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0001,
                'maximum': 1_000.0,
                'singleStep': 0.01,
                'value': 0.5,
            },
        },
    },
    {
        'fornma_id': 'threshold',
        'text': {
            'name': "Threshold Type",
            'label': "Select the threshold strategy:",
            'tooltip': "TOOLTIP for threshold",
            'help': "HELP MESSAGE for threshold",
        },
        'data': {
            'type': str,
            'value': "Triangle",
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
        },
    },
    {
        'fornma_id': 'offset',
        'text': {
            'name': "Threshold Offset",
            'label': "Set the offset:",
            'tooltip': "TOOLTIP for offset",
            'help': "HELP MESSAGE for offset",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.05,
                'value': 0.5,
            },
        },
    },
    {
        'fornma_id': 'blur',
        'text': {
            'name': "Smooth",
            'label': "Set the smoothness:",
            'tooltip': "TOOLTIP for blur",
            'help': "HELP MESSAGE for blur",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 100.0,
                'singleStep': 0.05,
                'value': 12.0,
            },
        },
    },
    {
        'fornma_id': 'adjust_size',
        'text': {
            'name': "Adjust Size",
            'label': "Set the adjust size value:",
            'tooltip': "TOOLTIP for adjust_size",
            'help': "HELP MESSAGE for adjust_size",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': -1_000.0,
                'maximum': 1_000.0,
                'singleStep': 0.05,
                'value': 0.0,
            },
        },
    },
    {
        'fornma_id': 'shape',
        'text': {
            'name': "Shape",
            'label': "Set the shape value:",
            'tooltip': "TOOLTIP for shape",
            'help': "HELP MESSAGE for shape",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': 0.88,
            },
        },
    },
    {
        'fornma_id': 'eccentricity',
        'text': {
            'name': "Eccentricity",
            'label': "Set the eccentricity value:",
            'tooltip': "TOOLTIP for eccentricity",
            'help': "HELP MESSAGE for eccentricity",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': 0.0,
            },
        },
    },
    {
        'fornma_id': 'cut_edges',
        'text': {
            'name': "Cut Edges",
            'label': "Set the cut edges value:",
            'tooltip': "TOOLTIP for cut edges",
            'help': "HELP MESSAGE for cut edges",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': 0.5,
            },
        },
    },
    {
        'fornma_id': 'min_size',
        'text': {
            'name': "Min Size",
            'label': "Set the min size",
            'tooltip': "TOOLTIP for min size",
            'help': "HELP MESSAGE for min size",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': 0.5,
            },
        },
    },
    {
        'fornma_id': 'max_size',
        'text': {
            'name': "Max Size",
            'label': "Set the max size",
            'tooltip': "TOOLTIP for max size",
            'help': "HELP MESSAGE for max size",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': 0.5,
            },
        },
    },
    {
        'fornma_id': 'min_radius',
        'text': {
            'name': "Min Size",
            'label': "Set the min radius",
            'tooltip': "TOOLTIP for min radius",
            'help': "HELP MESSAGE for min radius",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': 0.5,
            },
        },
    },
    {
        'fornma_id': 'max_radius',
        'text': {
            'name': "Max Size",
            'label': "Set the max radius",
            'tooltip': "TOOLTIP for max radius",
            'help': "HELP MESSAGE for max radius",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1.0,
                'singleStep': 0.01,
                'value': 0.5,
            },
        },
    },
    {
        'fornma_id': 'rescale_intensity',
        'text': {
            'name': "Rescale Intensity",
            'label': "Rescale intensity?",
            'tooltip': "TOOLTIP for rescale_intensity",
            'help': "HELP MESSAGE for rescale_intensity",
        },
        'data': {
            'type': bool,
            'state': False,
        },
    },
    {
        'fornma_id': 'remove_background',
        'text': {
            'name': "Remove Background",
            'label': "Remove background?",
            'tooltip': "TOOLTIP for remove_background",
            'help': "HELP MESSAGE for remove_background",
        },
        'data': {
            'type': bool,
            'state': False,
        },
    },
    {
        'fornma_id': 'radius_bg',
        'text': {
            'name': "Rolling Ball",
            'label': "Radius rolling-ball",
            'tooltip': "TOOLTIP for radius_bg",
            'help': "HELP MESSAGE for radius_bg",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 100.0,
                'singleStep': 0.01,
                'value': 10.0,
            },
        },
    },
    {
        'fornma_id': 'weakly_labeled',
        'text': {
            'name': "Weakly Labeled",
            'label': "Images are weakly labeled?",
            'tooltip': "TOOLTIP for weakly_labeled",
            'help': "HELP MESSAGE for weakly_labeled",
        },
        'data': {
            'type': bool,
            'state': False,
        },
    },
    {
        'fornma_id': 'find_low_intensity_nucleus',
        'text': {
            'name': "Find Low Intensity Nuclei",
            'label': "Find low intensity nuclei?",
            'tooltip': "TOOLTIP for find_low_intensity_nucleus",
            'help': "HELP MESSAGE for find_low_intensity_nucleus",
        },
        'data': {
            'type': bool,
            'state': False,
        },
    },
]

_CELLPOSE_BLUEPRINT = [
    {
        'fornma_id': 'diameter',
        'text': {
            'name': "Nuclear Diameter",
            'label': "Select the nuclear diameter:",
            'tooltip': "TOOLTIP for diameter",
            'help': "HELP MESSAGE for diameter",
        },
        'data': {
            'type': int,
            'limits': {
                'minimum': 0,
                'maximum': 1000,
                'singleStep': 5,
                'value': 20,
            },
        },
    },
    {
        'fornma_id': 'flow_threshold',
        'text': {
            'name': "Flow Threshold",
            'label': "Select the flow threshold:",
            'tooltip': "TOOLTIP for flow_threshold",
            'help': "HELP MESSAGE for flow_threshold",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1000.0,
                'singleStep': 0.5,
                'value': 20.0,
            },
        },
    },
    {
        'fornma_id': 'mask_threshold',
        'text': {
            'name': "Mask Threshold",
            'label': "Select the mask threshold:",
            'tooltip': "TOOLTIP for mask_threshold",
            'help': "HELP MESSAGE for mask_threshold",
        },
        'data': {
            'type': float,
            'limits': {
                'minimum': 0.0,
                'maximum': 1000.0,
                'singleStep': 0.5,
                'value': 20.0,
            },
        },
    },
    {
        'fornma_id': 'cellpose_rescale_intensity',  # TODO: confirmar se são parâmetros separados ou não
        'text': {
            'name': "Rescale Intensity",
            'label': "Rescale intensity?",
            'tooltip': "TOOLTIP for rescale_intensity",
            'help': "HELP MESSAGE for rescale_intensity",
        },
        'data': {
            'type': bool,
            'state': False,
        },
    },
    {
        'fornma_id': 'cellpose_remove_background',  # TODO: confirmar se são parâmetros separados ou não
        'text': {
            'name': "Remove Background",
            'label': "Remove background?",
            'tooltip': "TOOLTIP for remove_background",
            'help': "HELP MESSAGE for remove_background",
        },
        'data': {
            'type': bool,
            'state': False,
        },
    },
    {
        'fornma_id': 'use_gpu',
        'text': {
            'name': "Run in GPU",
            'label': "Run in GPU?",
            'tooltip': "TOOLTIP for use_gpu",
            'help': "HELP MESSAGE for use_gpu",
        },
        'data': {
            'type': bool,
            'state': False,
        },
    },
]
