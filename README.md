# html-versionator

Scans a webpage or set of webpages for content loaded from S3 buckets and checks if the bucket is write-enabled or does not exist.

## Purpose 
Detect loading of webpage content from insecure S3 buckets or ones that no longer exist.

Explanation of impact is here: https://www.mattsvensson.com/nerdings/2018/5/30/compromising-aws-s3-hosetd-websites-at-scale


## Usage
- Search a specific webpage
python search_webpages.py -w mydomain.com

- Search a specific webpage and up to 20 of its subpages (e.g. links and links to links on that domain)
python search_webpages.py -w mydomain.com --max_subpages 20

- Search a list of webpages and up to 20 of their subpages (e.g. links and links to links on that domain)
python search_webpages.py -wl webpage_list.txt --max_subpages 20


