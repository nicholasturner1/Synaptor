#!/usr/bin/env python3

import imp, os
import torch


from .. import io


NETWORK_DIRNAME = "network"
NETWORK_FNAME   = "net.py"
CHKPT_FNAME     = "net.chkpt"

def read_network(proc_dir_path):

    model_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, NETWORK_FNAME)
    chkpt_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, CHKPT_FNAME)

    local_model = io.pull_file(model_fname)
    local_chkpt = io.pull_file(chkpt_fname)

    model = imp.load_source("Model",model_fname).InstantiatedModel
    model.load_state_dict(torch.load(local_chkpt))

    return model


def write_chunk_edges():
    pass


def read_all_edges():
    pass


def read_chunk_edges():
    pass
