#!/usr/bin/env python3
'''

Author: Matt Svensson

Purpose: Search through a webpage for write-enabled or non-existant S3 buckets.

'''
from lib.constants import *
from lib.arg_parser import *
from lib.logger import *
from lib.get_subpages import get_domain
from module.find_s3_writable_buckets import find_writable_buckets
import json



def get_searched_sites():
    searched_sites = []
    try:
        f = open("%s/searched_sites.txt" % (list_dir), "r")
        for line in f:
            searched_sites.append(get_domain(line.strip().lower()))
        return list(set(searched_sites))
    except:
        with open("%s/searched_sites.txt" % (list_dir), "a") as f:
            pass
        return []


def get_urls(args, rerun):
    searched_sites = get_searched_sites()

    urls = []
    if args.webpage:
        urls.append(args.webpage)
    if args.webpage_list:
        if not rerun:
            logger.log.critical("Removing %s previously run sites.  Give me a sec..." %(len(searched_sites)))
        for line in open(args.webpage_list):
            line = line.strip()
            if line:
                if get_domain(line) not in searched_sites or rerun:
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

    vulns_found = find_writable_buckets(urls=get_urls(args=args, rerun=args.rerun), max_subpages=args.max_subpages)

    print_vulns_found(vulns_found)
