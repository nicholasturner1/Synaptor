"""
Database Initialization Functions

NOTE: I use the database as a glorified file store with transactions,
so the schema isn't normalized at all.

The current reasons for this approach are:
(1) Matching the file IO interface as easily as possible (i.e. I'm lazy)
(2) Putting as little pressure on the database as possible for scalability.
The queries required for our purposes should be rarely more complicated than
single WHERE clauses with this approach.

Current downsides are:
(1) Data replication
(2) Queries outside of the expected set could be very inefficient
"""

from sqlalchemy import Table, Column
from sqlalchemy import Integer, Float, BigInteger, Text
import pandas as pd

from ... import io
from .. import colnames as cn


__all__ = ["init_db", "drop_db", "fill_chunks", "TABLES"]


# NOTE: These need to be listed in a certain order to resolve dependencies when
# deleting tables (See drop_db below)
# - edges, clefts, & continuation_files depend on chunks
TABLES = ["final", "contin_graph", "merged_edges", "chunk_edges",
          "merged_segs", "chunk_segs",
          "seg_merge_map", "chunked_seg_merge_map", "dup_merge_map",
          "continuations", "chunk_overlaps", "max_overlaps", "timing_log"]


def init_db(url, segid_colname=cn.seg_id, metadata=None,
            edges=True, overlaps=False):
    """ Initializes a record database at a SQLAlchemy URL. """
    if metadata is None:
        metadata = io.open_db_metadata(url)

    # init_chunks(metadata)
    init_timing_log(metadata)

    init_seg_tables(metadata, segid_colname)
    init_continuation_tables(metadata)
    init_idmap_tables(metadata)

    if edges:
        init_edge_tables(metadata)
        init_idmap_table(metadata, "dup_merge_map")

    if overlaps:
        init_overlap_tables(metadata)

    io.create_db_tables(url, metadata)

    return metadata


def init_timing_log(metadata):
    """ Specified a table to record task durations """
    return Table("timing_log", metadata,
                 Column("id", Integer, primary_key=True),
                 Column(cn.task_name, Text),
                 Column(cn.timing_tag, Text),
                 Column(cn.task_time, Float))


def init_chunks(metadata):
    """ Specifies a table to record chunk tags. """
    return Table("chunks", metadata,
                 Column("id", Integer, primary_key=True),
                 Column(cn.chunk_bx, Integer),
                 Column(cn.chunk_by, Integer),
                 Column(cn.chunk_bz, Integer),
                 Column(cn.chunk_ex, Integer),
                 Column(cn.chunk_ey, Integer),
                 Column(cn.chunk_ez, Integer),
                 Column(cn.chunk_tag, Text))


def init_seg_tables(metadata, segid_colname=cn.seg_id):
    """
    Specifies two tables to track information about segments through their
    processing stages.
    """
    init_seg_table(metadata, "chunk_segs", segid_colname=segid_colname)
    init_seg_table(metadata, "merged_segs", segid_colname=segid_colname,
                   chunked=False)


def init_seg_table(metadata, tablename, segid_colname=cn.seg_id, chunked=True):
    """ Specifies a table for tracking info about a segment. """
    columns = [Column("id", BigInteger, primary_key=True),
               Column(cn.seg_id, Integer, index=True),
               Column(cn.size, Integer),
               # Centroid coordinates
               Column(cn.centroid_x, Float),
               Column(cn.centroid_y, Float),
               Column(cn.centroid_z, Float),
               # Bounding box
               Column(cn.bbox_bx, Integer),
               Column(cn.bbox_by, Integer),
               Column(cn.bbox_bz, Integer),
               Column(cn.bbox_ex, Integer),
               Column(cn.bbox_ey, Integer),
               Column(cn.bbox_ez, Integer)]

    if chunked:
        # Chunk id - None if merged across chunks
        columns.append(Column(cn.chunk_tag, Text, index=True))

    return Table(tablename, metadata, *columns)


def init_continuation_tables(metadata):
    init_continuation_file_table(metadata)
    init_continuation_graph_table(metadata)


def init_continuation_file_table(metadata, tablename="continuations"):
    """
    Specifies a table that associates chunk faces to a file which
    holds the continuation information for that face.
    """
    columns = [Column("id", Integer, primary_key=True),
               Column("filename", Text),
               Column("facehash", Integer, index=True)]

    return Table(tablename, metadata, *columns)


def init_continuation_graph_table(metadata, tablename="contin_graph"):
    """
    Specifies a table that stores a graph of connected segment continuations
    """
    columns = [Column("id", BigInteger, primary_key=True),
               Column(cn.graph_id1, BigInteger),
               Column(cn.graph_id2, BigInteger)]

    return Table(tablename, metadata, *columns)


def init_idmap_tables(metadata):
    init_idmap_table(metadata, "seg_merge_map", hashed=True)
    init_idmap_table(metadata, "chunked_seg_merge_map", chunked=True)


def init_idmap_table(metadata, tablename, hashed=False, chunked=False):
    """ Specifies a table that holds an id mapping. """
    columns = [Column("id", Integer, primary_key=True),
               Column(cn.src_id, Integer, index=True),
               Column(cn.dst_id, Integer)]

    if hashed:
        columns.append(Column(cn.dst_id_hash, Integer, default=-1))

    if chunked:
        columns.append(Column(cn.chunk_tag, Text))

    return Table(tablename, metadata, *columns)


def init_edge_tables(metadata):
    """
    Specifies three tables that track info about synaptic connections through
    different processing stages
    """
    init_edge_table(metadata, "chunk_edges")
    init_edge_table(metadata, "merged_edges")
    init_final_edge_table(metadata, "final")


def init_edge_table(metadata, tablename, chunked=True):
    """
    Specifies a table that tracks information about synaptic connections.
    """
    columns = [Column("id", Integer, primary_key=True),
               Column(cn.seg_id, Integer),
               Column(cn.presyn_id, BigInteger),
               Column(cn.postsyn_id, BigInteger),
               Column(cn.size, Integer),
               # Anchor points
               Column(cn.presyn_x, Integer),
               Column(cn.presyn_y, Integer),
               Column(cn.presyn_z, Integer),
               Column(cn.postsyn_x, Integer),
               Column(cn.postsyn_y, Integer),
               Column(cn.postsyn_z, Integer),
               # Hash values
               Column(cn.clefthash, Integer, default=-1, index=True),
               Column(cn.partnerhash, Integer, default=-1, index=True)]

    if chunked:
        columns.append(Column(cn.chunk_tag, Text))

    return Table(tablename, metadata, *columns)


def init_final_edge_table(metadata, tablename):
    """
    Specifies a table that holds all of the information about a set of
    synaptic connections, paired 1:1 with synapse segmentations
    """
    return Table(tablename, metadata,
                 Column(cn.seg_id, Integer, primary_key=True),
                 Column(cn.presyn_id, BigInteger),
                 Column(cn.postsyn_id, BigInteger),
                 Column(cn.size, Integer),
                 # Centroid coordinates
                 Column(cn.centroid_x, Float),
                 Column(cn.centroid_y, Float),
                 Column(cn.centroid_z, Float),
                 # Bounding box
                 Column(cn.bbox_bx, Integer),
                 Column(cn.bbox_by, Integer),
                 Column(cn.bbox_bz, Integer),
                 Column(cn.bbox_ex, Integer),
                 Column(cn.bbox_ey, Integer),
                 Column(cn.bbox_ez, Integer),
                 # Anchor points
                 Column(cn.presyn_x, Integer),
                 Column(cn.presyn_y, Integer),
                 Column(cn.presyn_z, Integer),
                 Column(cn.postsyn_x, Integer),
                 Column(cn.postsyn_y, Integer),
                 Column(cn.postsyn_z, Integer),
                 # Hash values
                 Column(cn.clefthash, Integer, default=-1),
                 Column(cn.partnerhash, Integer, default=-1))


def init_overlap_tables(metadata):
    """
    Specifies the tables which track information about amounts of
    overlap between sets of segments.
    """
    init_overlap_table(metadata, "chunk_overlaps", chunked=True)
    init_overlap_table(metadata, "max_overlaps", chunked=False)


def init_overlap_table(metadata, tablename, chunked=True):
    """ Specifies a table that holds an id mapping. """
    columns = [Column("id", Integer, primary_key=True),
               Column(cn.rows, BigInteger),
               Column(cn.cols, BigInteger),
               Column(cn.vals, Integer)]

    if chunked:
        columns.append(Column(cn.chunk_tag, Text))

    return Table(tablename, metadata, *columns)


def drop_db(url, metadata=None):
    """ Deletes a database initialized by init_db. """
    if metadata is None:
        metadata = io.open_db_metadata(url)

    tables = [metadata.tables[t] for t in TABLES if t in metadata.tables]

    return io.drop_db_tables(url, metadata, tables=tables)


def fill_chunks(url, bboxes):
    """
    Fills the chunks table with a list of bboxes. The id of each
    bounding box is the index of the box in the list + 1 (base-0 -> base-1
    indexing).
    """
    dframe = pd.DataFrame([bbox.astuple() for bbox in bboxes])
    dframe.columns = [cn.chunk_bx, cn.chunk_by, cn.chunk_bz,
                      cn.chunk_ex, cn.chunk_ey, cn.chunk_ez]

    tags = [io.fname_chunk_tag(bbox) for bbox in bboxes]
    dframe[cn.chunk_tag] = tags

    dframe.index.name = "id"

    io.write_db_dframe(dframe, url, "chunks")
