#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 10:15:18 2022

@author: luiza
"""


import argparse
from draw_tracking import draw_tracking


# Create the parser
parser = argparse.ArgumentParser(description='Track cells from table')

# Add the arguments
parser.add_argument('path_to_table',
                       type= str,
                       help='pah to forNMA Results.csv')

parser.add_argument('path_to_images',
                       type=str,
                       help='path to images folder')

parser.add_argument('path_to_save',
                       type=str,
                       help='path to save images')


parser.add_argument('-rs', '--rescale_intensity',
                    nargs='?',
                    type = bool,
                    default = False,
                    help = 'if True, adjusts image intensities. Recomended for low intensity images.')



# Execute the parse_args() method
args = parser.parse_args()

path_to_table = args.path_to_table
path_to_images = args.path_to_images
path_to_save = args.path_to_save
rescale_intensity = args.rescale_intensity

draw_tracking(path_to_table, path_to_images, path_to_save, rescale_intensity)

