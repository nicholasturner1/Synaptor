#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()


__doc__ = """
Local Filesystem IO

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


import os, glob, shutil
import importlib, types

import torch
import h5py
import pandas as pd


def pull_file(fname):
    assert os.path.exists, "File {} doesn't exist".format(fname)
    return fname


def pull_directory(dirname):
    return glob.glob(os.path.join(dirname, "*"))


def send_file(src, dst):
    shutil.copyfile(src, dst)


def send_directory(dirname, dst):
    full_dst = os.path.join(dst,dirname)
    if os.path.abspath(full_dst) != os.path.abspath(dirname):
        shutil.move(dirname, dst)
        

def read_dframe(path):
    """ Simple for now """
    return pd.read_csv(path, index_col=0)


def write_dframe(dframe, path):
    """ Simple for now """
    dframe.to_csv(path, index_label="psd_segid")


def read_network(net_fname, chkpt_fname):
    """ Reads a PyTorch model from disk """
    model = load_source(net_fname).InstantiatedModel
    model.load_state_dict(torch.load(chkpt_fname))

    return model


def write_network(net, path):
    """ Writes a PyTorch model to disk """
    torch.save(net, path)


def open_h5(fname):
    """ Opens an hdf5 file, returns the object """
    f = h5py.File(fname)
    return f


def read_h5(fname, dset_name="/main"):
    """ Reads a specific dataset from an hdf5 """
    assert os.path.isfile(fname), "File {} doesn't exist".format(fname)
    with h5py.File(fname) as f:
        return f[dset_name].value


def write_h5(data, fname, dset_name="/main", chunk_size=None):
    """ Writes a data array to a specific dataset within an hdf5 """
    if os.path.exists(fname):
        os.remove(fname)

    with h5py.File(fname) as f:

        if chunk_size is None:
            f.create_dataset(dset_name, data=data)
        else:
            f.create_dataset(dset_name, data=data, chunks=chunk_size,
                             compression="gzip", compression_opts=4)


def load_source(fname, module_name="something"):
    """ Imports a module from source """
    loader = importlib.machinery.SourceFileLoader(module_name,fname)
    mod = types.ModuleType(loader.name)
    loader.exec_module(mod)
    return mod
