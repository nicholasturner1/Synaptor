""" Cleft ID mapping IO for processing tasks """


import os

from sqlalchemy import select
import pandas as pd

from ... import io
from .. import colnames as cn
from . import filenames as fn


ID_MAP_COLUMNS = [cn.src_id, cn.dst_id]
UNIQUE_ID_MAP_COLUMNS = ["id", cn.seg_id]
CHUNKED_ID_MAP_COLUMNS = [cn.seg_id, cn.dst_id, cn.chunk_tag]


def cleft_map_fname(proc_url, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = fn.idmap_fmtstr.format(tag=chunk_tag)

    return os.path.join(proc_url, fn.idmap_dirname, basename)


def make_dframe_from_dict(id_map):
    df = pd.DataFrame(pd.Series(id_map), columns=[cn.dst_id])
    df.index.name = cn.src_id

    return df


def read_chunk_unique_ids(proc_url, chunk_bounds):
    assert io.is_db_url(proc_url), "file unique id map not implemented yet"

    tag = io.fname_chunk_tag(chunk_bounds)
    metadata = io.open_db_metadata(proc_url)
    chunk_segs = metadata.tables["chunk_segs"]

    columns = list(chunk_segs.c[name] for name in UNIQUE_ID_MAP_COLUMNS)
    statement = select(columns).where(chunk_segs.c[cn.chunk_tag] == tag)

    dframe = io.read_db_dframe(proc_url, statement)

    return dict(zip(dframe[cn.seg_id], dframe["id"]))


def read_all_chunk_unique_ids(proc_url):
    assert io.is_db_url(proc_url), "file unique id map not implemented yet"

    metadata = io.open_db_metadata(proc_url)
    chunk_segs = metadata.tables["chunk_segs"]

    columns = list(chunk_segs.c[name] for name in UNIQUE_ID_MAP_COLUMNS)
    columns.append(chunk_segs.c[cn.chunk_tag])
    statement = select(columns)

    dframe = io.read_db_dframe(proc_url, statement)

    chunk_tag_to_df = dict(iter(dframe.groupby(cn.chunk_tag)))

    map_lookup = {io.bbox_from_tag(tag).min(): unique_id_dframe_to_map(df)
                  for (tag, df) in chunk_tag_to_df.items()}

    return map_lookup


def unique_id_dframe_to_map(dframe):
    return dict(zip(dframe[cn.seg_id], dframe["id"]))


def write_seg_merge_map(seg_merge_df, proc_url):
    assert io.is_db_url(proc_url), "merge map IO not implemented for files"
    io.write_db_dframe(seg_merge_df, proc_url, "seg_merge_map")


def write_chunked_seg_map(proc_url):
    assert io.is_db_url(proc_url), "not implemented for files"

    metadata = io.open_db_metadata(proc_url)

    # order matters for these - sum of the first two
    # needs to match the third (see query below)
    chunk_seg_colnames = [cn.seg_id, cn.chunk_tag]
    merge_map_colnames = [cn.dst_id]
    chunked_map_colnames = [cn.src_id, cn.chunk_tag, cn.dst_id]

    chunk_segs = metadata.tables["chunk_segs"]
    seg_merge_map = metadata.tables["seg_merge_map"]
    chunked_map = metadata.tables["chunked_seg_merge_map"]

    cs_columns = list(chunk_segs.c[name] for name in chunk_seg_colnames)
    smm_columns = list(seg_merge_map.c[name] for name in merge_map_colnames)

    # matching columns for join
    chunk_seg_id = chunk_segs.c["id"]
    merge_map_id = seg_merge_map.c[cn.src_id]

    select_stmt = select(cs_columns + smm_columns).select_from(
                      chunk_segs.join(seg_merge_map,
                                      chunk_seg_id == merge_map_id))
    full_stmt = chunked_map.insert().from_select(
                    names=chunked_map_colnames,
                    select=select_stmt)

    io.execute_db_statement(proc_url, full_stmt)


def read_chunk_id_map(proc_url, chunk_bounds):
    """Reads an id mapping for a chunk from a processing directory"""
    if io.is_db_url(proc_url):
        tag = io.fname_chunk_tag(chunk_bounds)
        metadata = io.open_db_metadata(proc_url)

        cleft_maps = metadata.tables["chunked_seg_merge_map"]
        columns = list(cleft_maps.c[name] for name in ID_MAP_COLUMNS)
        statement = select(columns).where(cleft_maps.c[cn.chunk_tag] == tag)
        dframe = io.read_db_dframe(proc_url, statement, index_col=cn.src_id)

    else:
        fname = io.pull_file(cleft_map_fname(proc_url, chunk_bounds))
        dframe = io.read_dframe(fname)

    return dict(zip(dframe.index, dframe.dst_id))


def write_chunk_id_map(id_map, proc_url, chunk_bounds):
    """Writes an id mapping for a chunk to a processing directory"""
    dframe = make_dframe_from_dict(id_map)

    if io.is_db_url(proc_url):
        tag = io.fname_chunk_tag(chunk_bounds)
        dframe["chunk_tag"] = tag
        io.write_db_dframe(dframe, proc_url, "seg_idmap")

    else:
        io.write_dframe(dframe, cleft_map_fname(proc_url, chunk_bounds))


def write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_url):
    """
    Writes all of the id mappings for each chunk to a subdirectory
    of a processing directory
    """
    if io.is_db_url(proc_url):

        for (id_map, bounds) in zip(chunk_id_maps.flat, chunk_bounds):
            # Simple for now, since I'm not sure how to implement this later
            write_chunk_id_map(id_map, proc_url, bounds)

    else:
        if not os.path.exists(fn.idmap_dirname):
            os.makedirs(fn.idmap_dirname)

        for (id_map, bounds) in zip(chunk_id_maps.flat, chunk_bounds):
            write_chunk_id_map(id_map, "./", bounds)

        io.send_directory(fn.idmap_dirname, proc_url)


def read_dup_id_map(proc_url):
    """ Reads a duplicate mapping from storage. """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        dup_map = metadata.tables["dup_merge_map"]
        dframe = io.read_db_dframe(proc_url, dup_map.select(),
                                   index_col=cn.src_id)

    else:
        try:
            dframe = io.read_dframe(proc_url, "dup_id_map.df")
        except Exception as e:
            print(e)
            print("WARNING: no dup id map found, passing empty dup mapping")
            dframe = pd.DataFrame({cn.dst_id: []})

    return dict(zip(dframe.index, dframe[cn.dst_id]))


def write_dup_id_map(id_map, proc_url):
    """ Writes a duplicate mapping to storage. """
    dframe = make_dframe_from_dict(id_map)

    if io.is_db_url(proc_url):
        io.write_db_dframe(dframe.reset_index(), proc_url, "dup_merge_map")

    else:
        io.write_dframe(dframe, proc_url, fn.dup_map_fname)
