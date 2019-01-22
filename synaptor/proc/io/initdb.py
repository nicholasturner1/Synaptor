from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, Boolean, Float, BigInteger

import pandas as pd

from ... import io
from ... import types


__all__ = ["init_db", "drop_db", "fill_chunks"]


# NOTE: These need to be listed in a certain order to resolve dependencies when
# deleting tables (See drop_db below)
# - edges, clefts, & continuations depend on chunks
TABLES = ["edges", "clefts", "continuations",
          "chunks", "cleft_map", "dup_map",
          "overlaps"]
NULL_CHUNK_ID = 1


def init_db(url, metadata=None, edges=True, overlaps=False):
    """ Initializes the record database at a SQLAlchemy URL. """
    if metadata is None:
        metadata = io.open_db_metadata(url)

    init_chunks(metadata)

    init_clefts(metadata)
    init_continuations(metadata)
    init_cleft_map(metadata)

    if edges:
        init_edges(metadata)
        init_dup_map(metadata)

    if overlaps:
        init_overlaps(metadata)

    io.create_db_tables(url, metadata)

    return metadata


def init_chunks(metadata):
    return Table("chunks", metadata,
                 Column("id", Integer, primary_key=True),
                 Column("begin_x", Integer),
                 Column("begin_y", Integer),
                 Column("begin_z", Integer),
                 Column("end_x", Integer),
                 Column("end_y", Integer),
                 Column("end_z", Integer))


def init_clefts(metadata):
    return Table("clefts", metadata,
                 Column("id", Integer, primary_key=True),
                 Column("cleft_segid", Integer),
                 Column("chunk_id", None, ForeignKey("chunks.id"),
                        default=NULL_CHUNK_ID),
                 Column("size", Integer),
                 # centroid coordinates
                 Column("centroid_x", Float),
                 Column("centroid_y", Float),
                 Column("centroid_z", Float),
                 # cleft bbox
                 Column("bbox_bx", Integer),
                 Column("bbox_by", Integer),
                 Column("bbox_bz", Integer),
                 Column("bbox_ex", Integer),
                 Column("bbox_ey", Integer),
                 Column("bbox_ez", Integer),
                 # merged across chunks?
                 Column("merged", Boolean, default=False),
                 # final version?
                 Column("final", Boolean, default=False))


def init_continuations(metadata):
    pass


def init_cleft_map(metadata):
    return Table("cleft_map", metadata,
                 Column("id", Integer, primary_key=True),
                 Column("chunk_id", None, ForeignKey("chunks.id")),
                 Column("prev_id", Integer),
                 Column("new_id", Integer))


def init_edges(metadata):
    return Table("edges", metadata,
                 Column("id", Integer, primary_key=True),
                 Column("cleft_segid", Integer),
                 Column("chunk_id", None, ForeignKey("chunks.id")),
                 Column("presyn_segid", BigInteger),
                 Column("postsyn_segid", BigInteger),
                 Column("size", Integer),
                 # Anchor points
                 Column("presyn_x", Integer),
                 Column("presyn_y", Integer),
                 Column("presyn_z", Integer),
                 Column("postsyn_x", Integer),
                 Column("postsyn_y", Integer),
                 Column("postsyn_z", Integer),
                 # final version of cleft_id?
                 Column("merged", Boolean, default=False),
                 Column("final", Boolean, default=False),
                 Column("clefthash", Integer, default=-1),
                 Column("partnerhash", Integer, default=-1))


def init_dup_map(metadata):
    return Table("dup_map", metadata,
                 Column("id", Integer, primary_key=True),
                 Column("prev_id", Integer),
                 Column("new_id", Integer))


def init_overlaps(metadata):
    pass


def drop_db(url, metadata=None):
    if metadata is None:
        metadata = io.open_db_metadata(url)

    tables = [metadata.tables[t] for t in TABLES if t in metadata.tables]

    return io.drop_db_tables(url, metadata, tables=tables)


def fill_chunks(url, bboxes):

    dframe = pd.DataFrame([(0,0,0,0,0,0)] +
                          [bbox.astuple() for bbox in bboxes])

    dframe.columns = ["begin_x", "begin_y", "begin_z",
                      "end_x", "end_y", "end_z"]
    dframe.index.name = "id"

    io.write_db_dframe(dframe, url, "chunks")
