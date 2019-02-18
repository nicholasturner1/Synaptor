__doc__ = """
Merging Cleft Info Dataframes

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import itertools

from ....types import bbox
from ... import utils
from ...utils import schema as sch


def merge_cleft_df(cleft_info_df, id_map):
    return utils.merge_info_df(cleft_info_df, id_map, merge_cleft_rows)


def merge_cleft_rows(row1, row2):

    sz1, com1, bbox1 = unwrap_row(row1)
    sz2, com2, bbox2 = unwrap_row(row2)

    sz = sz1 + sz2
    com = utils.weighted_avg(com1, sz1, com2, sz2)
    bb = bbox1.merge(bbox2)

    return wrap_row(sz, com, bb)


def unwrap_row(df_row):

    sz = df_row[sch.size]

    com = tuple(df_row[col] for col in sch.centroid_cols)

    bb_b = tuple(df_row[col] for col in sch.bbox_cols[:3])
    bb_e = tuple(df_row[col] for col in sch.bbox_cols[3:])
    bb = bbox.BBox3d(bb_b, bb_e)

    return sz, com, bb


def wrap_row(sz, com, bb):
    return dict(zip(itertools.chain([sch.size],
                                    sch.centroid_cols,
                                    sch.bbox_cols),
                    map(int, itertools.chain((sz,), com, bb.astuple()))))


def enforce_size_threshold(cleft_info_df, size_thr):
    """Finds a mapping that removes clefts under the size threshold"""
    violations = cleft_info_df[cleft_info_df[sch.size] < size_thr].index
    cleft_info_df.drop(violations.tolist(), inplace=True)

    return {v: 0 for v in violations}