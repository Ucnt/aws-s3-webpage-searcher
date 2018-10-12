
#!/usr/bin/env python3
from lib.constants import *
from lib.logger import *
from lib.traceback import *
from lib.progressbar import *
from lib.get_subpages import Page, get_subpages, get_source_code, get_domain
from module.test_upload import *
from module.find_s3_writable_buckets_constants import *
import datetime
import time
import multiprocessing
import queue
import requests
import urllib3
import http
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
import re
try:
    from urllib import urlopen
except:
    from urllib.request import urlopen
import threading
import time
sleep_between_checks = .1


def find_writable_buckets(urls, max_subpages=50):    #main method
    try:
        logger.log.critical("Checking for write-enabled or non-existant S3 buckets")

        vulns_found = []            #Store all vulns found

        pool_size = multiprocessing.cpu_count() * 2
        pool = multiprocessing.Pool(processes=pool_size)
        active_processes = []            #Store the processes until they are done
        for url in urls:
            active_processes.append(pool.apply_async(check_for_writable_buckets, (url, max_subpages)))
            
        #Give a progressbar as the active_processes come in
        num_items = len(urls)
        progress = ProgressBar(num_items=len(urls))
        while progress.cur_item < num_items or active_processes:
            for active_process in active_processes:
                if active_process.ready():
                    if active_process._value:
                        vulns_found.extend(active_process._value)
                    active_processes.remove(active_process)
                    progress(num_completed=1)
            progress(num_completed=0)        
            time.sleep(1)

        #Everything's done!    
        progress.done()
        pool.close()
        pool.join()

        logger.log.critical("Done checking for write-enabled or non-existant S3 buckets")
        return vulns_found
    except:
        logger.log.critical("Exception %s" % (get_exception().replace("\n", "  ")))
        return []

def check_for_writable_buckets(url, max_subpages):
    try:
        # logger.log.warning("Checking %s" % (url))
        start_time = time.time()
        vulns_found = []
        threads = []

        #Create the first page and set it up to store other page's buckets
        page = Page(url=url)
        page.source_code = get_source_code(page=page, include_js=True)
        page.buckets_dict = {}
        page.js_links_found = []

        #Get subpages
        get_subpages(page=page, max_subpages=max_subpages)

        #Run the base page
        t = threading.Thread(target=run_website, args=(page, page,))
        threads.append(t)
        t.start()

        for subpage in page.subpages:
            t = threading.Thread(target=run_website, args=(page, subpage,))
            threads.append(t)
            t.start()
            #Pause if at max length
            while len(threads) >= max_subpages:
                time.sleep(sleep_between_checks)
                for thread in threads:
                    if not thread.isAlive():
                        threads.remove(thread)

        #Wait for all threads to finish.
        while threads:
            #Remove finished thraeds
            for thread in threads:
                if not thread.isAlive():
                    threads.remove(thread)
            time.sleep(sleep_between_checks)
        
        #Compile buckets
        buckets_with_website = []
        for vuln_url, buckets in page.buckets_dict.items():
            for bucket in buckets:
                if not any(existing_bucket == bucket for vuln_url, existing_bucket in buckets_with_website):
                    buckets_with_website.append((vuln_url, bucket))

        #Run buckets
        if buckets_with_website:
            logger.log.warning("Running potential buckets for %s: %s" % (url, buckets_with_website))
            for bucket_with_website in buckets_with_website:
                vuln = test_upload(url, bucket_with_website)
                if vuln:
                    vulns_found.append(vuln)

        #log the URL as searched
        add_searched_site(url)

        # logger.log.warning("Finished %s in %s sec" % (url, (int(time.time()) - start_time)))
        return vulns_found
    except:
        logger.log.critical("Exception on %s: %s" % (url, get_exception().replace("\n", "  ")))
        return []


def add_searched_site(url):
    with open("%s/searched_sites.txt" % (list_dir), "a") as f:
        f.write(get_domain(url)+"\n")


def run_website(page, subpage):
    try:
        if subpage.source_code:
            #Reformat the source code to make S3 link extraction easier
            subpage.source_code = reformat_s3_links(subpage.source_code)
            find_buckets(page, subpage.url, subpage.source_code)

            #Get links from any javascript on the pages as well
            new_js_links = get_js_links(page, subpage.url, subpage.source_code)
            # if new_js_links:
                # logger.log.warning("%s JS links found on %s" % (len(new_js_links), subpage.url))
            for new_js_link in new_js_links:
                p = Page(url=new_js_link)
                source_code = get_source_code(p, include_js=True)
                source_code = reformat_s3_links(source_code)
                find_buckets(page, new_js_link, source_code)
    except:
        logger.log.critical("Exception on %s: %s" % (subpage.url, get_exception().replace("\n", "  ")))


def find_buckets(page, url, source_code):
    try:
        #Be sure it's not an ELB or other amazonaws link
        if "s3.amazonaws.com" not in source_code:
            return
        else:
            # logger.log.critical("%s - amazonaws found...Checking for buckets in source code." % (url))
            bucket_names = []
            good_bucket_names = []
            bad_bucket_names = []

            #Pull out all possible buckets
            bucket_names = extract_bucket_names(source_code)

            for bucket_name in list(set(bucket_names)):
                bucket_name = bucket_name.strip()
                #See if it got too much data from an earlier "//" string
                if "//" in bucket_name:
                    bucket_name = bucket_name.split("//")[len(bucket_name.split("//"))-1]

                #Add the bucket if it looks valid, checking if it is in the source code (e.g. no replacing messed it up)
                if bucket_name in source_code:
                    if not any(bad_bucket_name_content in bucket_name for bad_bucket_name_content in bad_bucket_name_contents):
                        if len(bucket_name) <= max_bucket_len and len(bucket_name) >= 3:
                            if bucket_name in junk_buckets:
                                bad_bucket_names.append(bucket_name)
                            elif "elasticbeanstalk-" in bucket_name:
                                bad_bucket_names.append(bucket_name)
                            elif "blacklist" in url:
                                bad_bucket_names.append(bucket_name)
                            else:
                                good_bucket_names.append(bucket_name)

            #Return unique bucket names
            good_bucket_names = list(set(good_bucket_names))
            page.buckets_dict[url] = good_bucket_names
    except:
        logger.log.critical("Exception %s" % (get_exception().replace("\n", "  ")))


def reformat_s3_links(source_code):
    #Remove DNS prefetch...
    source_code = source_code.replace("rel='dns-prefetch' href='//s3.amazonaws.com'", "")
    source_code = source_code.replace("rel='dns-prefetch' href='s3.amazonaws.com'", "")
    source_code = source_code.replace("rel='dns-prefetch' href='http://s3.amazonaws.com", "")
    source_code = source_code.replace("rel='dns-prefetch' href='https://s3.amazonaws.com", "")

    source_code = source_code.replace('rel="dns-prefetch" href="//s3.amazonaws.com"', '')
    source_code = source_code.replace('rel="dns-prefetch" href="s3.amazonaws.com"', '')
    source_code = source_code.replace('rel="dns-prefetch" href="http://s3.amazonaws.com', "")
    source_code = source_code.replace('rel="dns-prefetch" href="https://s3.amazonaws.com', "")

    #Remove region names so you don't have to worry about them in the regex
    source_code = source_code.replace(":80", "")
    source_code = source_code.replace(":8080", "")
    source_code = source_code.replace(":8000", "")
    source_code = source_code.replace(":443", "")
    source_code = source_code.replace("-us-east-2", "")
    source_code = source_code.replace("-us-east-1", "")
    source_code = source_code.replace("-us-west-2", "")
    source_code = source_code.replace("-us-west-1", "")
    source_code = source_code.replace("-ap-south-1", "")
    source_code = source_code.replace("-ap-northeast-1", "")
    source_code = source_code.replace("-ap-northeast-2", "")
    source_code = source_code.replace("-ap-northeast-3", "")
    source_code = source_code.replace("-ap-southeast-1", "")
    source_code = source_code.replace("-ap-southeast-2", "")
    source_code = source_code.replace("-ca-central-1", "")
    source_code = source_code.replace("-cn-north-1", "")
    source_code = source_code.replace("-eu-central-1", "")
    source_code = source_code.replace("-eu-west-1", "")
    source_code = source_code.replace("-eu-west-2", "")
    source_code = source_code.replace("-eu-west-3", "")
    source_code = source_code.replace("-sa-east-1", "")

    #Replace some of the html encoding
    source_code = str(source_code.replace("\/","/").replace("') + '", "").replace('") + "', ''))

    return source_code


def extract_bucket_names(source_code):
    try:
        bucket_names = []

        search_string = "s3.amazonaws.com"
        first_chars = [match.start() for match in re.finditer(re.escape(search_string), source_code)]

        for first_char in first_chars:
            start_index = (first_char-max_bucket_len) if (first_char-max_bucket_len) >=0 else 0
            end_index = first_char+max_bucket_len

            #Get subdomain strings
            bucket_names_subdomain = re.findall(r'''[\/'" ]([a-zA-Z0-9\.\-\_]{3,63})\.s3\.amazonaws\.com''', source_code[start_index:first_char+len(search_string)])
            #Be sure you've got the bucket name as the regex will take the first instance of the optional char
            for bucket_name in bucket_names_subdomain:
                # print(bucket_name)
                bucket_name = bucket_name.strip()
                for c in ("/", "'", '"', " "):
                    if str(c) in str(bucket_name):
                        bucket_name = bucket_name.split(c)[len(bucket_name.split(c))-1]
                bucket_names.append(bucket_name)

            #Get subfolder strings
            bucket_names_subfolder = re.findall(r'''[^.]s3\.amazonaws\.com\/([a-zA-Z0-9\.\-\_]{3,63})[\/'" ]''', source_code[first_char-1:end_index])
            #Be sure you've got the bucket name as the regex will take the last instance of the optional char
            for bucket_name in bucket_names_subfolder:
                # print(bucket_name)
                bucket_name = bucket_name.strip()
                for c in ("/", "'", '"', " "):
                    if c in bucket_name:
                        bucket_name.split(c)[0]
                bucket_names.append(bucket_name)

        return bucket_names
    except:
        logger.log.critical("Error extracting names: %s" % (get_exception().replace("\n", "  ")))


def get_js_links(page, url, source_code):
    # logger.log.warning("Checking for js on %s" % (url))
        
    #Get all links
    try:
        bsObj = BeautifulSoup(source_code, "html.parser")
    excepte:
        logger.log.warning("Error parsing source code: %s" % (get_exception().replace("\n", "  ")))
        return []

    new_js_links = []
    try:
        js_links = [i.get('src') for i in bsObj.find_all('script') if i.get('src')]
        for js_link in js_links:
            #See if it's an external lnk
            if js_link[0] == "/" and  js_link[1] == "/":
                js_link = js_link[2::]
                if js_link not in page.js_links_found:
                    page.js_links_found.append(js_link)
                    new_js_links.append(js_link)
            #Strip it of http/https just to clean it up
            else:            
                if "http" not in js_link:
                    #Just try it as is, e.g. if it's "somedomain.com/js/file.js"  Just be sure it's not a /.....
                    if js_link not in page.js_links_found:
                        if js_link[0] != "/":
                            page.js_links_found.append(js_link)
                            new_js_links.append(js_link)
                    #Also try it with the current domain, e.g. if it's "js/file.js"
                    if page.domain not in js_link:
                        if js_link[0] == "/":
                            js_link = "%s%s" % (page.domain, js_link)
                        else:
                            js_link = "%s/%s" % (page.domain, js_link)
                        if js_link not in page.js_links_found:
                            page.js_links_found.append(js_link)
                            new_js_links.append(js_link)
                #Just be sure it's in there in some way...
                if js_link not in page.js_links_found:
                    page.js_links_found.append(js_link)
                    new_js_links.append(js_link)
        return new_js_links
    except:
        logger.log.critical("Error parsing source code: %s" % (get_exception().replace("\n", "  ")))
        return new_js_links

def is_ok_error(e):
    try:
        for ok_error in ok_errors:
            if str(ok_error) in str(e):
                return True
        return False
    except:
        logger.log.critical("Exception %s" % (get_exception().replace("\n", "  ")))
