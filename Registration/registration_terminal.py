#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  3 09:18:17 2022

@author: luiza
"""

import argparse
from registration import registration
from typing import List

# Create the parser
parser = argparse.ArgumentParser(description='Register images in a folder')

# Add the arguments
parser.add_argument('list_of_paths',
                       type=List[str],
                       help='a list with path to folderto register. If there are more image channels, each must be in a separate folder, inside the list.')

parser.add_argument('path_to_save',
                       type=str,
                       help='path to save registered images')


parser.add_argument('--crop',
                    nargs='?',
                    type=bool,
                    default = True,
                    help='Crop images to keep only portions that are allways in the field of view')

# Execute the parse_args() method
args = parser.parse_args()

paths = args.list_of_paths
save = args.path_to_save
crop= args.crop

registration(paths, save, crop )