#!/usr/bin/env python3
'''

Author: Matt Svensson

Purpose: Search through a webpage for write-enabled or non-existant S3 buckets.

'''
from lib.constants import *
from lib.arg_parser import *
from lib.logger import *
from lib.progressbar import *
from lib.get_subpages import get_domain
from module.find_s3_writable_buckets import find_writable_buckets
import multiprocessing
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
        f = open(args.webpage_list, "r")
        lines = list(set(f.readlines()))
        if rerun:
            logger.log.critical("Rerunning all %s urls." %(len(lines)))
            return lines
        else:
            logger.log.critical("Getting domains from %s urls.  Give me a sec..." %(len(lines)))
            progress = ProgressBar(num_items=len(lines))

            pool_size = multiprocessing.cpu_count() * 2
            pool = multiprocessing.Pool(processes=pool_size)
            active_processes = []            #Store the processes until they are done
            domains = []

            for line in lines:
                active_processes.append(pool.apply_async(get_domain, (line.strip(),)))

            #Compile the domains as they come in. 
            num_items = len(lines)
            while active_processes:
                for active_process in active_processes:
                    if active_process.ready():
                        if active_process._value:
                            domains.append(active_process._value)
                        active_processes.remove(active_process)
                        #Don't over-update the progressbar or it'll slow everything down.  Printing is SLOW
                        if len(active_processes) % 100 == 0:
                            progress(num_completed=len(lines) - len(active_processes) - progress.cur_item)
                progress(num_completed=0)        
                time.sleep(1)

            #Everything's done!    
            progress.done()
            pool.close()
            pool.join()

            remaining_domains = list(set(domains) - set(searched_sites))

            logger.log.critical("Removed previously run sites from the %s potential results, leaving %s to be run." % (len(searched_sites), len(remaining_domains)))
            
            return remaining_domains

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

    #Get the unique domains/urls.
    urls = get_urls(args=args, rerun=args.rerun)

    if urls:

        #Run the urls
        vulns_found = find_writable_buckets(urls=urls, max_subpages=args.max_subpages)

        #Print the vulns found
        print_vulns_found(vulns_found)
