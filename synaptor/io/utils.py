#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import filter
from builtins import range
from builtins import map
from future import standard_library
standard_library.install_aliases()
__doc__ = """
IO Utility Functions

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import os, re, random

import numpy as np

from .. import bbox
from . import backends as bck


AWS_REGEXP = bck.aws.REGEXP
GCLOUD_REGEXP = bck.gcloud.REGEXP
BBOX_REGEXP   = re.compile("[0-9]+_[0-9]+_[0-9]+-[0-9]+_[0-9]+_[0-9]+")


def fname_chunk_tag(chunk_bounds):
    """ Creates a filename tag for a 3d dataset chunk """
    chunk_min = chunk_bounds.min()
    chunk_max = chunk_bounds.max()
    return "{0}_{1}_{2}-{3}_{4}_{5}".format(chunk_min[0], chunk_min[1],
                                            chunk_min[2],
                                            chunk_max[0], chunk_max[1],
                                            chunk_max[2])


def temp_path(path):
    """ Creates a temporary filename for """
    no_prefix = GCLOUD_REGEXP.sub("", AWS_REGEXP.sub("", path))
    tag = random_tag()

    return tag + "_" + os.path.basename(no_prefix)


def random_tag(k=8):
    """ Returns a random tag for disambiguating filenames """
    return "".join(random.choice(string.ascii_uppercase +
                                  string.digits)
                   for _ in range(k))


def bbox_from_fname(path):
    """ Extracts the bounding box from a path """

    match = BBOX_REGEXP.search(path)

    if match is None:
        raise(Exception("bbox not found in path"))

    beg_str, end_str = match.group(0).split("-")
    beg = tuple(map(int,beg_str.split("_")))
    end = tuple(map(int,end_str.split("_")))

    return bbox.BBox3d(beg, end)


def extract_sorted_bboxes(local_dir):
    """
    Takes every file within a local directory, and returns a list
    of their bounding boxes sorted lexicographically
    """
    fnames = bck.local.pull_directory(local_dir)
    bboxes = list(map(bbox_from_fname, fnames))

    return sorted(bboxes, key=lambda bb: bb.min())


def make_info_arr(start_lookup):

    ordering = sorted(start_lookup.keys())
    dims     = infer_dims(ordering)

    ordered = [start_lookup[k] for k in ordering]

    arr = np.array([None for _ in range(len(ordered))]) #object arr
    for i in range(len(ordered)):
        arr[i] = ordered[i]

    return arr.reshape(dims)


def infer_dims(ordered_tups):

    #assuming the grid is full and complete, then
    # each dim's first index is repeated a number of times
    # equal to the product of the other dimension lengths.
    # => we can find the length in that dimension by dividing
    # the total # elems by this product

    num_tups = len(ordered_tups)
    first_x, first_y, first_z = ordered_tups[0]

    y_times_z = len(list(filter(lambda v: v[0] == first_x, ordered_tups)))
    x_times_z = len(list(filter(lambda v: v[1] == first_y, ordered_tups)))
    x_times_y = len(list(filter(lambda v: v[2] == first_z, ordered_tups)))

    assert num_tups % y_times_z == 0, "grid incomplete or redundant"
    assert num_tups % x_times_z == 0, "grid incomplete or redundant"
    assert num_tups % x_times_y == 0, "grid incomplete or redundant"

    x = num_tups  // y_times_z
    y = x_times_y // x
    z = x_times_z // x

    return (x,y,z)
