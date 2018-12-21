__doc__ = """
Edge info DataFrame IO for processing tasks
"""

from sqlalchemy import select, and_
from sqlalchemy.sql.expression import true

from ... import io
from . import cleftinfo
from . import edgeinfo
from . import initdb


# FILE STORAGE CONVENTIONS
FINAL_FULL_DF_FNAME = "final.df"

# This needs to match volumns in `initdb.py`
EDGE_INFO_COLUMNS = edgeinfo.EDGE_INFO_COLUMNS
CLEFT_INFO_COLUMNS = cleftinfo.CLEFT_INFO_COLUMNS
NULL_CHUNK_ID = initdb.NULL_CHUNK_ID


def read_full_info(proc_url):
    """
    Reads the info dataframe with clefts and edges combined
    from a processing directory
    """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        clefts, edges = metadata.tables["clefts"], metadata.tables["edges"]
        columns = list(clefts.c[name] for name in CLEFT_INFO_COLUMNS)
        columns += list(clefts.c[name] for name in EDGE_INFO_COLUMNS)
        statement = select(columns).where(and_(
                                   clefts.c.cleft_segid == edges.c.cleft_segid,
                                   clefts.c.final == true(),
                                   edges.c.final == true()))
        return io.read_db_dframe(proc_url, statement, index_col="cleft_segid")

    else:
        return io.read_dframe(proc_url, FINAL_FULL_DF_FNAME)


def write_full_info(dframe, proc_url):
    """
    Writes the info dataframe with clefts and edges combined
    to a processing directory
    """
    if io.is_db_url(proc_url):
        dframe = dframe.reset_index()
        cleft_info = dframe[CLEFT_INFO_COLUMNS]
        edge_info = dframe[EDGE_INFO_COLUMNS]

        cleft_info["chunk_id"] = NULL_CHUNK_ID
        cleft_info["merged"] = True
        cleft_info["final"] = True

        edge_info["chunk_id"] = NULL_CHUNK_ID
        edge_info["merged"] = True
        edge_info["final"] = True

        io.write_db_dframes([cleft_info, edge_info], proc_url,
                            ["clefts", "edges"], index=False)

    else:
        io.write_dframe(dframe, proc_url, FINAL_FULL_DF_FNAME)
