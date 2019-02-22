""" Overlap Matrix IO for processing tasks """


import os

import pandas as pd
import scipy.sparse as sp
from sqlalchemy import select

from ... import io
from .. import colnames as cn
from . import filenames as fn


OVERLAP_COLUMNS = [cn.rows, cn.cols, cn.vals]
CHUNK_START_COLUMNS = [cn.chunk_tag, cn.chunk_bx, cn.chunk_by, cn.chunk_bz]


def read_chunk_overlap_mat(fname):
    """ Reads an overlap matrix for a single chunk by filename. """
    df = io.read_dframe(fname)

    return overlap_mat_from_dframe(df)


def overlap_mat_from_dframe(df):
    """
    Converts a dataframe specifying a sparse matrix to a scipy sparse matrix
    """
    rs = list(df[cn.rows])
    cs = list(df[cn.cols])
    vs = list(df[cn.vals])

    return sp.coo_matrix((vs, (rs, cs)))


def write_chunk_overlap_mat(overlap_mat, chunk_bounds, proc_url):
    """Writes an overlap matrix for a chunk to a processing directory"""
    chunk_tag = io.fname_chunk_tag(chunk_bounds)

    rs, cs, vs = sp.find(overlap_mat)
    df = pd.DataFrame(dict(rows=rs, cols=cs, vals=vs))

    if io.is_db_url(proc_url):
        df[cn.chunk_tag] = chunk_tag
        io.write_db_dframe(df, proc_url, "chunk_overlaps")

    else:
        mat_fname = os.path.join(proc_url, fn.overlaps_dirname,
                                 fn.overlaps_fmtstr.format(tag=chunk_tag))
        io.write_dframe(df, mat_fname)


def read_all_overlap_mats(proc_url):
    """
    Reads all overlap matrix files within the proper subdirectory
    within the processing directory. Currently assumes that
    NOTHING else is in the overlap matrix subdirectory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)
        overlaps = metadata.tables["chunk_overlaps"]
        chunks = metadata.tables["chunks"]

        overlapcols = list(overlaps.c[name] for name in OVERLAP_COLUMNS)
        overlapcols.append(overlaps.c[cn.chunk_tag])
        overlapstmt = select(overlapcols)

        chunkcols = list(chunks.c[name] for name in CHUNK_START_COLUMNS)
        chunkstmt = select(chunkcols)

        results = io.read_db_dframes(proc_url, (overlapstmt, chunkstmt),
                                     index_cols=("id", "id"))

        overlap_df, chunk_df = results[0], results[1]

        chunk_id_to_df = dict(iter(overlap_df.groupby(cn.chunk_tag)))
        chunk_lookup = dict(zip(chunk_df[cn.chunk_tag],
                                list(zip(chunk_df[cn.chunk_bx],
                                         chunk_df[cn.chunk_by],
                                         chunk_df[cn.chunk_bz]))))

        dframe_lookup = {chunk_lookup[i]: overlap_mat_from_dframe(df)
                         for (i, df) in chunk_id_to_df.items()}

        # ensuring that each chunk is represented
        represented_keys = set(dframe_lookup.keys())
        for chunk_begin in chunk_lookup.values():
            if chunk_begin not in represented_keys:
                empty_mat = overlap_mat_from_dframe(make_empty_df())
                dframe_lookup[chunk_begin] = empty_mat

    else:
        overlap_mat_dir = os.path.join(proc_url, fn.overlaps_dirname)
        fnames = io.pull_directory(overlap_mat_dir)
        assert len(fnames) > 0, "No filenames returned"

        starts = [io.bbox_from_fname(f).min() for f in fnames]
        mats = [read_chunk_overlap_mat(f) for f in fnames]

        dframe_lookup = {s: mat for (s, mat) in zip(starts, mats)}

    return io.utils.make_info_arr(dframe_lookup)


def make_empty_df():
    """ Make an empty dataframe as a placeholder. """
    df = pd.DataFrame(data=None, dtype=int, columns=OVERLAP_COLUMNS)

    return df.set_index(cn.seg_id)


def read_max_overlaps(proc_url):
    """
    Reads the mapping from segment to base segment of maximal overlap
    from a processing directory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        overlaps = metadata.tables["max_overlaps"]
        columns = list(overlaps.c[name] for name in OVERLAP_COLUMNS)
        df = io.read_db_dframe(proc_url, select(columns), index=cn.rows)

    else:
        df = io.read_dframe(proc_url, fn.max_overlaps_fname)

    return dict(zip(df.index, df[cn.cols]))


def write_max_overlaps(max_overlaps, proc_url):
    """
    Writes a mapping from segment to base segment of maximal overlap
    to a processing directory

    UNFINISHED - will revisit after testing other tasks
    """
    rs, cs, vs = sp.find(max_overlaps)
    df = pd.DataFrame(pd.Series(max_overlaps), columns=["max_overlap"])
    if io.is_db_url(proc_url):
        io.write_db_dframe(df, proc_url, "max_overlaps")

    else:
        io.write_dframe(df, proc_url, fn.max_overlaps_fname)
