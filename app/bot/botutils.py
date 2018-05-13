# -*- coding: utf-8 -*-
"""bot helper functions and classes."""


import json
import os
import sys
import urllib.parse
import mimetypes
from collections import namedtuple


__author__ = "Freddy Bello"
__author_email__ = "frbello@cisco.com"
__copyright__ = "Copyright (c) 2016-2018 Cisco and/or its affiliates."
__license__ = "MIT"


EncodableFile = namedtuple('EncodableFile', ['file_name', 'file_object', 'content_type'])

def is_web_url(string):
    """Check to see if string is an validly-formatted web url."""
    #assert isinstance(string, basestring)
    parsed_url = urllib.parse.urlparse(string)
    return ((parsed_url.scheme.lower() == 'http' or
             parsed_url.scheme.lower() == 'https') and
            parsed_url.netloc)

def is_local_file(string):
    """Check to see if string is a valid local file path."""
    #assert isinstance(string, basestring)
    return os.path.isfile(string)


def open_local_file(file_path):
    """Open the file and return an EncodableFile tuple."""
    #assert isinstance(file_path, basestring)
    #assert is_local_file(file_path)
    file_name = os.path.basename(file_path)
    file_object = open(file_path, 'rb')
    content_type = mimetypes.guess_type(file_name)[0] or 'text/plain'
    return EncodableFile(file_name=file_name,
                         file_object=file_object,
                         content_type=content_type)


