""" Edge info DataFrame IO for processing tasks """


from sqlalchemy import select

from ... import io
from .. import colnames as cn
from . import filenames as fn


FULL_INFO_COLUMNS = [cn.seg_id, cn.presyn_id, cn.postsyn_id, cn.size,
                     *cn.centroid_cols, *cn.bbox_cols,
                     *cn.presyn_coord_cols, *cn.postsyn_coord_cols,
                     cn.clefthash, cn.partnerhash]


def read_full_info(proc_url):
    """
    Reads the info dataframe with clefts and edges combined
    from a processing directory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        final = metadata.tables["final"]
        columns = list(final.c[name] for name in FULL_INFO_COLUMNS)
        statement = select(columns)

        return io.read_db_dframe(proc_url, statement, index_col=cn.seg_id)

    else:
        return io.read_dframe(proc_url, fn.final_edgeinfo_fname)


def write_full_info(dframe, proc_url, tag=None):
    """
    Writes the info dataframe with clefts and edges combined
    to a processing directory
    """
    if io.is_db_url(proc_url):
        dframe = dframe.reset_index()
        io.write_db_dframe(dframe, proc_url, "final", index=False)

    else:
        if tag is None:
            io.write_dframe(dframe, proc_url, fn.final_edgeinfo_fname)
        else:
            io.write_dframe(dframe, proc_url,
                            fn.tagged_final_edgeinfo_fname.format(tag))
