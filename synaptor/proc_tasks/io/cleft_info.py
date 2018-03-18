#!/usr/bin/env python3
__doc__ = """
Cleft info DataFrame IO for processing tasks
"""

import os, itertools

import pandas as pd
import numpy as np

from ... import io


CLEFT_INFO_DIRNAME = "cleft_infos"
CLEFT_INFO_FMTSTR = "cleft_info_{tag}.df"
MERGED_CLEFT_FNAME = "merged_cleft_info.df"


def read_chunk_cleft_info(fname):
    """Reads a cleft info file for a single chunk by filename"""
    return io.read_dframe(fname)


def write_chunk_cleft_info(dframe, chunk_bounds, proc_dir_path):
    """Writes a dataframe of chunk info to the processing directory"""
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    cleft_info_fname = os.path.join(proc_dir_path, CLEFT_INFO_DIRNAME,
                                    CLEFT_INFO_FMTSTR.format(tag=chunk_tag))

    io.write_dframe(dframe, cleft_info_fname)


def read_all_cleft_infos(proc_dir_path):
    """
    Reads all cleft info files within the proper subdirectory within
    the processing directory. Currently assumes that NOTHING else is in the
    cleft info subdirectory
    """
    cleft_info_dir = os.path.join(proc_dir_path, CLEFT_INFO_DIRNAME)
    fnames = io.pull_directory(cleft_info_dir)
    assert len(fnames) > 0, "No filenames returned"

    starts  = [ io.bbox_from_fname(f).min() for f in fnames ]
    dframes = [ read_chunk_cleft_info(f) for f in fnames ]

    info_arr = io.utils.make_info_arr({s : df
                                       for (s,df) in zip(starts, dframes)})
    return info_arr, os.path.dirname(fnames[0])


def read_merged_cleft_info(proc_dir_path):
    """Reads the merged cleft info dataframe from a processing directory"""
    full_fname = os.path.join(proc_dir_path, MERGED_CLEFT_FNAME)
    fname = io.pull_file(full_fname)

    return io.read_dframe(fname)


def write_merged_cleft_info(cons_cleft_info, proc_dir_path):
    """Writes a merged cleft info dataframe to a processing directory"""
    fname = os.path.join(proc_dir_path, MERGED_CLEFT_FNAME)
    io.write_dframe(cons_cleft_info, fname)
