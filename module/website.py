#!/usr/bin/env python3


class Website():
    def __init__ (self, url, num_subpages):
        self.url = url
        self.base_url = self.get_url_base(self.url)
        self.num_subpages = num_subpages
        self.subpages = []              #Pages found within the website and its subwebsites
        self.buckets_dict = {}          #Dict of bucket name arrays
        self.js_links_found = []


    def get_url_base(self, url):
        try:
            base_url = url.replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
            # if len(base_url.split(".")) > 2:
                # base_url_parts = base_url.split(".")
                # base_url = "%s.%s" % (base_url_parts[len(base_url_parts)-2], base_url_parts[len(base_url_parts)-1])
            return base_url.strip()
        except Exception as e:
            return url.strip()
