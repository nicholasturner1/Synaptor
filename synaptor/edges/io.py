#!/usr/bin/env python3

import imp, os
import torch


from .. import io


NETWORK_DIRNAME = "network"
NETWORK_FNAME   = "net.py"
CHKPT_FNAME     = "net.chkpt"

EDGES_DIRNAME = "chunk_edges"


def upload_network(net_fname, chkpt_fname, proc_dir_path):

    dest_net_fname   = os.path.join(proc_dir_path, NETWORK_DIRNAME, NETWORK_FNAME)
    dest_chkpt_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, CHKPT_FNAME)

    io.send_local_file(net_fname,   dest_net_fname)
    io.send_local_file(chkpt_fname,  dest_chkpt_fname)


def read_network(proc_dir_path):

    model_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, NETWORK_FNAME)
    chkpt_fname = os.path.join(proc_dir_path, NETWORK_DIRNAME, CHKPT_FNAME)

    local_model = io.pull_file(model_fname)
    local_chkpt = io.pull_file(chkpt_fname)

    model = imp.load_source("Model",local_model).InstantiatedModel
    model.load_state_dict(torch.load(local_chkpt))

    return model


def write_chunk_edges(edges_dframe, chunk_bounds, proc_dir_path):

    chunk_tag = io.chunk_tag(chunk_bounds)
    edges_df_fname = os.path.join(proc_dir_path, EDGES_DIRNAME,
                                 "chunk_edges_{tag}.df".format(tag=chunk_tag))

    io.write_dframe(edges_dframe, edges_df_fname)


def read_all_edges(proc_dir_path):

    edges_dir = os.path.join(proc_dir_path, EDGES_DIRNAME)
    fnames = io.pull_all_files(edges_dir)
    assert len(fnames) > 0, "No filenames returned"

    starts  = [ io.bbox_from_fname(f).min() for f in fnames ]
    dframes = [ read_chunk_edges(f) for f in fnames ]

    info_arr = io.utils.make_info_arr({s : df for (s,df) in zip(starts, dframes)})
    return info_arr, os.path.dirname(fnames[0])


def read_chunk_edges(fname):
    return io.read_dframe(fname)


def write_full_edge_list(edge_df, proc_dir_path):

    edge_df_fname = os.path.join(proc_dir_path, "all_edges.df")
    io.write_dframe(edge_df, edge_df_fname)
