#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import filter
from builtins import range
from future import standard_library
standard_library.install_aliases()


__doc__ = """
Utilities for Cloud Backends

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


def parse_remote_path(remote_path):
    """ 
    Parses a remote pathname into its protocol, bucket, and key. These
    are fields required by the current cloud backends
    """
    #Simple, but should work
    fields = remote_path.split("/")

    assert len(fields) > 3, "Improper remote path (needs more fields)"

    protocol = fields[0]
    assert fields[1] == ""
    bucket   = fields[2]
    key      = "/".join(fields[3:])

    return protocol, bucket, key


def check_slash(path):
    """ Make sure that a slash terminates the string """
    if path[-1] == "/":
        return path
    else:
        return path + "/"


def check_no_slash(path):
    """ Make sure that a slash doesn't terminate the string """
    if path[-1] == "/":
        return path[:-1]
    else:
        return path
