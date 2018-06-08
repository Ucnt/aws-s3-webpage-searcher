# aws-s3-webpage-searcher

Scans a webpage or set of webpages for content loaded from S3 buckets and checks if the bucket is write-enabled or does not exist.


## Purpose 
Detect loading of webpage content from insecure S3 buckets or ones that no longer exist.

Explanation of impact is here: https://www.mattsvensson.com/nerdings/2018/5/30/compromising-aws-s3-hosetd-websites-at-scale


## Requirements
- Setup an AWS Account (https://portal.aws.amazon.com/billing/signup)
- Create an AWS user (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)
- Create access keys and secret keys (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
- Install the AWS CLI (https://docs.aws.amazon.com/cli/latest/userguide/installing.html)
- Add your access keys to the AWS CLI
- Python modules: requests


## Usage
- Search a specific webpage

python search_webpages.py -w mydomain.com

- Search a specific webpage with verbose output (e.g. attempted buckets, etc)

python search_webpages.py -pv -w mydomain.com

- Search a specific webpage and up to 20 of its subpages (e.g. links and links to links on that domain)

python search_webpages.py -w mydomain.com --max_subpages 20

- Search a list of webpages and up to 20 of their subpages (e.g. links and links to links on that domain)

python search_webpages.py -wl webpage_list.txt --max_subpages 20


## Output Example
- An example, like below, will be printed each time a vuln is found.
- At the end of the search, all vulns found will be printed (to consolidate findings).

{
    "Vuln" : "Writable S3 Bucket", 
    "Website" : "example.com",
    "Example URL" : "example.com/subpage/othersubpage,
    "Bucket" : "mybucket",
}


## Notes
- Edit the module/testupload.txt file to be personalized. It has my info in it for now :)
- This is tested on Ubuntu and Python 3.6.5
- "amazonaws.com" will sometimes be found in the source code but no bucket found.  Manual analyisis is then required.  Sometimes it's bad regex.  Sometimes it's not actually loading content.
- There may be a few FPs, e.g. on non-existent buckets if "-us-east-1" is in the bucket name but it's removed.
- You might (?) need to ensure all the __init__.py files are +x'd 
