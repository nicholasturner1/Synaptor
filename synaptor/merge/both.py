#!/usr/bin/env python3

import math, operator

import numpy as np
import scipy.spatial
import pandas as pd

from . import utils
from .. import bbox


aux_record_keys = ["presyn_seg","presyn_sz","presyn_wt",
                   "presyn_x","presyn_y","presyn_z",
                   "postsyn_seg","postsyn_sz","postsyn_wt",
                   "postsyn_x","postsyn_y","postsyn_z", "size"]


def merge_dframes(cleft_df, edge_df):
    new_df = pd.merge(cleft_df, edge_df, left_index=True, right_index=True, copy=False)

    new_df["size"] = new_df["size_x"]
    new_df.drop(columns=["size_x","size_y"], inplace=True)

    return new_df


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

        conn_comps.extend(utils.find_connected_components(cleft_pairs))

    return utils.make_id_map(conn_comps)


def find_pairs_within_dist(ids, coords, dist_thr, res):

    coord_array = np.vstack(coords) * res

    dists = scipy.spatial.distance.pdist(coord_array)
    under_thr = np.nonzero(dists < dist_thr)[0]

    pairs = [row_col_from_condensed_index(len(ids),i) for i in under_thr]

    return list(map(lambda tup: (ids[tup[0]], ids[tup[1]]), pairs))


def match_clefts_by_partners(cleft_info_df):

    cleft_by_partners = {}
    for (cid, pre, post, x,y,z) in zip(cleft_info_df.index,
                                       cleft_info_df.presyn_seg,
                                       cleft_info_df.postsyn_seg,
                                       cleft_info_df.COM_x,
                                       cleft_info_df.COM_y,
                                       cleft_info_df.COM_z):

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
    return utils.merge_info_df(full_info_df, id_map, merge_full_records)


def merge_full_records(record1, record2):

    record_dict1 = unwrap_row(record1)
    record_dict2 = unwrap_row(record2)

    #Pick the aux params for the larger cleft
    if record_dict1["size"] > record_dict2["size"]:
        base_dict = record_dict1
    else:
        base_dict = record_dict2

    sz1, sz2   = record_dict1["size"], record_dict2["size"]
    com1, com2 = record_dict1["COM"],  record_dict2["COM"]
    bb1, bb2   = record_dict1["BBOX"], record_dict2["BBOX"]

    base_dict["size"] = sz1 + sz2
    base_dict["COM"]  = utils.weighted_avg(com1, sz1, com2, sz2)
    base_dict["BBOX"] = bb1.merge(bb2)

    return wrap_row(base_dict)


def unwrap_row(df_row):

    com = (df_row["COM_x"], df_row["COM_y"], df_row["COM_z"])

    bb = bbox.BBox3d((df_row["BBOX_bx"], df_row["BBOX_by"], df_row["BBOX_bz"]),
                     (df_row["BBOX_ex"], df_row["BBOX_ey"], df_row["BBOX_ez"]))

    complete_row = { k : df_row[k] for k in aux_record_keys }
    complete_row["COM"]  = com
    complete_row["BBOX"] = bb

    return complete_row


def wrap_row(row_dict):
    
    new_row = { k : row_dict[k] for k in aux_record_keys }

    new_row["COM_x"],new_row["COM_y"],new_row["COM_z"] = row_dict["COM"]
    (new_row["BBOX_bx"], 
     new_row["BBOX_by"], 
     new_row["BBOX_bz"]) = row_dict["BBOX"].min()
    (new_row["BBOX_ex"], 
     new_row["BBOX_ey"], 
     new_row["BBOX_ez"]) = row_dict["BBOX"].max()

    return new_row

