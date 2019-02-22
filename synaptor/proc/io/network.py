""" PyTorch Neural Network Model IO for processing tasks """


import os

from ... import io
from . import filenames as fn


def read_network_from_proc(proc_dir_path):

    model_fname = os.path.join(proc_dir_path,
                               fn.network_dirname, fn.network_fname)
    chkpt_fname = os.path.join(proc_dir_path,
                               fn.network_dirname, fn.network_chkpt)

    return io.read_network(model_fname, chkpt_fname)


def write_network_to_proc(net_fname, chkpt_fname, proc_dir_path):

    dest_net_fname = os.path.join(proc_dir_path,
                                  fn.network_dirname, fn.network_fname)
    dest_chkpt_fname = os.path.join(proc_dir_path,
                                    fn.network_dirname, fn.network_chkpt)

    io.send_file(net_fname, dest_net_fname)
    io.send_file(chkpt_fname, dest_chkpt_fname)
