#!/usr/bin/env python3
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
from builtins import int
from builtins import map
from future import standard_library
standard_library.install_aliases()

__doc__ = """

"""

import math, operator

import numpy as np
import scipy.spatial
import pandas as pd

from ...types import bbox
from .. import chunk_ccs
from . import misc


RECORD_KEYS = ["presyn_segid","presyn_sz","presyn_wt",
               "presyn_x","presyn_y","presyn_z",
               "postsyn_segid","postsyn_sz","postsyn_wt",
               "postsyn_x","postsyn_y","postsyn_z", "size"]
BASIN_KEYS = ["presyn_basin","postsyn_basin"]

SZ_SCHEMA = chunk_ccs.SZ_SCHEMA
CENTROID_SCHEMA = chunk_ccs.CENTROID_SCHEMA
BBOX_SCHEMA = chunk_ccs.BBOX_SCHEMA


def merge_duplicate_clefts(full_info_df, dist_thr, res):

    cleft_by_partners = match_clefts_by_partners(full_info_df)

    conn_comps = []

    for cleft_list in cleft_by_partners.values():

        if len(cleft_list) == 1:
            continue

        cleft_ids = list(map(operator.itemgetter(0), cleft_list))
        cleft_coords = list(map(operator.itemgetter(1), cleft_list))

        cleft_pairs = find_pairs_within_dist(cleft_ids, cleft_coords,
                                             dist_thr, res)

        conn_comps.extend(misc.find_connected_components(cleft_pairs))

    return misc.make_id_map(conn_comps)


def find_pairs_within_dist(ids, coords, dist_thr, res):

    coord_array = np.vstack(coords) * res

    dists = scipy.spatial.distance.pdist(coord_array)
    under_thr = np.nonzero(dists < dist_thr)[0]

    pairs = [row_col_from_condensed_index(len(ids),i) for i in under_thr]

    return list(map(lambda tup: (ids[tup[0]], ids[tup[1]]), pairs))


def match_clefts_by_partners(cleft_info_df):

    cleft_by_partners = {}
    for (cid, pre, post, x,y,z) in zip(cleft_info_df.index,
                                       cleft_info_df.presyn_segid,
                                       cleft_info_df.postsyn_segid,
                                       cleft_info_df.centroid_x,
                                       cleft_info_df.centroid_y,
                                       cleft_info_df.centroid_z):

        partners = (pre,post)

        if partners not in cleft_by_partners:
            cleft_by_partners[partners] = [ (cid, (x,y,z)) ]
        else:
            cleft_by_partners[partners].append( (cid,(x,y,z)) )

    return cleft_by_partners


def row_col_from_condensed_index(d,i):
    #https://stackoverflow.com/questions/5323818/condensed-matrix-function-to-find-pairs
    b = 1 -2*d
    x = math.floor((-b - math.sqrt(b**2 - 8*i))/2)
    y = i + x*(b + x + 2)/2 + 1
    return (x,int(y))


def merge_full_df(full_info_df, id_map):
    return misc.merge_info_df(full_info_df, id_map, merge_full_records)


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
    base_dict["COM"]  = misc.weighted_avg(com1, sz1, com2, sz2)
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
