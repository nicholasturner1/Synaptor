""" AWS IO Functionality """

import os
import re
import subprocess

import cloudvolume  # Piggybacking on cloudvolume's secrets
import boto3

from . import utils


REGEXP = re.compile("s3://")
CREDS_FN = cloudvolume.secrets.aws_credentials


def pull_file(remote_path):
    bucket, key = parse_remote_path(remote_path)

    local_fname = os.path.basename(remote_path)

    client = open_client(bucket)

    client.download_file(bucket, key, local_fname)


def pull_files(remote_paths, batching_limit=50000, batch_size=1000):

    if len(remote_paths) > batching_limit:
        return pull_files_in_batches(remote_paths, batch_size)
    else:
        subprocess.call(["gsutil", "-m", "-q", "cp", *remote_paths, "."])
        return list(map(os.path.basename, remote_paths))


def pull_files_in_batches(paths, batch_size=1000):
    num_batches = len(paths) / batch_size + 1

    local_paths = list()
    for i in range(num_batches):
        batch_paths = paths[i*batch_size:(i+1)*batch_size]
        subprocess.call(["gsutil", "-m", "-q", "cp", *batch_paths, "."])
        local_paths.extend(map(os.path.basename, batch_paths))

    return local_paths


def pull_directory(remote_dir):
    """ This will currently break if the remote dir has subdirectories """
    bucket, key = parse_remote_path(remote_dir)

    client = open_client(bucket)

    remote_keys = keys_under_prefix(client, bucket, key)
    local_dir = os.path.basename(utils.check_no_slash(key))
    local_fnames = [os.path.join(local_dir, os.path.basename(k))
                    for k in remote_keys]

    if not os.path.isdir(local_dir):
        os.makedirs(local_dir)

    for (f, k) in zip(local_fnames, remote_keys):
        client.download_file(bucket, k, f)

    return local_fnames


def send_file(local_name, remote_path):
    bucket, key = parse_remote_path(remote_path)

    client = open_client(bucket)

    client.upload_file(local_name, bucket, key)


def send_files(local_names, remote_dir):
    subprocess.call(["gsutil", "-q", "-m", "cp", *local_names, remote_dir])


def send_directory(local_dir, remote_dir):
    bucket, key = parse_remote_path(remote_dir)

    # Sending directory to a subdirectory of remote dir
    key = os.path.join(key, os.path.basename(utils.check_no_slash(local_dir)))

    fnames = os.listdir(local_dir)
    remote_keys = [os.path.join(key, f) for f in fnames]

    client = open_client(bucket)

    for (f, key) in zip(fnames, remote_keys):
        client.upload_file(os.path.join(local_dir, f), bucket, key)


def keys_under_prefix(client, bucket, key):

    response = client.list_objects(Bucket=bucket,
                                   Prefix=utils.check_slash(key))

    return [obj["Key"] for obj in response["Contents"]]


def parse_remote_path(remote_path):
    """ Wrapper around the utils function - checks for the right protocol """
    protocol, bucket, key = utils.parse_remote_path(remote_path)

    assert protocol == "s3:", "Mismatched protocol (expected AWS S3)"

    return bucket, key


def open_client(bucket):
    creds = CREDS_FN(bucket)
    return boto3.client("s3",
                        aws_access_key_id=creds["AWS_ACCESS_KEY_ID"],
                        aws_secret_access_key=creds["AWS_SECRET_ACCESS_KEY"],
                        region_name="us-east-1")
