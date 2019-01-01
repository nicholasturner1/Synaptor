#!/usr/bin/env python3
__doc__ = """
Edge info DataFrame IO for processing tasks
"""

import os

from sqlalchemy import select, and_
from sqlalchemy.sql.expression import true, false
import pandas as pd

from ... import io
from . import initdb


# FILE STORAGE CONVENTIONS
# Edge info files for a single chunk
EDGES_DIRNAME = "chunk_edges"
EDGES_FMTSTR = "chunk_edges_{tag}.df"
# Edge info files merged across chunks
MERGED_EDGES_FNAME = "merged_edges.df"
# w/ duplicates removed
FINAL_EDGES_FNAME = "final_edges.df"
# merged with cleft info
FINAL_FULL_DF_FNAME = "final.df"

# This needs to match volumns in `initdb.py`
EDGE_INFO_COLUMNS = ["cleft_segid", "size",
                     "presyn_segid", "postsyn_segid",
                     "presyn_x", "presyn_y", "presyn_z",
                     "postsyn_x", "postsyn_y", "postsyn_z"]
OPTIONAL_COLUMNS = ["hashed_index"]
CHUNK_START_COLUMNS = ["id", "begin_x", "begin_y", "begin_z"]
NULL_CHUNK_ID = initdb.NULL_CHUNK_ID


def chunk_info_fname(proc_url, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = EDGES_FMTSTR.format(tag=chunk_tag)
    return os.path.join(proc_url, EDGES_DIRNAME, basename)


def read_chunk_edge_info(proc_url, chunk_bounds=None, chunk_id=None,
                         read_index=False):
    """ Reads the edge info for a single chunk from storage """
    if io.is_db_url(proc_url):
        assert chunk_id is not None, "bounds reading not yet impl for dbs"
        metadata = io.open_db_metadata(proc_url)

        edges = metadata.tables["edges"]
        columns = list(edges.c[name] for name in EDGE_INFO_COLUMNS)
        statement = select(columns).where(edges.c.chunk_id == chunk_id)
        return io.read_db_dframe(proc_url, statement, index_col="cleft_segid")

    else:
        assert chunk_bounds is not None, "chunk id reading not impl for files"
        return io.read_dframe(chunk_info_fname(proc_url, chunk_bounds))


def read_hashed_edge_info(proc_url, hash_index, merged=True):
    assert io.is_db_url(proc_url), "reading by hash not supported for files"

    metadata = io.open_db_metadata(proc_url)

    edges = metadata.tables["edges"]
    columns = list(edges.c[name] for name in EDGE_INFO_COLUMNS)
    statement = select(columns).where(and_(edges.c.hashed_index == hash_index,
                                           edges.c.merged == merged))
    return io.read_db_dframe(proc_url, statement, index_col="cleft_segid")


def write_chunk_edge_info(dframe, proc_url, chunk_bounds=None, chunk_id=None):
    """Writes edge info for a single chunk to storage """
    if io.is_db_url(proc_url):
        assert chunk_id is not None, "bounds writing not yet impl for dbs"
        dframe["chunk_id"] = chunk_id
        dframe["merged"] = False
        dframe["final"] = False
        io.write_db_dframe(dframe, proc_url, "edges", index=False)

    else:
        assert chunk_bounds is not None, "chunk id writing not impl for files"
        return io.write_dframe(dframe,
                               chunk_info_fname(proc_url, chunk_bounds))


def read_all_chunk_edge_infos(proc_url):
    """
    Reads all edge info for chunks within storage.
    For file storage, currently assumes that NOTHING else is in the
    edge info subdirectory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)
        edges, chunks = metadata.tables["edges"], metadata.tables["chunks"]

        edgecols = list(edges.c[name] for name in EDGE_INFO_COLUMNS)
        edgecols.append(edges.c["chunk_id"])
        edgestmt = select(edgecols).where(and_(edges.c.merged == false(),
                                               edges.c.final == false()))

        chunkcols = list(chunks.c[name] for name in CHUNK_START_COLUMNS)
        chunkstmt = select(chunkcols)

        results = io.read_db_dframes(proc_url, (edgestmt, chunkstmt),
                                     index_cols=(None, "id"))
        edge_df, chunk_df = results[0], results[1]

        chunk_id_to_df = dict(iter(edge_df.groupby("chunk_id")))
        chunk_lookup = dict(zip(chunk_df.index, list(zip(chunk_df.begin_x,
                                                         chunk_df.begin_y,
                                                         chunk_df.begin_z))))

        dframe_lookup = {chunk_lookup[i]: df
                         for (i, df) in chunk_id_to_df.items()}

        # ensuring that each chunk is represented
        for chunk_begin in chunk_lookup.values():
            if chunk_begin not in dframe_lookup:
                dframe_lookup[chunk_begin] = pd.DataFrame(data=None,
                                                          columns=edgecols,
                                                          dtype=int)

    else:
        edges_dir = os.path.join(proc_url, EDGES_DIRNAME)
        fnames = io.pull_directory(edges_dir)
        assert len(fnames) > 0, "No filenames returned"

        starts = [io.bbox_from_fname(f).min() for f in fnames]
        dframes = [read_chunk_edge_info(f) for f in fnames]

        dframe_lookup = {s: df for (s, df) in zip(starts, dframes)}

    return io.utils.make_info_arr(dframe_lookup)


def read_max_n_edge_per_cleft(proc_url, n):
    assert io.is_db_url(proc_url)

    metadata = io.open_db_metadata(proc_url)
    edges = metadata.tables["edges"]

    n_column = edges.columns[n]
    statement = edges.select().distinct(edges.c.cleft_segid).\
                          order_by(edges.c.cleft_segid, n_column.desc()).\
                          where(edges.c.merged == false())

    return io.read_db_dframe(proc_url, statement, index_col="cleft_segid")


def read_merged_edge_info(proc_url, read_optional=False):
    """Reads the merged edge info dataframe from a processing directory"""
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        edges = metadata.tables["edges"]
        columns = list(edges.c[name] for name in EDGE_INFO_COLUMNS)
        if read_optional:
            columns += list(edges.c[name] for name in OPTIONAL_COLUMNS)
        statement = select(columns).where(and_(edges.c.merged == true(),
                                               edges.c.final == false()))
        return io.read_db_dframe(proc_url, statement, index_col="cleft_segid")

    else:
        return io.read_dframe(proc_url, MERGED_EDGES_FNAME)


def write_merged_edge_info(dframe, proc_url):
    """ Writes a merged edge info dataframe to storage. """
    if io.is_db_url(proc_url):
        dframe = dframe.reset_index()
        to_write = dframe[EDGE_INFO_COLUMNS].copy()
        for col in OPTIONAL_COLUMNS:
            if col in dframe.columns:
                to_write[col] = dframe[col]
                
        to_write["chunk_id"] = NULL_CHUNK_ID
        to_write["merged"] = True
        to_write["final"] = False
        io.write_db_dframe(to_write, proc_url, "edges", index=False)

    else:
        io.write_dframe(dframe, proc_url, MERGED_EDGES_FNAME)


def write_final_edge_info(dframe, proc_url):
    """
    Writes a merged edge info dataframe (with duplicates removed)
    to storage.
    """
    if io.is_db_url(proc_url):
        dframe["chunk_id"] = NULL_CHUNK_ID
        dframe["merged"] = True
        dframe["final"] = True
        io.write_db_dframe(dframe, proc_url, "edges")

    else:
        io.write_dframe(dframe, proc_url, FINAL_EDGES_FNAME)
