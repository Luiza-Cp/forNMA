#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  9 11:02:07 2022

@author: luiza

this file is going to trnalate TOML parameters to forNMA inputs
"""

import toml
from run import run


import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Runs segmentation and feature extaction')
    
    parser.add_argument('parameters',
                           type= str,
                           help='path to parameters.toml')

    parser.add_argument('--headless',
                           type=bool,
                           default = False,
                           help='path to save registered images')

    return parser.parse_args()




args = parse_args()
run(toml.load(args.parameters), args.headless)



