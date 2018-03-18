#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import zip
from future import standard_library
standard_library.install_aliases()


__doc__ = """
AWS IO Functionality

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


import os, re

import cloudvolume #Piggybacking on cloudvolume's secrets
import boto3

from . import utils


REGEXP = re.compile("s3://")
CREDS = cloudvolume.secrets.aws_credentials


def pull_file(remote_path):
    bucket, key = parse_remote_path(remote_path)

    local_fname = os.path.basename(remote_path)

    client = open_client()

    client.download_file(bucket, key, local_fname)


def pull_directory(remote_dir):
    """ This will currently break if the remote dir has subdirectories """
    bucket, key = parse_remote_path(remote_dir)

    client = open_client()

    remote_keys  = keys_under_prefix(client, bucket, key)
    local_dir    = os.path.basename(utils.check_no_slash(key))
    local_fnames = [os.path.join(local_dir, os.path.basename(k))
                    for k in remote_keys]

    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    for (f,k) in zip(local_fnames, remote_keys):
        client.download_file(bucket, k, f)

    return local_fnames


def send_file(local_name, remote_path):
    bucket, key = parse_remote_path(remote_path)

    client = open_client()

    client.upload_file(local_name, bucket, key)


def send_directory(local_dir, remote_dir):
    bucket, key = parse_remote_path(remote_dir)

    #Sending directory to a subdirectory of remote dir
    key = os.path.join(key, os.path.basename(utils.check_no_slash(local_dir)))

    fnames = os.listdir(local_dir)
    remote_keys = [os.path.join(key, f) for f in fnames]

    client = open_client()

    for (f,key) in zip(fnames, remote_keys):
        client.upload_file(os.path.join(local_dir, f), bucket, key)


def keys_under_prefix(client, bucket, key):

    response = client.list_objects(Bucket=bucket,
                                   Prefix=utils.check_slash(key))

    return [ obj["Key"] for obj in response["Contents"] ]


def parse_remote_path(remote_path):
    """ Wrapper around the utils function - checks for the right protocol """
    protocol, bucket, key = utils.parse_remote_path(remote_path)

    assert protocol == "s3:", "Mismatched protocol (expected AWS S3)"

    return bucket, key


def open_client():
    return boto3.client("s3",
                        aws_access_key_id=CREDS["AWS_ACCESS_KEY_ID"],
                        aws_secret_access_key=CREDS["AWS_SECRET_ACCESS_KEY"],
                        region_name="us-east-1")
