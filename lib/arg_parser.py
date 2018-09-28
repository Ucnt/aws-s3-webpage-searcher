#!/usr/bin/env python3
###############################################
## Purpose: Provies argument parsing capability
###############################################
import argparse

parser = argparse.ArgumentParser(description='''''')

###############################################
## Optional arguments
###############################################
parser.add_argument('-w', '--webpage', default="", help='Run the test on this webpage only.')
parser.add_argument('-wl', '--webpage_list', default="", help='Run the test on the given list of webpages')
parser.add_argument('--max_subpages', default=0, type=int, help='Number of subpages to run from the initial webpage')

###############################################
## Debug Options
###############################################
parser.add_argument('-f', '--debug_file_name', help='Debug output file')
parser.add_argument('-v', '--print_verbose', action='store_true', help="Print verbose")

#Compile the argument paser options
args = parser.parse_args()
