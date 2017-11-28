#!/usr/bin/env python3


import os, re, random, string


from . import local
from . import aws
from . import gcloud


random.seed(9999) #for testing
GCLOUD_REGEXP = re.compile("gs://")
AWS_REGEXP    = re.compile("s3://")


def chunk_tag(chunk_bounds):
    """ Creates a filename tag for a 3d dataset chunk """
    return "{0}_{1}_{2}-{3}_{4}_{5}".format(*chunk_bounds.min(),*chunk_bounds.max())


def make_local_h5(pathname):
    if is_remote_pathname(pathname):
        fname = temp_pathname(pathname)
    else:
        fname = pathname

    return local.open_h5(fname)
    

def temp_pathname(pathname):
    no_prefix = GCLOUD_REGEXP.sub("", AWS_REGEXP.sub("", pathname))
    tag = random_tag()

    return tag + "_" + os.path.basename(no_prefix)


def random_tag(k=8):
    return "".join(random.choice(string.ascii_uppercase +
                                  string.digits)
                   for _ in range(k))


def is_remote_pathname(pathname):
    return GCLOUD_REGEXP.match(pathname) or AWS_REGEXP.match(pathname)


def save_dframe(dframe, pathname):
    """
    Saves a dataframe to a pathname - pathname can specify
    remote storage in Google Cloud or AWS S3
    """

    if is_remote_pathname(pathname):
        local_fname = temp_pathname(pathname)
    else:
        local_fname = pathname

    local.save_dframe(dframe, local_fname)

    if is_remote_pathname(pathname):
        send_local_file(local_fname, pathname)


def send_local_file(local_name, pathname):
    """
    Sends a local file to remote storage (GCloud or AWS S3)
    """

    if   GCLOUD_REGEXP.match(pathname):
        gcloud.send_local_file(local_name, pathname)
    elif AWS_REGEXP.match(pathname):
        aws.send_local_file(local_name, pathname)
    else:
        raise(Exception("Pathname doesn't match remote pattern"))
