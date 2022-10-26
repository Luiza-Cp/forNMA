#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 23 09:10:24 2022

@author: luiza
"""

import argparse
from tracking import tracking


# Create the parser
parser = argparse.ArgumentParser(description='Track cells from table')

# Add the arguments
parser.add_argument('path_to_table',
                       type= str,
                       help='pah to forNMA Results.csv')

parser.add_argument('path_to_save',
                       type=str,
                       help='path to save tracked csv')

parser.add_argument('-md', '--max_distance',
                    nargs='?',
                    type = int,
                    default = 200,
                    help = 'maximal distance to allow particle linking between frames')

parser.add_argument('-t', '--time_window',
                    nargs='?',
                    type = int,
                    default = 10,
                    help = 'maximal memory of the tracker to link track segments')

parser.add_argument('-ms', '--max_split_distance',
                    nargs='?',
                    type = int,
                    default = 30,
                    help = 'maximal distance to link segment starts to segment middlepoints')

parser.add_argument('-mg','--max_gap_closing_distance',
                    nargs='?',
                    type = int,
                    default = 10,
                    help = 'maximal distance for closing segment gaps')

parser.add_argument('-am', '--allow_merging',
                    nargs='?',
                    type = bool,
                    default = True,
                    help = 'indicates whether object merging is allowed or not ')


# Execute the parse_args() method
args = parser.parse_args()

path_to_table = args.path_to_table
path_to_save = args.path_to_save
max_distance =args.max_distance
time_window =args.time_window
max_split_distance = args.max_split_distance
max_gap_closing_distance = args.max_gap_closing_distance
allow_merging = args.allow_merging

tracking(path_to_table,path_to_save, max_distance, time_window, max_split_distance,
         max_gap_closing_distance, allow_merging)
