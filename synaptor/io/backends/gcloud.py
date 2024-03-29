""" GCloud IO Functionality """

import os
import re
import glob
import subprocess

import cloudvolume  # Piggybacking on cloudvolume's secrets
from google.cloud import storage

from . import utils


REGEXP = re.compile("gs://")
CREDS_FN = cloudvolume.secrets.google_credentials


def pull_file(remote_path, alwayspull=False):
    bucket, key = parse_remote_path(remote_path)

    local_fname = os.path.basename(remote_path)

    if not alwayspull and os.path.isfile(local_fname):
        return local_fname

    blob = open_bucket(bucket).blob(key)

    blob.download_to_filename(local_fname)

    return local_fname


def pull_files(remote_paths, check=True,
               batching_limit=50000, batch_size=1000):

    if len(remote_paths) > batching_limit:
        return pull_files_in_batches(remote_paths, batch_size)
    else:
        subprocess.run(["gsutil", "-m", "-q", "cp", *remote_paths, "."],
                       check=check)
        return list(map(os.path.basename, remote_paths))


def pull_files_in_batches(paths, check=True, batch_size=1000):
    num_batches = len(paths) / batch_size + 1

    local_paths = list()
    for i in range(num_batches):
        batch_paths = paths[i*batch_size:(i+1)*batch_size]
        subprocess.run(["gsutil", "-m", "-q", "cp", *batch_paths, "."],
                       check=check)
        local_paths.extend(map(os.path.basename, batch_paths))

    return local_paths


def pull_directory(remote_dir, check=True):
    """ This will currently break if the remote dir has subdirectories """
    local_dirname = os.path.basename(remote_dir)
    subprocess.run(["gsutil", "-m", "-q", "cp", "-r", remote_dir, "."],
                   check=check)

    local_fnames = glob.glob(f"{local_dirname}/*")

    return local_fnames


def send_file(local_name, remote_path):
    bucket, key = parse_remote_path(remote_path)

    blob = open_bucket(bucket).blob(key)

    blob.upload_from_filename(local_name)


def send_files(local_names, remote_dir, check=True):
    subprocess.run(["gsutil", "-q", "-m", "cp", *local_names, remote_dir],
                   check=check)


def send_directory(local_dir, remote_dir):
    bucket, key = parse_remote_path(remote_dir)

    # Sending directory to a subdirectory of remote dir
    key = os.path.join(key, os.path.basename(utils.check_no_slash(local_dir)))

    fnames = os.listdir(local_dir)
    remote_keys = [os.path.join(key, f) for f in fnames]

    active_bucket = open_bucket(bucket)

    for (f, key) in zip(fnames, remote_keys):
        blob = active_bucket.blob(key)
        blob.upload_from_filename(os.path.join(local_dir, f))


def parse_remote_path(remote_path):
    """ Wrapper around the utils function - checks for the right protocol """
    protocol, bucket, key = utils.parse_remote_path(remote_path)

    assert protocol == "gs:", "Mismatched protocol (expected Google Storage)"

    return bucket, key


def open_bucket(bucket):
    """ Opens a bucket """
    project, creds = CREDS_FN(bucket)
    client = storage.Client(project=project,
                            credentials=creds)

    return client.get_bucket(bucket)
