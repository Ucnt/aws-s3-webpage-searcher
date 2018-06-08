#!/usr/bin/env python3
'''

Author: Matt Svensson

Purpose: Search through a webpage for write-enabled or non-existant S3 buckets.

'''
from lib.constants import *
from lib.arg_parser import *
from lib.logger import *
from module.find_s3_writable_buckets import find_writable_buckets
import json


def get_urls(args):
    urls = []
    if args.webpage:
        urls.append(args.webpage)
    if args.webpage_list:
        for line in open(args.webpage_list):
            line = line.strip()
            if line:
                urls.append(line)
    return urls


def print_vulns_found(vulns_found):
    if vulns_found:
        logger.log.critical("*** VULNS FOUND!! ***") 
        for vuln in vulns_found:
            logger.log.critical(json.dumps(vuln))
    else:
        logger.log.critical("*** No vulns found :( ***") 



if __name__ == "__main__":
    logger.log.critical("Running: %s" % (args))
    vulns_found = []

    vulns_found = find_writable_buckets(urls=get_urls(args), max_subpages=args.max_subpages)

    print_vulns_found(vulns_found)
