#!/usr/bin/env python3
from lib.logger import *

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
            "HeaderParsingError",
            "MissingHeaderBodySeparatorDefect",
            "No connection adapters were found",
]


def check_error_ignore(e):
    try:
        for ok_error in ok_errors:
            if ok_error in e.replace("\n",""):
                break
        else:
            logger.log.warning(e)
    except:
        logger.log.warning(e)
