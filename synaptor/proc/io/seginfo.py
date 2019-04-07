""" Segment info DataFrame IO for processing tasks """


import os

from sqlalchemy import select, text
import pandas as pd

from ... import io
from .. import colnames as cn
from . import filenames as fn


SEG_INFO_COLUMNS = [cn.seg_id, cn.size, *cn.centroid_cols, *cn.bbox_cols]
CHUNK_START_COLUMNS = [cn.chunk_tag, cn.chunk_bx, cn.chunk_by, cn.chunk_bz]
CHUNKED_TABLENAME = "chunk_segs"
MERGED_TABLENAME = "merged_segs"


def chunk_info_fname(proc_url, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = fn.seginfo_fmtstr.format(tag=chunk_tag)

    return os.path.join(proc_url, fn.seginfo_dirname, basename)


def read_chunk_seg_info(proc_url, chunk_bounds):
    """ Reads seg info for a single chunk """
    if io.is_db_url(proc_url):
        tag = io.fname_chunk_tag(chunk_bounds)
        metadata = io.open_db_metadata(proc_url)

        segs = metadata.tables[CHUNKED_TABLENAME]
        columns = list(segs.c[name] for name in SEG_INFO_COLUMNS)
        statement = select(columns).where(segs.c[cn.chunk_tag] == tag)

        return io.read_db_dframe(proc_url, statement, index_col=cn.seg_id)

    else:
        return io.read_dframe(chunk_info_fname(proc_url, chunk_bounds))


def write_chunk_seg_info(dframe, proc_url, chunk_bounds):
    """ Writes seg info to the processing URL """
    if io.is_db_url(proc_url):
        to_write, tablename = prep_chunk_seg_info(dframe, chunk_bounds)
        io.write_db_dframe(to_write, proc_url, tablename)

    else:
        io.write_dframe(dframe, chunk_info_fname(proc_url, chunk_bounds))


def prep_chunk_seg_info(dframe, chunk_bounds):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    to_write = dframe.reset_index()[SEG_INFO_COLUMNS].copy()
    to_write[cn.chunk_tag] = chunk_tag

    return to_write, CHUNKED_TABLENAME


def read_all_chunk_seg_infos(proc_url):
    """
    Reads all seg info for chunks within storage.
    Currently assumes that NOTHING else is in the
    seg info subdirectory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)
        segs = metadata.tables[CHUNKED_TABLENAME]
        chunks = metadata.tables["chunks"]

        segcols = list(segs.c[name] for name in SEG_INFO_COLUMNS)
        segcols.append(segs.c[cn.chunk_tag])
        segstmt = select(segcols)

        chunkcols = list(chunks.c[name] for name in CHUNK_START_COLUMNS)
        chunkstmt = select(chunkcols)

        results = io.read_db_dframes(proc_url, (segstmt, chunkstmt),
                                     index_cols=(cn.seg_id, "id"))
        seg_df, chunk_df = results[0], results[1]

        chunk_id_to_df = dict(iter(seg_df.groupby(cn.chunk_tag)))
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
        seginfo_dir = os.path.join(proc_url, fn.seginfo_dirname)
        fnames = io.pull_directory(seginfo_dir)
        assert len(fnames) > 0, "No filenames returned"

        starts = [io.bbox_from_fname(f).min() for f in fnames]
        dframes = [io.read_dframe(f) for f in fnames]

        dframe_lookup = {s: df for (s, df) in zip(starts, dframes)}

    return io.utils.make_info_arr(dframe_lookup), os.path.dirname(fnames[0])


def make_empty_df():
    """ Make an empty dataframe as a placeholder. """
    df = pd.DataFrame(data=None, dtype=int, columns=SEG_INFO_COLUMNS)

    return df.set_index(cn.seg_id)


def read_mapped_seginfo_by_dst_hash(proc_url, hashval):
    assert io.is_db_url(proc_url), "Not implemented for file IO"

    metadata = io.open_db_metadata(proc_url)
    chunk_segs = metadata.tables[CHUNKED_TABLENAME]
    seg_merge_map = metadata.tables["seg_merge_map"]

    segs_cols = list(chunk_segs.c[name] for name in SEG_INFO_COLUMNS)
    map_cols = [seg_merge_map.c[cn.dst_id]]

    # matching columns for join
    chunk_seg_id = chunk_segs.c["id"]
    merge_map_id = seg_merge_map.c[cn.src_id]
    dst_id_hash = seg_merge_map.c[cn.dst_id_hash]

    statement = select(segs_cols + map_cols).select_from(
                    chunk_segs.join(seg_merge_map,
                                    chunk_seg_id == merge_map_id)).where(
                                    dst_id_hash == hashval)

    return io.read_db_dframe(proc_url, statement)


def read_all_unique_seg_ids(proc_url):
    assert io.is_db_url(proc_url), "Not implemented for file IO"

    metadata = io.open_db_metadata(proc_url)
    chunk_segs = metadata.tables[CHUNKED_TABLENAME]

    columns = [chunk_segs.c["id"]]

    statement = select(columns)

    return io.read_db_dframe(proc_url, statement)["id"].tolist()


def read_merged_seg_info(proc_url, hash_index=None):
    """
    Reads the merged seg info dataframe from storage. If hash_index is
    passed, restrict the results to those with an edge with partnerhash equal
    to this index
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        segs = metadata.tables[MERGED_TABLENAME]
        columns = list(segs.c[name] for name in SEG_INFO_COLUMNS)

        if hash_index is None:
            statement = select(columns)
        else:
            edges = metadata.tables["merged_edges"]
            statement = select(columns).select_from(
                            segs.join(edges,
                                      segs.c[cn.seg_id] == edges.c[cn.seg_id])
                            ).where(edges.c[cn.partnerhash] == hash_index)

        raw_df = io.read_db_dframe(proc_url, statement)
        df = raw_df.loc[~raw_df[cn.seg_id].duplicated()]
        return df.set_index(cn.seg_id)

    else:
        assert hash_index is None, "hash_index not implemented for file IO"
        return io.read_dframe(proc_url, fn.merged_seginfo_fname)


def write_merged_seg_info(dframe, proc_url, hash_tag=None):
    """Writes a merged seg info dataframe to storage. """
    if io.is_db_url(proc_url):
        io.write_db_dframe(dframe, proc_url, MERGED_TABLENAME, index=True)

    else:
        if hash_tag is not None:
            filename = fn.merged_seginfo_fmtstr.format(tag=hash_tag)
        else:
            filename = fn.merged_seginfo_fname

        io.write_dframe(dframe, proc_url, filename)


def dedup_chunk_segs(proc_url):
    assert io.is_db_url(proc_url), "not implemented for file IO"

    statement = text("""DELETE FROM chunk_segs a USING chunk_segs b
                        WHERE a.id > b.id
                        AND a.cleft_segid = b.cleft_segid
                        AND a.chunk_tag = b.chunk_tag""")

    io.execute_db_statement(proc_url, statement)
