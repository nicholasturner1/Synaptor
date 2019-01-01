#!/usr/bin/env python3
__doc__ = """
Cleft info DataFrame IO for processing tasks
"""

import os

from sqlalchemy import select, and_
from sqlalchemy.sql.expression import true, false

from ... import io
from . import initdb


# FILE STORAGE CONVENTIONS
# Cleft info files for a single chunk
CLEFT_INFO_DIRNAME = "cleft_infos"
CLEFT_INFO_FMTSTR = "cleft_info_{tag}.df"
# Cleft info files merged across chunks
MERGED_CLEFT_FNAME = "merged_cleft_info.df"

# This needs to match columns within `initdb.py`
CLEFT_INFO_COLUMNS = ["cleft_segid", "size",
                      "centroid_x", "centroid_y", "centroid_z",
                      "bbox_bx", "bbox_by", "bbox_bz",
                      "bbox_ex", "bbox_ey", "bbox_ez"]
CHUNK_START_COLUMNS = ["id", "begin_x", "begin_y", "begin_z"]
NULL_CHUNK_ID = initdb.NULL_CHUNK_ID


def chunk_info_fname(proc_url, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = CLEFT_INFO_FMTSTR.format(tag=chunk_tag)
    return os.path.join(proc_url, CLEFT_INFO_DIRNAME, basename)


def read_chunk_cleft_info(proc_url, chunk_bounds=None, chunk_id=None):
    """ Reads cleft info for a single chunk """
    if io.is_db_url(proc_url):
        assert chunk_id is not None, "bounds reading not yet impl for dbs"
        metadata = io.open_db_metadata(proc_url)

        clefts = metadata.tables["clefts"]
        columns = list(clefts.c[name] for name in CLEFT_INFO_COLUMNS)
        statement = select(columns).where(clefts.c.chunk_id == chunk_id)
        return io.read_db_dframe(proc_url, statement, index_col="cleft_segid")

    else:
        assert chunk_bounds is not None, "chunk id reading not impl for files"
        return io.read_dframe(chunk_info_fname(proc_url, chunk_bounds))


def write_chunk_cleft_info(dframe, proc_url, chunk_bounds=None, chunk_id=None):
    """ Writes cleft info to the processing URL """
    if io.is_db_url(proc_url):
        assert chunk_id is not None, "bounds reading not yet impl for dbs"
        dframe["chunk_id"] = chunk_id
        dframe["merged"] = False
        dframe["final"] = False
        io.write_db_dframe(dframe, proc_url, "clefts")

    else:
        assert chunk_bounds is not None, "chunk id reading not impl for files"
        io.write_dframe(dframe, chunk_info_fname(proc_url, chunk_bounds))


def read_all_chunk_cleft_infos(proc_url):
    """
    Reads all cleft info for chunks within storage.
    Currently assumes that NOTHING else is in the
    cleft info subdirectory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)
        clefts, chunks = metadata.tables["clefts"], metadata.tables["chunks"]

        cleftcols = list(clefts.c[name] for name in CLEFT_INFO_COLUMNS)
        cleftstmt = select(cleftcols).where(and_(clefts.c.merged == false(),
                                                 clefts.c.final == false()))

        chunkcols = list(chunks.c[name] for name in CHUNK_START_COLUMNS)
        chunkstmt = select(chunkcols)

        results = io.read_db_dframes(proc_url, (cleftstmt, chunkstmt),
                                     index_cols=("cleft_segid", "id"))
        cleft_df, chunk_df = results[0], results[1]

        chunk_id_to_df = dict(iter(cleft_df.groupby("cleft_segid")))
        chunk_lookup = dict(zip(chunk_df.index, zip(chunk_df.begin_x,
                                                    chunk_df.begin_y,
                                                    chunk_df.begin_z)))

        dframe_lookup = {chunk_lookup[i]: df
                         for (i, df) in chunk_id_to_df.items()}

    else:
        cleft_info_dir = os.path.join(proc_url, CLEFT_INFO_DIRNAME)
        fnames = io.pull_directory(cleft_info_dir)
        assert len(fnames) > 0, "No filenames returned"

        starts = [io.bbox_from_fname(f).min() for f in fnames]
        dframes = [io.read_dframe(f) for f in fnames]

        dframe_lookup = {s: df for (s, df) in zip(starts, dframes)}

    return io.utils.make_info_arr(dframe_lookup)


def read_merged_cleft_info(proc_url):
    """ Reads the merged cleft info dataframe from storage. """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        clefts = metadata.tables["clefts"]
        columns = list(clefts.c[name] for name in CLEFT_INFO_COLUMNS)
        statement = select(columns).where(and_(clefts.c.merged == true(),
                                               clefts.c.final == false()))
        return io.read_db_dframe(proc_url, statement, index_col="cleft_segid")

    else:
        return io.read_dframe(proc_url, MERGED_CLEFT_FNAME)


def write_merged_cleft_info(dframe, proc_url):
    """Writes a merged cleft info dataframe to storage. """
    if io.is_db_url(proc_url):
        dframe["chunk_id"] = NULL_CHUNK_ID
        dframe["merged"] = True
        dframe["final"] = False
        io.write_db_dframe(dframe, proc_url, "clefts", index=False)

    else:
        io.write_dframe(dframe, proc_url, MERGED_CLEFT_FNAME)
