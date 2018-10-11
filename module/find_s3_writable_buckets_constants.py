#!/usr/bin/env python3
max_bucket_len = 60

#Headers for requests
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'}

#Bucket name content that indicates bad parsing
bad_bucket_name_contents = ("<", ">", "/", '"', "'", " ")

#Outside pages to now crawl
bad_outside_pages = [
                        "amazon",
                        "apple",
                        "facebook",
                        "github",
                        "google",
                        "instagram",
                        "linkedin",
                        "mailto:",
                        "pinterest",
                        "snapchat",
                        "tumblrl"
                        "twitter",
                        "youtube",
                    ]

#Bucket names that are either not writable and common or are otherwise invalid
junk_buckets = [
                    "*",
                    "blog",
                    "d3jlsadfjkuern",
                    "github-cloud",
                    "html",
                    "images",
                    "ki.js",
                    "new.cetrk.com",
                    "nwapi",
                    "private",
                    "public",
                    "twitter-badges",
                    "upload",
                    "uploads",
                    "widgets",
                    "lastsecondcoupon",
                    "downloads.mailchimp.com",
                ]


#Content in HTML that indicates that the pages is not valid
bad_html_conents = [
                    "403 forbidden",
                    "page not found"
                   ]
