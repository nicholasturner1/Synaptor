from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, Boolean, Float, BigInteger

import pandas as pd

from ... import io
from ... import types
from ..utils import schema as sch


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
                 Column(sch.chunk_bx, Integer),
                 Column(sch.chunk_by, Integer),
                 Column(sch.chunk_bz, Integer),
                 Column(sch.chunk_ex, Integer),
                 Column(sch.chunk_ey, Integer),
                 Column(sch.chunk_ez, Integer))


def init_clefts(metadata):
    return Table("clefts", metadata,
                 Column("id", Integer, primary_key=True),
                 Column(sch.cleft_id, Integer),
                 Column(sch.chunk_id, None, ForeignKey("chunks.id"),
                        default=NULL_CHUNK_ID),
                 Column(sch.size, Integer),
                 # centroid coordinates
                 Column(sch.centroid_x, Float),
                 Column(sch.centroid_y, Float),
                 Column(sch.centroid_z, Float),
                 # cleft bbox
                 Column(sch.bbox_bx, Integer),
                 Column(sch.bbox_by, Integer),
                 Column(sch.bbox_bz, Integer),
                 Column(sch.bbox_ex, Integer),
                 Column(sch.bbox_ey, Integer),
                 Column(sch.bbox_ez, Integer),
                 # merged across chunks?
                 Column("merged", Boolean, default=False),
                 # final version?
                 Column("final", Boolean, default=False))


def init_continuations(metadata):
    pass


def init_cleft_map(metadata):
    return Table("cleft_map", metadata,
                 Column("id", Integer, primary_key=True),
                 Column(sch.chunk_id, None, ForeignKey("chunks.id")),
                 Column("prev_id", Integer),
                 Column("new_id", Integer))


def init_edges(metadata):
    return Table("edges", metadata,
                 Column("id", Integer, primary_key=True),
                 Column(sch.cleft_id, Integer),
                 Column(sch.chunk_id, None, ForeignKey("chunks.id")),
                 Column(sch.presyn_id, BigInteger),
                 Column(sch.postsyn_id, BigInteger),
                 Column(sch.size, Integer),
                 # Anchor points
                 Column(sch.presyn_x, Integer),
                 Column(sch.presyn_y, Integer),
                 Column(sch.presyn_z, Integer),
                 Column(sch.postsyn_x, Integer),
                 Column(sch.postsyn_y, Integer),
                 Column(sch.postsyn_z, Integer),
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

    dframe.columns = [sch.chunk_bx, sch.chunk_by, sch.chunk_bz,
                      sch.chunk_ex, sch.chunk_ey, sch.chunk_ez]
    dframe.index.name = "id"

    io.write_db_dframe(dframe, url, "chunks")
