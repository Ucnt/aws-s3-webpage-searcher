#!/usr/bin/env python3
import os
from lib.arg_parser import *

#Current file directory
lib_dir = os.path.dirname(os.path.realpath(__file__))
main_dir = os.path.dirname(os.path.dirname(__file__))
log_dir = "%s/log" % (main_dir)
list_dir = "%s/list" % (main_dir)


#Headers for requests
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}


#Threading vars
sleep_betwee_checks = .1
max_num_threads = 10    



