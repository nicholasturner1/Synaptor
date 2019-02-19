__doc__ = """
Segment info DataFrame IO for processing tasks
"""

import os

from sqlalchemy import select, and_
from sqlalchemy.sql.expression import true, false

from ... import io
from .. import colnames as cn
from . import filenames as fn


SEG_INFO_COLUMNS = [cn.segid, cn.size, *cn.centroid_cols, *cn.bbox_cols]
CHUNK_START_COLUMNS = [cn.chunk_tag, cn.chunk_bx, cn.chunk_by, cn.chunk_bz]


def chunk_info_fname(proc_url, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = fn.seginfo_fmtstr.format(tag=chunk_tag)

    return os.path.join(proc_url, fn.seginfo_dirname, basename)


def read_chunk_seg_info(proc_url, chunk_bounds):
    """ Reads seg info for a single chunk """
    if io.is_db_url(proc_url):
        tag = io.fname_chunk_tag(chunk_bounds)
        metadata = io.open_db_metadata(proc_url)

        segs = metadata.tables["chunk_segs"]
        columns = list(segs.c[name] for name in SEG_INFO_COLUMNS)
        statement = select(columns).where(segs.c[cn.chunk_tag] == chunk_tag)

        return io.read_db_dframe(proc_url, statement, index_col=cn.segid)

    else:
        return io.read_dframe(chunk_info_fname(proc_url, chunk_bounds))


def write_chunk_seg_info(dframe, proc_url, chunk_bounds):
    """ Writes seg info to the processing URL """
    if io.is_db_url(proc_url):
        chunk_tag = io.fname_chunk_tag(chunk_bounds)
        dframe[cn.chunk_tag] = chunk_tag
        io.write_db_dframe(dframe, proc_url, "chunk_segs")

    else:
        io.write_dframe(dframe, chunk_info_fname(proc_url, chunk_bounds))


def read_all_chunk_seg_infos(proc_url):
    """
    Reads all seg info for chunks within storage.
    Currently assumes that NOTHING else is in the
    seg info subdirectory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)
        segs = metadata.tables["chunk_segs"]
        chunks = metadata.tables["chunks"]

        segcols = list(segs.c[name] for name in SEG_INFO_COLUMNS)
        segcols.append(segs.c[cn.chunk_tag])
        segstmt = select(segcols)

        chunkcols = list(chunks.c[name] for name in CHUNK_START_COLUMNS)
        chunkstmt = select(chunkcols)

        results = io.read_db_dframes(proc_url, (segstmt, chunkstmt),
                                     index_cols=(cn.segid, "id"))
        seg_df, chunk_df = results[0], results[1]

        chunk_id_to_df = dict(iter(seg_df.groupby(cn.chunk_tag)))
        chunk_lookup = dict(zip(chunk_df[cn.chunk_tag],
                                zip(chunk_df[cn.chunk_bx],
                                    chunk_df[cn.chunk_by],
                                    chunk_df[cn.chunk_bz])))

        dframe_lookup = {chunk_lookup[i]: df
                         for (i, df) in chunk_id_to_df.items()}

    else:
        seginfo_dir = os.path.join(proc_url, fn.seginfo_dirname)
        fnames = io.pull_directory(seginfo_dir)
        assert len(fnames) > 0, "No filenames returned"

        starts = [io.bbox_from_fname(f).min() for f in fnames]
        dframes = [io.read_dframe(f) for f in fnames]

        dframe_lookup = {s: df for (s, df) in zip(starts, dframes)}

    return io.utils.make_info_arr(dframe_lookup)


def read_merged_seg_info(proc_url, hash_index=None):
    """
    Reads the merged seg info dataframe from storage. If hash_index is
    passed, restrict the results to those with an edge with partnerhash equal
    to this index
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        segs = metadata.tables["merged_segs"]
        columns = list(segs.c[name] for name in SEG_INFO_COLUMNS)

        if hash_index is None:
            statement = select(columns)
        else:
            edges = metadata.tables["chunk_edges"]
            statement = select(columns).select_from(
                            segs.join(edges,
                                      segs.c[cn.segid] == edges.c[cn.segid])
                            ).where(edges.c[cn.partnerhash] == hash_index)

        return io.read_db_dframe(proc_url, statement, index_col=cn.segid)

    else:
        assert hash_index is None, "hash_index not implemented for file IO"
        dframe = io.read_dframe(proc_url, fn.merged_seginfo_fname)


def write_merged_seg_info(dframe, proc_url):
    """Writes a merged seg info dataframe to storage. """
    if io.is_db_url(proc_url):
        io.write_db_dframe(dframe, proc_url, "merged_segs", index=False)

    else:
        io.write_dframe(dframe, proc_url, fn.merged_seginfo_fname)
