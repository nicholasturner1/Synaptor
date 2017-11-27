#!/usr/bin/env python3

import os
import h5py


def save_dframe(dframe, pathname):
    """ Simple for now """
    dframe.to_csv(pathname, index_label="psd_segid")


def read_dframe(pathname):
    return pd.read_csv(pathname, index_col=0)


def read_h5(fname, dset_name="/main"):

    assert os.path.isfile(fname)
    f = h5py.File(fname)
    d = f[dset_name].value
    f.close()
    return d


def write_h5(data, fname, dset_name="/main", chunk_size=None):

    if os.path.exists(fname):
        os.remove(fname)

    f = h5py.File(fname)

    if chunk_size is None:
        f.create_dataset(dset_name, data=data)
    else:
        f.create_dataset(dset_name, data=data, chunks=chunk_size,
                         compression="gzip", compression_opts=4)

    f.close()
