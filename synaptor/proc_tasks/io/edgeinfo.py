#!/usr/bin/env python3
__doc__ = """
Edge info DataFrame IO for processing tasks
"""

import os

from ... import io


EDGES_DIRNAME = "chunk_edges"
EDGES_FMTSTR = "chunk_edges_{tag}.df"
MERGED_EDGES_FNAME = "cons_edges.df"
FINAL_EDGES_FNAME = "final_edges.df"
FINAL_FULL_DF_FNAME = "final.df"
ANCHOR_DIRNAME = "anchors"
ANCHOR_FMTSTR = "anchors_{tag}.df"


def read_chunk_edge_info(fname):
    """Reads an edge info file for a single chunk by filename"""
    return io.read_dframe(fname)


def write_chunk_edge_info(edges_dframe, chunk_bounds, proc_dir_path):
    """Writes a dataframe of edge info to the processing directory"""
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    edges_df_fname = os.path.join(proc_dir_path, EDGES_DIRNAME,
                                 EDGES_FMTSTR.format(tag=chunk_tag))

    io.write_dframe(edges_dframe, edges_df_fname)


def read_all_edge_infos(proc_dir_path):
    """
    Reads all edge info files within the proper subdirectory within
    the processing directory. Currently assumes that NOTHING else is in the
    edge info subdirectory
    """
    edges_dir = os.path.join(proc_dir_path, EDGES_DIRNAME)
    fnames = io.pull_directory(edges_dir)
    assert len(fnames) > 0, "No filenames returned"

    starts  = [ io.bbox_from_fname(f).min() for f in fnames ]
    dframes = [ read_chunk_edge_info(f) for f in fnames ]

    info_arr = io.utils.make_info_arr({s : df for (s,df) in zip(starts, dframes)})
    return info_arr, os.path.dirname(fnames[0])


def read_merged_edge_info(df, proc_dir_path):
    """Reads the merged edge info dataframe from a processing directory"""
    return io.utils.read_dframe(proc_dir_path, MERGED_EDGES_FNAME)


def write_merged_edge_info(edge_df, proc_dir_path):
    """Writes a merged edge info dataframe to a processing directory"""
    edge_df_fname = os.path.join(proc_dir_path, MERGED_EDGES_FNAME)
    io.write_dframe(edge_df, edge_df_fname)


def write_final_edge_info(edge_df, proc_dir_path):
    """
    Writes a merged edge info dataframe (with duplicates removed)
    to a processing directory
    """
    edge_df_fname = os.path.join(proc_dir_path, FINAL_EDGES_FNAME)
    io.write_dframe(edge_df, edge_df_fname)


def read_full_info(proc_dir_path):
    """
    Reads the info dataframe with clefts and edges combined
    from a processing directory
    """
    return io.read_dframe(proc_dir_path, FINAL_FULL_DF_FNAME)


def write_full_info(df, proc_dir_path):
    """
    Writes the info dataframe with clefts and edges combined
    to a processing directory
    """
    io.write_dframe(df, proc_dir_path, FINAL_FULL_DF_FNAME)


def write_chunk_anchor(anchor_dframe, chunk_bounds, proc_dir_path):
    """Writes a dataframe of anchor points to the processing directory"""
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    anchor_df_fname = os.path.join(proc_dir_path, ANCHOR_DIRNAME,
                                 ANCHOR_FMTSTR.format(tag=chunk_tag))

    io.write_dframe(anchor_dframe, anchor_df_fname)
