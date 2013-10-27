# Skeletal functions provided by example in ices-0.4/conf/ices.py.dist
# 
# The ices0 Icecast source client can integrate with Python.
# it looks for an "ices" module that provides the ices_init(), 
# ices_shutdown(), ices_get_next(), and ices_get_metadata() functions.
# 
# This was kept very lightweight in the interest of keeping the 
# stream source always running.  Any code changes to the selector
# algorithm, logging configuration, or potential database schema 
# changes can all happen in a an http API that is visited only once
# per song change.  Theoretically, a hard-coded web server could
# be put up in its place to keep the feed going during maintenance.
#
# (c) 2013 Lars Lehtonen

import json
import requests
import time
from pprint import pprint

global metadata

execfile('/etc/tuubz/ices.conf')

class SelectorAPIFailure(Exception):
    pass

# Function called to initialize your python environment.
# Should return 1 if ok, and 0 if something went wrong.
def ices_init():
    time.sleep(STARTUP_SLEEP_SECONDS)
    return True


# Function called to shutdown your python enviroment.
# Return 1 if ok, 0 if something went wrong.
def ices_shutdown():
    return True


# Function called to get the next filename to stream.
# Should return a string.
def ices_get_next():
    global metadata
    metadata = ""
    try:
        r = requests.get(SELECTOR_URL)
        if r.status_code != 200:
            raise SelectorAPIFailure
        result = json.loads(r.content)
        pprint(result)
        metadata = result['metadata']
        filename = result['filename']
        return str(filename)
    except:
        print "hit exception"
        metadata = "FAIL"
        return EMERGENCY_RESPONSE_MP3

# This function, if defined, returns the string you'd like used
# as metadata (ie for title streaming) for the current song. You may
# return null to indicate that the file comment should be used.
def ices_get_metadata():
    return str(metadata)
