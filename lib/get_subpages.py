#!/usr/bin/env python3
from lib.traceback import *
from lib.logger import *
from lib.constants import *
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
import re
try:
    from urllib import urlopen
except:
    from urllib.request import urlopen
import threading
import time
sleep_betwee_checks = .5
max_num_threads = 10

#Headers for http requests
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}
#Content in HTML that indicates that the pages is not valid

ok_errors = [
            "Read timed out",
            "Invalid URL",
            "InvalidURL",
            "timed out",
            "Failed to establish a new connection",
            "Max retries exceeded with url",
            "UnicodeError",
            "KeyError",
            "InvalidSchema",
            "InvalidURL",
            "ConnectionError",
            "Connection reset by peer",
            "Connection aborted",
            "RemoteDisconnected",
            "content-type",
            "InvalidSchema",
            "TooManyRedirects",
            "NotImplementedError",
            "No connection adapters were found",
]


def get_subpages_recursive(url, max_subpages=30):
    try:
        if not max_subpages:
            return [url]
            
        all_subpages = [url]
        unchecked_subpages = [url]

        while True:
            #If you are at the limit, return only # requested
            if len(all_subpages) >= max_subpages:
                break

            #Start the next unchecked page
            try:
                threading.Thread(target=get_subpages_recursive_helper, args=(unchecked_subpages.pop(), all_subpages, unchecked_subpages, max_subpages)).start()
            except IndexError:
                pass

            #If at the max num threads, wait until you're below it.
            while threading.active_count() >= max_num_threads:
                time.sleep(sleep_betwee_checks)

            if threading.active_count() == 1:
                break

        # logger.log.warning("Returning %s subpages for %s" % (len(all_subpages), url))
        return all_subpages
    except:
        logger.log.critical("Error getting subpages for %s: %s" % (url, get_exception()))
        return []


def get_subpages_recursive_helper(url, all_subpages, unchecked_subpages, max_subpages):
    try:
        #See which of the subpages are new
        subpages = get_subpages(url=url)
        new_subpages =  list(set(subpages) - set(all_subpages))

        #Add new subpages
        if new_subpages:
            new_subpages = new_subpages[:max_subpages-len(all_subpages)]
            all_subpages.extend(new_subpages)
            unchecked_subpages.extend(new_subpages)
    except:
        logger.log.critical("Error getting subpages for %s: %s" % (url, get_exception()))


def get_subpages(url):
    # logger.log.warning("Checking for sub pages from %s" % (url))

    #Get all links
    try:
        bsObj = BeautifulSoup(get_source_code(url), "html.parser")
    except:
        logger.log.critical("Error parsing source code: %s" % (get_exception().replace("\n", "  ")))
        return []

    try:
        a_items = list(set(bsObj.find_all('a')))
        links = []
        for a_item in a_items:
            try:
                href = a_item.get('href')
                if href and len(href) >= 2:
                    #Skip mailto links
                    if "mailto:" in href:
                        continue
                    #Cut off when the url has a leading "/"
                    if href[0] == "/" and  href[1] == "/":
                        href = href[2::]
                    else:
                        #Need to check after "?" to prevent 3rd party links, e.g. shares to FB or Google+
                        if "?" in str(href):
                            if get_url_base(url) in href.split("?")[1]:
                                href = href.split("?")[0]
                        #See if the base domains are the same (might end up with a subpage having the domain name)
                        if get_url_base(url) == get_url_base(href):
                            links.append(href)
                        elif href[0] == "/":
                            href = "%s/%s" % (get_url_base(url), href[1::])
                            links.append(href)
            except:
                logger.log.critical("Error getting subpages for %s: %s" % (url, get_exception().replace("\n", "  ")))
                pass

        #Get unique set of lnks
        unique_links = list(set(links))
        if unique_links:
            pass
            # logger.log.warning("Subpages from %s: %s" % (url, unique_links))
        return unique_links
    except:
        logger.log.critical("Error getting subpages for %s: %s" % (url, get_exception().replace("\n", "  ")))
        return []


def get_source_code(url):
    try:
        #If http is already in the url, just process it
        if "http" in url.lower():
            try:
                if possible_download_link(url):
                    # logger.log.warning("Skipping possible download link %s" % (url))
                    return ""
                r = requests.get(url, verify=False, timeout=10, headers=headers)
                return r.text
            except:
                pass

        #If http isn't in the URL, need to try different ways to get to the source code
        for protocol in ("http://","https://"):
            for www in ("", "www."):
                url_to_check = "%s%s%s" % (protocol, www, url)
                try:
                    if possible_download_link(url_to_check):
                        return ""
                    r = requests.get(url_to_check, verify=False, timeout=10, headers=headers)
                    return r.text
                except Exception as e:
                    if not is_ok_error(e):
                        logger.log.critical("Error - %s - %s" % (url, get_exception().replace("\n", "  ")))

        #Final return just in case....
        return ""
    except:
        logger.log.warning("Error getting source code for %s: %s" % (url, get_exception().replace("\n", "  ")))
        return ""


def possible_download_link(url):
    try:
        r = requests.get(url, verify=False, stream=True, timeout=10)
        # print(vars(r))
        content_type = r.headers['Content-Type']
        try:
            file_size = int(r.headers['Content-Length'])
            #If page is >= 3MB (aka 3,000,000 bits), skip it
            if file_size >= 3000000:
                # logger.log.critical("Skipping %s - Large page: %s bits" % (url, file_size))
                return True
        except:
            pass
        
        if "text/html" in content_type:
            return False
        else:
            # logger.log.critical("Skipping %s - Not HTML: %s" % (url, content_type))
            return True
    except Exception as e:
        if not is_ok_error(e):
            logger.log.critical("Exception %s" % (get_exception().replace("\n", "  ")))
        return True


def get_url_base(url):
    """Returns the base url, e.g. https://this.site.com/some/subpage returns site.com"""
    try:
        base_url = url.replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
        if len(base_url.split(".")) > 2:
            base_url_parts = base_url.split(".")
            base_url = "%s.%s" % (base_url_parts[len(base_url_parts)-2], base_url_parts[len(base_url_parts)-1])
        return base_url.strip()
    except Exception as e:
        logger.log.critical("Error getting base url for %s - %s" % (url, e))
        return url.strip()


def is_ok_error(e):
    try:
        for ok_error in ok_errors:
            if str(ok_error) in str(e):
                return True
        return False
    except: 
        logger.log.critical("Exception %s" % (get_exception().replace("\n", "  ")))
