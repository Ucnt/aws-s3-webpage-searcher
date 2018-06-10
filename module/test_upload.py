#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from lib.logger import *
from lib.constants import *
cur_dir = os.path.dirname(os.path.realpath(__file__))
import sys


def test_upload(website_base, domain_bucket):
    url, bucket_name = domain_bucket
    try:
        import subprocess
        command = "aws s3api put-object --bucket %s --key testupload.txt --body %s/testupload.txt --acl 'public-read-write' "% (bucket_name, cur_dir)
        p = subprocess.Popen(command,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                shell=True,)
        output, error = p.communicate()
        output = str(output).strip()
        #If there's no bucket....maybe it can be created!!!
        if "NoSuchBucket" in output:
            vuln = {
                        "Vuln" : "No Such Bucket", 
                        "Website" : website_base,
                        "Example URL" : url,
                        "Bucket" : bucket_name,
                   }
            logger.log.critical(vuln)
            return vuln
        elif "AccessDenied" in output or "AllAccessDisabled" in output:
            log_found_bucket(website_base, url, bucket_name)
        #You can write to the bucket!!
        elif '"ETag":' in output:
            log_writable_bucket(website_base, url, bucket_name)
            vuln = {
                        "Vuln" : "Writable S3 Bucket", 
                        "Website" : website_base,
                        "Example URL" : url,
                        "Bucket" : bucket_name,
                   }
            logger.log.critical(vuln)
            return vuln
        elif "Error parsing parameter" in output:
            logger.log.critical("Error: %s -> %s -> %s" % (url, bucket_name, output))
        else:
            if "aws: not found" in output:
                logger.log.critical("AWS CLI not installed.  Install and configure it w/ access and secret keys before continuing: https://docs.aws.amazon.com/cli/latest/userguide/installing.html")
                return
            elif "Unable to locate credentials" in output:
                logger.log.critical("AWS CLI credentials not configured.  Configure access and secret keys before continuing: https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html")
                return
            else:
                logger.log.warning("Error: %s -> %s -> %s" % (url, bucket_name, output))
    except Exception as e:
        if "aws: not found" in output:
            logger.log.critical("AWS CLI not installed.  Install and configure it w/ access and secret keys before continuing: https://docs.aws.amazon.com/cli/latest/userguide/installing.html")
            return
        elif "Unable to locate credentials" in output:
            logger.log.critical("AWS CLI credentials not configured.  Configure access and secret keys before continuing: https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html")
            return
        logger.log.critical("Error: %s-%s-%s: %s" % (website_base, url, bucket_name, e))


def log_found_bucket(website_base, url, bucket_name):
    f = open("%s/buckets_found.txt" % (log_dir), "a")
    f.write("%s -> %s -> %s\n" % (website_base, url, bucket_name))
    f.close()


def log_writable_bucket(website_base, url, bucket_name):
    f = open("%s/buckets_found_writable.txt" % (log_dir), "a")
    f.write("%s -> %s -> %s\n" % (website_base, url, bucket_name))
    f.close()
