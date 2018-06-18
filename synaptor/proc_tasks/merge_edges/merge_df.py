#!/usr/bin/env python3
__doc__ = """
Merging Cleft Info Dataframes with Edge Information ("Full" Dataframes)

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import pandas as pd

from ...types import bbox
from .. import chunk_ccs
from .. import utils


RECORD_KEYS = ["presyn_segid","presyn_sz","presyn_wt",
               "presyn_x","presyn_y","presyn_z",
               "postsyn_segid","postsyn_sz","postsyn_wt",
               "postsyn_x","postsyn_y","postsyn_z", "size"]
BASIN_KEYS = ["presyn_basin","postsyn_basin"]

SZ_SCHEMA = chunk_ccs.SZ_SCHEMA
CENTROID_SCHEMA = chunk_ccs.CENTROID_SCHEMA
BBOX_SCHEMA = chunk_ccs.BBOX_SCHEMA


def merge_full_df(full_info_df, id_map):
    return utils.merge_info_df(full_info_df, id_map, merge_full_records)


def merge_full_records(record1, record2):

    record_dict1 = unwrap_row(record1)
    record_dict2 = unwrap_row(record2)

    #Pick the aux params for the larger cleft
    if record_dict1[SZ_SCHEMA[0]] > record_dict2[SZ_SCHEMA[0]]:
        base_dict = record_dict1
    else:
        base_dict = record_dict2

    sz1, sz2   = record_dict1[SZ_SCHEMA[0]], record_dict2[SZ_SCHEMA[0]]
    com1, com2 = record_dict1["COM"],  record_dict2["COM"]
    bb1, bb2   = record_dict1["BBOX"], record_dict2["BBOX"]

    base_dict["size"] = sz1 + sz2
    base_dict["COM"]  = utils.weighted_avg(com1, sz1, com2, sz2)
    base_dict["BBOX"] = bb1.merge(bb2)

    return wrap_row(base_dict)


def unwrap_row(df_row):

    com = tuple(df_row[col] for col in CENTROID_SCHEMA)

    bb_b = tuple(df_row[col] for col in BBOX_SCHEMA[:3])
    bb_e = tuple(df_row[col] for col in BBOX_SCHEMA[3:])
    bb = bbox.BBox3d(bb_b, bb_e)

    complete_row = { k : df_row[k] for k in RECORD_KEYS }
    complete_row["COM"]  = com
    complete_row["BBOX"] = bb
    #Adding watershed basins if they're in the row
    for k in BASIN_KEYS:
        if k in df_row:
            complete_row[k] = df_row[k]

    return complete_row


def wrap_row(row_dict):

    new_row = { k : row_dict[k] for k in RECORD_KEYS }

    (new_row[CENTROID_SCHEMA[0]],
     new_row[CENTROID_SCHEMA[1]],
     new_row[CENTROID_SCHEMA[2]]) = row_dict["COM"]
    (new_row[BBOX_SCHEMA[0]],
     new_row[BBOX_SCHEMA[1]],
     new_row[BBOX_SCHEMA[2]]) = row_dict["BBOX"].min()
    (new_row[BBOX_SCHEMA[3]],
     new_row[BBOX_SCHEMA[4]],
     new_row[BBOX_SCHEMA[5]]) = row_dict["BBOX"].max()

    #Adding watershed basins if they're in the row
    for k in BASIN_KEYS:
        if k in row_dict:
            new_row[k] = row_dict[k]

    return new_row
