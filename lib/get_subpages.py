#!/usr/bin/env python3
from lib.constants import *
from lib.traceback import *
from lib.logger import *
from lib.error_ignore import check_error_ignore
import requests
import urllib.parse
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
sleep_between_checks = 1
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}


class Page():
    def __init__ (self, url):
        self.url = url
        self.source_code = ""
        self.domain = get_domain(url)
        self.subdomain = get_domain(url, with_subdomain=True)
        self.invalid = False                                    #ability to remove non HTML/JS pages as they're found
        self.links = []
        self.subpages = []


def get_subpages(page, max_subpages=30, include_js=True):
    try:
        #If you're not asking for any subpages, just return
        if not max_subpages:
            return
            
        get_page_links(page)
        page.all_urls = page.links
        page.unchecked_urls = page.links

        threads = []
        while True:
            #If no active threads and either nothing left to look at or at max, end
            if not threads and (not page.unchecked_urls or len(page.subpages) >= max_subpages):
                break

            #If you are below the limit of subpages (found+active) and under the max num threads, add more!!
            if ((len(page.subpages)+len(threads)) < max_subpages) and (len(threads) < max_num_threads):
                #Start the next unchecked page
                try:
                    t = threading.Thread(target=get_subpages_helper, args=(page, page.unchecked_urls.pop(0), include_js))
                    threads.append(t)
                    t.start()
                except IndexError:
                    pass
            elif len(threads) >= max_num_threads:
                time.sleep(sleep_between_checks)

            #Remove finished thraeds
            for thread in threads:
                if not thread.isAlive():
                    threads.remove(thread)

            #Remove any invalid pages
            for subpage in page.subpages:
                if subpage.invalid:
                    page.subpages.remove(subpage)
    except:
        logger.log.warning("Error getting subpages for %s: %s" % (page.url, get_exception().replace("\n", "  ")))


def get_subpages_helper(page, unchecked_url, include_js):
    try:
        #See which of the subpages are new
        new_subpage = Page(url=unchecked_url)
        page.subpages.append(new_subpage)
        get_page_links(page=new_subpage, include_js=include_js)
        new_subpages =  list(set(new_subpage.links) - set(page.all_urls))

        #Add new subpages
        if new_subpages:
            page.all_urls.extend(new_subpages)
            page.unchecked_urls.extend(new_subpages)
    except:
        logger.log.warning("Error getting subpages for %s: %s" % (url, get_exception().replace("\n", "  ")))


def get_page_links(page, include_js=True):
    # logger.log.warning("Checking for sub pages from %s" % (url))

    #Get all links
    try:
        page.source_code = get_source_code(page, include_js)
        bsObj = BeautifulSoup(page.source_code, "html.parser")
    except:
        logger.log.warning("Error parsing source code: %s" % (get_exception().replace("\n", "  ")))
        return []

    try:
        a_items = list(set(bsObj.find_all('a')))
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
                        #If its own domain isn't in the string and no other TLDs are, either a subpage or child page
                        if page.domain not in href:
                            #IF the href has a TLD, it's prob going somewhere else
                            try:
                                get_domain(href)
                                continue
                            except:
                                pass
                            #Might be a child page
                            if "../" in href:
                                page.links.append("%s/%s" % ("/".join(page.url.split("/")[:-2]), href.replace("../","")))
                            else:
                                page.links.append("%s/%s" % (page.domain, href))
                        #Need to check after "?" to prevent 3rd party links, e.g. shares to FB or Google+
                        if "?" in str(href):
                            if page.domain in href.split("?")[1]:
                                href = href.split("?")[0]
                        #See if the base domains are the same (might end up with a subpage having the domain name)
                        if page.domain == get_domain(href):
                            page.links.append(href)
                        elif href[0] == "/":
                            page.links.append("%s/%s" % (page.domain, href[1::]))
            except:
                logger.log.warning("Error getting subpages for %s: %s" % (url, get_exception().replace("\n", "  ")))
                pass

        #Get unique set of lnks
        page.links = list(set(page.links))
        if page.links:
            pass
            # logger.log.warning("Subpages from %s: %s" % (url, unique_links))
    except:
        logger.log.warning("Error getting links for %s: %s" % (page.url, get_exception().replace("\n", "  ")))


def get_source_code(page, include_js):
    try:
        #If http is already in the url, just process it
        if "http" in page.url.lower():
            try:
                if invalid_webpage(page.url, include_js):
                    page.invalid = True
                    return ""
                r = requests.get(page.url, verify=False, timeout=10, headers=headers)
                page.url = r.url            #Update the URL to the redirected one
                return urllib.parse.unquote(r.text.encode().decode("unicode_escape"))
            except:
                # logger.log.warning("Error getting source code for %s - %s" % (url, get_exception().replace("\n", "  ")))
                pass

        #If http isn't in the URL, need to try different ways to get to the source code
        for protocol in ("http://","https://"):
            for www in ("", "www."):
                url_to_check = "%s%s%s" % (protocol, www, page.url)
                try:
                    if invalid_webpage(url_to_check, include_js):
                        page.invalid = True
                        return ""
                    r = requests.get(url_to_check, verify=False, timeout=10, headers=headers)
                    page.url = r.url            #Update the URL to the redirected one
                    return urllib.parse.unquote(r.text.encode().decode("unicode_escape"))
                except Exception as e:
                    # logger.log.warning("Error getting source code for %s - %s" % (url, get_exception().replace("\n", "  ")))
                    pass

        #Final return just in case....
        return ""
    except:
        logger.log.warning("Error getting source code for %s - %s" % (page.url, get_exception().replace("\n", "  ")))
        return ""


def invalid_webpage(url, include_js):
    try:
        r = requests.get(url, verify=False, stream=True, timeout=10)
        # logger.log.warning(vars(r))
        content_type = r.headers['Content-Type']
        try:
            file_size = int(r.headers['Content-Length'])
            #If page is >= 3MB (aka 3,000,000 bits), skip it
            if file_size >= 3000000:
                # logger.log.warning("Skipping %s - Large page: %s bits" % (url, file_size))
                return True
        except:
            pass
        
        if "text/html" in content_type or "javascript" in content_type:
            return False
        else:
            # logger.log.warning("Skipping %s - Not HTML: %s" % (url, content_type))
            return True
    except Exception as e:
        return True


def get_domain(url, with_subdomain=False):
    """Returns the base url, e.g. https://this.site.com/some/subpage returns site.com"""
    try:
        base_url = url.replace("http://", "").replace("https://", "").split("/")[0]
        if with_subdomain:
            return base_url
        else:
            if len(base_url.split(".")) > 2:
                base_url_parts = base_url.split(".")
                base_url = "%s.%s" % (base_url_parts[len(base_url_parts)-2], base_url_parts[len(base_url_parts)-1])
            return base_url.strip()
    except Exception as e:
        logger.log.warning("Error getting base url for %s - %s" % (url, e))
        return url.strip()
