#!/usr/bin/env python3
import os
#from pycurl import FAILONERROR
import requests
import urllib
import urllib.parse as urlparse
from io import StringIO


def _set_x509_creds(handle):
    """
    Set the certificate if available
    """
    cert = None
    key = None
    if 'X509_USER_CERT' in os.environ:
        cert = os.environ['X509_USER_CERT']
    if 'X509_USER_KEY' in os.environ:
        key = os.environ['X509_USER_KEY']
    if cert and key:
        handle.cert = (cert, key)
    elif cert:
        handle.cert = cert


def _build_full_url(url, args):
    """
    Update url with the given query parameters that are passed by args
    """
    parsed = urlparse.urlparse(url)
    query = urlparse.parse_qs(parsed.query)
    for a in args:
        if args[a]:
            query[a] = args[a]
    query_str = urllib.parse.urlencode(query)
    new_url = (parsed.scheme, parsed.netloc, parsed.path, parsed.params, query_str, parsed.fragment)
    return urlparse.urlunparse(new_url)


def get_url(url, **kwargs):
    """
    Get the content from an URL, and expand the extra arguments as query parameters
    """
    handle = requests.Session()
    
    handle.verify = False
    _set_x509_creds(handle)
    
    buffer = StringIO()
    handle.stream = True
    #handle.setopt(pycurl.WRITEFUNCTION, buffer.write)
    
    #handle.setopt(pycurl.FOLLOWLOCATION, True)
    buffer = handle.get(url=_build_full_url(url, kwargs), allow_redirects=True)
    
    return buffer.content
