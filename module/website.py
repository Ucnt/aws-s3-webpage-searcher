#!/usr/bin/env python3


class Website():
    def __init__ (self, url, num_subpages):
        self.url = url
        self.num_subpages = num_subpages
        self.subpages = []              #Pages found within the website and its subwebsites
        self.buckets_dict = {}          #Dict of bucket name arrays
