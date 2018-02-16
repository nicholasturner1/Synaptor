#!/usr/bin/env python3


#Pasteurize
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import map
from builtins import range
from future import standard_library
standard_library.install_aliases()

import os, re, random, string, glob
import warnings


from . import local
from . import aws
from . import gcloud

from .. import bbox


GCLOUD_REGEXP = re.compile("gs://")
AWS_REGEXP    = re.compile("s3://")

BBOX_REGEXP   = re.compile("[0-9]+_[0-9]+_[0-9]+-[0-9]+_[0-9]+_[0-9]+")


def chunk_tag(chunk_bounds):
    """ Creates a filename tag for a 3d dataset chunk """
    chunk_min = chunk_bounds.min()
    chunk_max = chunk_bounds.max()
    return "{0}_{1}_{2}-{3}_{4}_{5}".format(chunk_min[0], chunk_min[1],
                                            chunk_min[2],
                                            chunk_max[0], chunk_max[1],
                                            chunk_max[2])


def make_local_h5(path):

    if ".h5" not in path:
        path = path + ".h5"

    if is_remote_path(path):
        fname = temp_path(path)
    else:
        fname = path

    return local.open_h5(fname)


def temp_path(path):
    no_prefix = GCLOUD_REGEXP.sub("", AWS_REGEXP.sub("", path))
    tag = random_tag()

    return tag + "_" + os.path.basename(no_prefix)


def random_tag(k=8):
    return "".join(random.choice(string.ascii_uppercase +
                                  string.digits)
                   for _ in range(k))


def is_remote_path(path):
    return GCLOUD_REGEXP.match(path) or AWS_REGEXP.match(path)


def write_dframe(dframe, path):
    """
    Writes a dataframe to a path - path can specify
    remote storage in Google Cloud or AWS S3
    """

    if is_remote_path(path):
        local_fname = temp_path(path)
    else:
        local_fname = path

    local.write_dframe(dframe, local_fname)

    if is_remote_path(path):
        send_local_file(local_fname, path)


def read_dframe(path):
    """
    Reads a dataframe - path can specify remote
    storage in Google Cloud or AWS S3
    """

    if is_remote_path(path):
        local_fname = pull_file(path)
    else:
        local_fname = path

    return local.read_dframe(local_fname)


def send_local_file(local_name, path):
    """
    Sends a local file to remote storage (GCloud or AWS S3)
    """

    if   GCLOUD_REGEXP.match(path):
        gcloud.send_local_file(local_name, path)
    elif AWS_REGEXP.match(path):
        aws.send_local_file(local_name, path)
    else:
        warnings.warn("Pathname {} doesn't match remote pattern".format(path),
                      Warning)
        local.send_local_file(local_name, path)


def send_directory(local_dir, path):

    if   GCLOUD_REGEXP.match(path):
        gcloud.send_local_dir(local_dir, path)
    elif AWS_REGEXP.match(path):
        aws.send_local_dir(local_dir, path)
    else:
        warnings.warn("Pathname {} doesn't match remote pattern".format(path),
                      Warning)
        local.send_local_dir(local_dir, path)


def pull_file(path):

    if   GCLOUD_REGEXP.match(path):
        return gcloud.pull_file(path)
    elif AWS_REGEXP.match(path):
        return aws.pull_file(path)
    else: #local
        return local.pull_file(path)


def pull_all_files(dir_path):

    if   GCLOUD_REGEXP.match(dir_path):
        return gcloud.pull_all_files(dir_path)
    elif AWS_REGEXP.match(dir_path):
        return aws.pull_all_files(dir_path)
    else: #local
        return local.pull_all_files(dir_path)


def bbox_from_fname(path):

    match = BBOX_REGEXP.search(path)

    if match is None:
        raise(Exception("bbox not found in path"))

    beg_str, end_str = match.group(0).split("-")
    beg = tuple(map(int,beg_str.split("_")))
    end = tuple(map(int,end_str.split("_")))

    return bbox.BBox3d(beg, end)


def extract_sorted_bboxes(local_dir):

    fnames = local.pull_all_files(local_dir)
    bboxes = list(map(bbox_from_fname, fnames))

    return sorted(bboxes, key=lambda bb: bb.min())


def write_single_df(df, proc_dir_path, basename):

    full_fname = os.path.join(proc_dir_path, basename)

    write_dframe(df, full_fname)


def read_single_df(proc_dir_path, basename):

    full_fname = os.path.join(proc_dir_path, basename)
    fname = pull_file(full_fname)

    return read_dframe(fname)
