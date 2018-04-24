#!/usr/bin/env python3
__doc__ = """
Overlap Matrix IO for processing tasks
"""

import os

import pandas as pd
import scipy.sparse as sp

from ... import io

OVERLAPS_DIRNAME = "chunk_overlaps"
OVERLAPS_FMTSTR = "chunk_overlap_{tag}.df"
MAX_OVERLAPS_FNAME = "max_overlaps.df"


def read_chunk_overlap_mat(fname):
    """Reads an overlap matrix for a single chunk by filename"""
    df = io.read_dframe(fname)

    rs = list(df.rows)
    cs = list(df.cols)
    vs = list(df.vals)

    return sp.coo_matrix((vs,(rs,cs)))


def write_chunk_overlap_mat(overlap_mat, chunk_bounds, proc_dir_path):
    """Writes an overlap matrix for a chunk to a processing directory"""
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    mat_fname = os.path.join(proc_dir_path, OVERLAPS_DIRNAME,
                             OVERLAPS_FMTSTR.format(tag=chunk_tag))

    rs, cs, vs = sp.find(overlap_mat)
    df = pd.DataFrame(dict(rows=rs, cols=cs, vals=vs))

    io.write_dframe(df, mat_fname)


def read_all_overlap_mats(proc_dir_path):
    """
    Reads all overlap matrix files within the proper subdirectory 
    within the processing directory. Currently assumes that 
    NOTHING else is in the overlap matrix subdirectory
    """
    overlap_mat_dir = os.path.join(proc_dir_path, OVERLAPS_DIRNAME)
    fnames = io.pull_directory(overlap_mat_dir)
    assert len(fnames) > 0, "No filenames returned"

    starts = [io.bbox_from_fname(f).min() for f in fnames]
    mats = [read_chunk_overlap_mat(f) for f in fnames]

    info_arr = io.utils.make_info_arr({s : mat
                                       for (s,mat) in zip(starts, mats)})
    return info_arr, os.path.dirname(fnames[0])


def read_max_overlaps(proc_dir_path):
    """
    Reads the mapping from segment to base segment of maximal overlap 
    from a processing directory
    """
    df = io.read_dframe(proc_dir_path, MAX_OVERLAPS_FNAME)
    return dict(zip(df.index, df.max_overlap))


def write_max_overlaps(max_overlaps, proc_dir_path):
    """
    Writes a mapping from segment to base segment of maximal overlap
    to a processing directory
    """
    df = pd.DataFrame(pd.Series(max_overlaps), columns=["max_overlap"])
    io.write_dframe(df, proc_dir_path, MAX_OVERLAPS_FNAME)

