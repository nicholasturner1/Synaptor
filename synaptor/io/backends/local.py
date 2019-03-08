""" Local Filesystem IO """

import os
import glob
import shutil
import itertools
import importlib
import types

import torch
import h5py
import pandas as pd


def pull_file(fname):
    """ Ensure that a file exists locally. """
    assert os.path.exists, f"File {fname} doesn't exist"
    return fname


def pull_files(fnames):
    assert all(os.path.exists(f) for f in fnames), "Some file doesn't exist"
    return fnames


def pull_directory(dirname):
    """ Find which files exist within a local directory. """
    return glob.glob(os.path.join(dirname, "*"))


def send_file(src, dst):
    """ Copy a file. """
    shutil.copyfile(src, dst)


def send_files(fnames, dst):
    for f in fnames:
        send_file(f, os.path.join(dst, f))


def send_directory(dirname, dst):
    """ Move a directory. """
    full_dst = os.path.join(dst, dirname)
    if os.path.abspath(full_dst) != os.path.abspath(dirname):
        shutil.move(dirname, dst)


def read_dframe(path):
    """ Read a dataframe from local disk. """
    assert os.path.isfile(path)
    return pd.read_csv(path, index_col=0)


def write_dframe(dframe, path, header=True, index=True):
    """ Write a dataframe to local disk. """
    dframe.to_csv(path, index=index, header=header)


def read_network(net_fname, chkpt_fname):
    """ Read a PyTorch model from disk. """
    model = load_source(net_fname).InstantiatedModel
    model.load_state_dict(torch.load(chkpt_fname))

    return model.cuda()


def write_network(net, path):
    """ Write a PyTorch model to disk. """
    torch.save(net, path)


def open_h5(fname):
    """ Open an hdf5 file, return the file object. """
    f = h5py.File(fname)
    return f


def read_h5(fname, dset_name="/main"):
    """ Read a specific dataset from an hdf5. """
    assert os.path.isfile(fname), "File {} doesn't exist".format(fname)
    with h5py.File(fname) as f:
        return f[dset_name].value


def write_h5(data, fname, dset_name="/main", chunk_size=None):
    """ Write a data array to a specific dataset within an hdf5. """
    if os.path.exists(fname):
        os.remove(fname)

    with h5py.File(fname) as f:

        if chunk_size is None:
            f.create_dataset(dset_name, data=data)
        else:
            f.create_dataset(dset_name, data=data, chunks=chunk_size,
                             compression="gzip", compression_opts=4)


def read_edge_csv(fname, delim=";", only_confident=False):
    """ Read the first three fields of a csv file. """
    edges = []
    with open(fname) as f:
        for l in f.readlines():
            fields = l.strip().split(delim)

            edgeid = int(fields[0])
            field1 = eval(fields[1])
            field2 = eval(fields[2])

            if isinstance(field1, int):
                field1 = [field1]
            if isinstance(field2, int):
                field2 = [field2]

            if only_confident and int(fields[3]) == 0:
                continue

            for (pre, post) in itertools.product(field1, field2):
                edges.append((edgeid, pre, post))

    return edges


def write_edge_csv(edges, fname, delim=";"):
    """
    Write a three-field csv file formatted as
    (cleft_id, presyn_segid, postsyn_segid).
    """
    with open(fname, "w+") as f:
        for (cleft_id, presyn_id, postsyn_id) in edges:
            content = delim.join(map(str, (cleft_id, presyn_id, postsyn_id)))
            f.write(f"{content}\n")


def load_source(fname, module_name="importedmodule"):
    """ Import a module from source """
    loader = importlib.machinery.SourceFileLoader(module_name, fname)
    mod = types.ModuleType(loader.name)
    loader.exec_module(mod)
    return mod
