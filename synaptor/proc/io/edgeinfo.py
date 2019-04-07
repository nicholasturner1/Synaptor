""" Edge info DataFrame IO for processing tasks """


import os

from sqlalchemy import select
import pandas as pd

from ... import io
from .. import colnames as cn
from . import filenames as fn


EDGE_INFO_COLUMNS = [cn.seg_id, cn.size, cn.presyn_id, cn.postsyn_id,
                     *cn.presyn_coord_cols, *cn.postsyn_coord_cols,
                     cn.clefthash, cn.partnerhash]
CHUNK_START_COLUMNS = [cn.chunk_tag, cn.chunk_bx, cn.chunk_by, cn.chunk_bz]


def chunk_info_fname(proc_url, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = fn.edgeinfo_fmtstr.format(tag=chunk_tag)

    return os.path.join(proc_url, fn.edgeinfo_dirname, basename)


def read_chunk_edge_info(proc_url, chunk_bounds):
    """ Reads the edge info for a single chunk from storage """
    if io.is_db_url(proc_url):
        tag = io.fname_chunk_tag(chunk_bounds)
        metadata = io.open_db_metadata(proc_url)

        edges = metadata.tables["chunk_edges"]
        columns = list(edges.c[name] for name in EDGE_INFO_COLUMNS)
        statement = select(columns).where(edges.c[cn.chunk_tag] == tag)

        return io.read_db_dframe(proc_url, statement, index_col=cn.seg_id)

    else:
        return io.read_dframe(chunk_info_fname(proc_url, chunk_bounds))


def read_hashed_edge_info(proc_url, partnerhash=None,
                          clefthash=None, merged=True, dedup=False):
    """ Reads the edge information with a particular hash value. """
    assert partnerhash is not None or clefthash is not None, "Need hash value"
    assert partnerhash is None or clefthash is None, "Specify only one hash"
    assert io.is_db_url(proc_url), "reading by hash not supported for files"

    metadata = io.open_db_metadata(proc_url)

    if merged:
        edges = metadata.tables["merged_edges"]
    else:
        edges = metadata.tables["chunk_edges"]

    columns = list(edges.c[name] for name in EDGE_INFO_COLUMNS)

    if partnerhash is not None:
        statement = select(columns).where(edges.c.partnerhash == partnerhash)
    elif clefthash is not None:
        statement = select(columns).where(edges.c.clefthash == clefthash)

    if dedup:
        raw_df = io.read_db_dframe(proc_url, statement)
        df = raw_df.loc[~raw_df[cn.seg_id].duplicated()]
        return df.set_index(cn.seg_id)
    else:
        return io.read_db_dframe(proc_url, statement, index_col=cn.seg_id)


def write_chunk_edge_info(dframe, proc_url, chunk_bounds):
    """ Writes edge info for a single chunk to storage. """
    if io.is_db_url(proc_url):
        chunk_tag = io.fname_chunk_tag(chunk_bounds)
        to_write = dframe[EDGE_INFO_COLUMNS].copy()
        to_write[cn.chunk_tag] = chunk_tag
        io.write_db_dframe(to_write, proc_url, "chunk_edges", index=False)

    else:
        io.write_dframe(dframe, chunk_info_fname(proc_url, chunk_bounds))


def read_all_chunk_edge_infos(proc_url):
    """
    Reads all edge info for chunks within storage.
    For file storage, currently assumes that NOTHING else is in the
    edge info subdirectory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)
        edges = metadata.tables["chunk_edges"]
        chunks = metadata.tables["chunks"]

        edgecols = list(edges.c[name] for name in EDGE_INFO_COLUMNS)
        edgecols.append(edges.c[cn.chunk_tag])
        edgestmt = select(edgecols)

        chunkcols = list(chunks.c[name] for name in CHUNK_START_COLUMNS)
        chunkstmt = select(chunkcols)

        results = io.read_db_dframes(proc_url, (edgestmt, chunkstmt),
                                     index_cols=(cn.seg_id, "id"))
        edge_df, chunk_df = results[0], results[1]

        chunk_id_to_df = dict(iter(edge_df.groupby(cn.chunk_tag)))
        chunk_lookup = dict(zip(chunk_df[cn.chunk_tag],
                                list(zip(chunk_df[cn.chunk_bx],
                                         chunk_df[cn.chunk_by],
                                         chunk_df[cn.chunk_bz]))))

        dframe_lookup = {chunk_lookup[i]: df
                         for (i, df) in chunk_id_to_df.items()}

        # ensuring that each chunk is represented
        for chunk_begin in chunk_lookup.values():
            if chunk_begin not in dframe_lookup:
                dframe_lookup[chunk_begin] = make_empty_df()

    else:
        edgeinfo_dir = os.path.join(proc_url, fn.edgeinfo_dirname)
        fnames = io.pull_directory(edgeinfo_dir)
        assert len(fnames) > 0, "No filenames returned"

        starts = [io.bbox_from_fname(f).min() for f in fnames]
        dframes = [io.read_dframe(f) for f in fnames]

        dframe_lookup = {s: df for (s, df) in zip(starts, dframes)}

    return io.utils.make_info_arr(dframe_lookup)


def make_empty_df():
    """ Make an empty dataframe as a placeholder. """
    df = pd.DataFrame(data=None, dtype=int, columns=EDGE_INFO_COLUMNS)

    return df.set_index(cn.seg_id)


def read_max_n_edge_per_cleft(proc_url, n):
    """ Read the edge with maximum `n` value over all chunks. """
    assert io.is_db_url(proc_url)

    metadata = io.open_db_metadata(proc_url)
    edges = metadata.tables["chunk_edges"]

    n_column = edges.columns[n]
    statement = edges.select().distinct(edges.c[cn.seg_id]).\
        order_by(edges.c[cn.seg_id], n_column.desc())

    return io.read_db_dframe(proc_url, statement, index_col=cn.seg_id)


def read_merged_edge_info(proc_url):
    """ Reads the merged edge info dataframe from a processing directory. """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        edges = metadata.tables["merged_edges"]
        columns = list(edges.c[name] for name in EDGE_INFO_COLUMNS)
        statement = select(columns)

        # Removing duplicates in case...
        raw_df = io.read_db_dframe(proc_url, statement)
        df = raw_df.loc[~raw_df[cn.seg_id].duplicated()]
        return df.set_index(cn.seg_id)
    else:
        return io.read_dframe(proc_url, fn.merged_edgeinfo_fname)


def write_merged_edge_info(dframe, proc_url):
    """ Writes a merged edge info dataframe to storage. """
    if io.is_db_url(proc_url):
        dframe = dframe.reset_index()
        io.write_db_dframe(dframe, proc_url, "merged_edges", index=False)

    else:
        io.write_dframe(dframe, proc_url, fn.merged_edgeinfo_fname)


def write_final_edge_info(dframe, proc_url):
    """
    Writes a merged edge info dataframe (with duplicates removed)
    to storage.
    """
    if io.is_db_url(proc_url):
        io.write_db_dframe(dframe, proc_url, "final")

    else:
        io.write_dframe(dframe, proc_url, fn.final_edgeinfo_fname)
