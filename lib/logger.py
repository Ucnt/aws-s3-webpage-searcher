#!/usr/bin/env python3
from lib.constants import *
import logging
import os
from lib.arg_parser import *
#Short format for printing to screen
formatter_stdout = logging.Formatter('''[*] {message}'''.format(asctime='%(asctime)s',message='%(message)s'))
#Verbose format for logging to file
formatter_file = logging.Formatter('''{asctime} | {message}'''.format(asctime='%(asctime)s',message='%(message)s'))


class Logger():
    def __init__(self, debug_file_name, print_stdout, print_verbose):
        self.log = logging.getLogger()

        # Log all CRITICAL AND WARNING to log.txt or the given file name
        if not debug_file_name:
            debug_file_name = "log.txt"
        fh = logging.FileHandler("%s/%s" % (log_dir, debug_file_name))
        fh.setLevel(logging.WARNING)
        fh.setFormatter(formatter_file)
        self.log.addHandler(fh)

        #Only print to stdout if requested
        if print_verbose or print_stdout:
            ch = logging.StreamHandler()
            if print_verbose:
                ch.setLevel(logging.WARNING)
            else:
                ch.setLevel(logging.CRITICAL)
            ch.setFormatter(formatter_stdout)
            self.log.addHandler(ch)

    def check_args(self, ):
        """Prints a debug notice if no printing was requested"""
        if not args.debug_file_name and not args.print_stdout and not args.print_verbose:
            print('''
=============================================================================================
*** Running with NO debugging ***
Output to file: --debug_file_name 'debug.log'  OR  --f 'debug.log'
Output to stdout: --print_debug  OR  -p
=============================================================================================
        ''')

logger = Logger(debug_file_name=args.debug_file_name, print_stdout=args.print_stdout, print_verbose=args.print_verbose)
logger.check_args()         #See if debugging will go to a file or the screen
