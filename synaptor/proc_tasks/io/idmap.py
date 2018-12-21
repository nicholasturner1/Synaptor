#!/usr/bin/env python3
__doc__ = """
Cleft ID mapping IO for processing tasks
"""

import os

from sqlalchemy import select
import pandas as pd

from ... import io


# FILE STORAGE CONVENTIONS
# Id maps for merging clefts
ID_MAP_DIRNAME = "id_maps"
ID_MAP_FMTSTR = "id_map_{tag}.df"
# Mapping to merge duplicates
DUP_MAP_FNAME = "dup_id_map.df"

ID_MAP_COLUMNS = ["prev_id", "new_id"]


def cleft_map_fname(proc_url, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = ID_MAP_FMTSTR.format(tag=chunk_tag)
    return os.path.join(proc_url, ID_MAP_DIRNAME, basename)


def make_dframe(id_map):
    dframe = pd.DataFrame(pd.Series(id_map), columns=["new_id"])
    dframe.index.name = "prev_id"
    return dframe


def read_chunk_id_map(proc_url, chunk_bounds=None, chunk_id=None):
    """Reads an id mapping for a chunk from a processing directory"""
    if io.is_db_url(proc_url):
        assert chunk_id is not None, "bounds reading not yet impl for dbs"
        metadata = io.open_db_metadata(proc_url)

        cleft_maps = metadata.tables["cleft_map"]
        columns = list(cleft_maps.c[name] for name in ID_MAP_COLUMNS)
        statement = select(columns).where(cleft_maps.c.chunk_id == chunk_id)

        dframe = io.read_db_dframe(proc_url, statement, index_col="prev_id")

    else:
        assert chunk_bounds is not None, "chunk id reading not impl for files"
        fname = io.pull_file(cleft_map_fname(proc_url, chunk_bounds))

        dframe = io.read_dframe(fname)

    return dict(zip(dframe.index, dframe.new_id))


def write_chunk_id_map(id_map, proc_url, chunk_bounds=None, chunk_id=None):
    """Writes an id mapping for a chunk to a processing directory"""
    dframe = make_dframe(id_map)

    if io.is_db_url(proc_url):
        assert chunk_id is not None, "bounds writing not yet impl for dbs"
        dframe["chunk_id"] = chunk_id
        io.write_db_dframe(dframe, proc_url, "cleft_map")

    else:
        assert chunk_bounds is not None, "chunk id writing not impl for files"
        io.write_dframe(dframe, cleft_map_fname(proc_url, chunk_bounds))


def write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_url):
    """
    Writes all of the id mappings for each chunk to a subdirectory
    of a processing directory
    """
    if io.is_db_url(proc_url):
        raise(Exception("haven't implemented chunk mapping for dbs yet"))

    else:
        if not os.path.exists(ID_MAP_DIRNAME):
            os.makedirs(ID_MAP_DIRNAME)

        for (id_map, bounds) in zip(chunk_id_maps.flat, chunk_bounds):

            chunk_tag = io.fname_chunk_tag(bounds)
            fname = os.path.join(ID_MAP_DIRNAME,
                                 ID_MAP_FMTSTR.format(tag=chunk_tag))
            write_chunk_id_map(id_map, fname)

        io.send_directory(ID_MAP_DIRNAME, proc_url)


def read_dup_id_map(proc_url):
    """ Reads a duplicate mapping from storage. """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        dup_map = metadata.tables["dup_map"]
        dframe = io.read_db_dframe(proc_url, dup_map.select(),
                                   index_col="prev_id")

    else:
        try:
            dframe = io.read_dframe(proc_url, "dup_id_map.df")
        except Exception as e:
            print(e)
            print("WARNING: no dup id map found, passing empty dup mapping")
            dframe = pd.DataFrame({"new_id": []})

    return dict(zip(dframe.index, dframe.new_id))


def write_dup_id_map(id_map, proc_url):
    """ Writes a duplicate mapping to storage. """
    dframe = make_dframe(id_map)

    if io.is_db_url(proc_url):
        io.write_db_dframe(dframe, proc_url, "dup_map")

    else:
        io.write_dframe(dframe, proc_url, DUP_MAP_FNAME)
