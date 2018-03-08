#!/usr/bin/env python3
__doc__ = """
Neural Network Model IO for processing tasks
"""

import os

from ... import io


NETWORK_DIRNAME = "network"
NETWORK_FNAME   = "net.py"
CHKPT_FNAME     = "net.chkpt"


def read_network_from_proc(proc_dir_path):

    model_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, NETWORK_FNAME)
    chkpt_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, CHKPT_FNAME)

    return io.read_network(model_fname, chkpt_fname)


def write_network_to_proc(net_fname, chkpt_fname, proc_dir_path):

    dest_net_fname   = os.path.join(proc_dir_path, NETWORK_DIRNAME, NETWORK_FNAME)
    dest_chkpt_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, CHKPT_FNAME)

    io.send_local_file(net_fname,   dest_net_fname)
    io.send_local_file(chkpt_fname,  dest_chkpt_fname)
