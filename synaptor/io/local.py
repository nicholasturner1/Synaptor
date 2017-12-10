#!/usr/bin/env python3

import os, glob, shutil
import h5py
import pandas as pd



def write_dframe(dframe, path):
    """ Simple for now """
    dframe.to_csv(path, index_label="psd_segid")


def read_dframe(path):
    """ Simple for now """
    return pd.read_csv(path, index_col=0)


def open_h5(fname):
    f = h5py.File(fname)
    return f


def read_h5(fname, dset_name="/main"):
    assert os.path.isfile(fname)
    with h5py.File(fname) as f:
        return f[dset_name].value


def write_h5(data, fname, dset_name="/main", chunk_size=None):

    if os.path.exists(fname):
        os.remove(fname)

    with h5py.File(fname) as f:

        if chunk_size is None:
            f.create_dataset(dset_name, data=data)
        else:
            f.create_dataset(dset_name, data=data, chunks=chunk_size,
                             compression="gzip", compression_opts=4)

def send_local_file(src, dst):
    shutil.copyfile(src, dst)


def send_local_dir(dirname, dst):
    full_dst = os.path.join(dst,dirname)
    if os.path.exists(full_dst):
        os.rmdir(full_dst)
    shutil.move(dirname, dst)


def pull_file(fname):
    assert os.path.exists
    return fname


def pull_all_files(dirname):
    return glob.glob(os.path.join(dirname, "*"))
