#!/usr/bin/env python3

import numpy as np
import pandas as pd

from . import utils
from . import continuations
from .. import bbox


def consolidate_cleft_info_arr(cleft_info_arr):
    """ Assigns new ids to every cleft segment """

    chunk_id_maps = utils.empty_obj_array(cleft_info_arr.shape)
    full_df = None
    next_id = 1

    for (x,y,z) in np.ndindex(cleft_info_arr.shape):

        new_df = cleft_info_arr[x,y,z]
        chunk_id_maps[x,y,z], next_id = new_id_map(new_df, next_id)

        if full_df is None:
            full_df = remap_ids(new_df, chunk_id_maps[x,y,z])
        else:
            full_df = pd.concat((full_df,
                                remap_ids(new_df, chunk_id_maps[x,y,z])),
                                copy=False)

    return full_df, chunk_id_maps


def new_id_map(df, next_id):
    """ Creates a new id for each record in df, starting with next_id """

    segids = df.index.tolist()

    id_map = { segid : n for (segid,n) in
               zip(segids,range(next_id, next_id+len(segids)))}

    return id_map, next_id+len(segids)


def remap_ids(df, id_map):
    """ Remaps the index ids of a dataframe """
    df.rename(id_map, inplace=True)
    return df


def apply_chunk_id_maps(continuation_arr, chunk_id_maps):

    for (c_dict, id_map) in zip(continuation_arr.flat, chunk_id_maps.flat):
        apply_id_map(c_dict, id_map)

    return continuation_arr


def apply_id_map(cont_dict, id_map):

    for (face,conts) in cont_dict.items():
        for continuation in conts:
            continuation.segid = id_map[continuation.segid]


def merge_connected_continuations(continuation_arr):

    matches = find_connected_continuations(continuation_arr)
    ccs = utils.find_connected_components(matches)
    return  utils.make_id_map(ccs)


def find_connected_continuations(continuation_arr):

    sizes   = continuation_arr.shape
    matches = []

    for index in np.ndindex(sizes):

        for face in continuations.Face.all_faces():

            #bounds checking
            if face.hi_index and index[face.axis] == sizes[face.axis] - 1:
                continue
            if not face.hi_index and index[face.axis] == 0:
                continue


            index_to_check = list(index)
            if face.hi_index:
                index_to_check[face.axis] += 1
            else:
                index_to_check[face.axis] -= 1
            index_to_check = tuple(index_to_check)

            conts_here  = continuation_arr[index][face]
            conts_there = continuation_arr[index_to_check][face.opposite()]

            new_matches = match_continuations(conts_here, conts_there)

            matches.extend(new_matches)

    return matches


def match_continuations(conts1, conts2):

    arr_to_row_set = lambda arr: set(tuple(row) for row in arr)
    voxel_sets1 = { c.segid : arr_to_row_set(c.face_coords) for c in conts1 }
    voxel_sets2 = { c.segid : arr_to_row_set(c.face_coords) for c in conts2 }

    matches = []
    for (segid1, voxel_set1) in voxel_sets1.items():
        for (segid2, voxel_set2) in voxel_sets2.items():

            if len(voxel_set1.intersection(voxel_set2)):
                matches.append((segid1, segid2))

    return matches


def update_chunk_id_maps(chunk_id_maps, cont_id_map):

    for mapping in chunk_id_maps.flat:
        for (k,v) in mapping.items():
            mapping[k] = cont_id_map.get(v,v)

    return chunk_id_maps


def merge_cleft_df(cleft_info_df, id_map):
    return utils.merge_info_df(cleft_info_df, id_map, merge_cleft_rows)


def merge_cleft_rows(row1, row2):

    sz1, com1, bbox1 = unwrap_row(row1)
    sz2, com2, bbox2 = unwrap_row(row2)

    sz  = sz1 + sz2
    com = utils.weighted_avg(com1, sz1, com2, sz2)
    bb  = bbox1.merge(bbox2)

    return wrap_row(sz, com, bb)
     

def unwrap_row(df_row):

    sz = df_row["size"]

    com = (df_row["COM_x"], df_row["COM_y"], df_row["COM_z"])

    bb = bbox.BBox3d((df_row["BBOX_bx"], df_row["BBOX_by"], df_row["BBOX_bz"]),
                     (df_row["BBOX_ex"], df_row["BBOX_ey"], df_row["BBOX_ez"]))

    return sz, com, bb


def wrap_row(sz, com, bb):
    return dict(zip(["size","COM_x","COM_y","COM_z",
                     "BBOX_bx","BBOX_by","BBOX_bz",
                     "BBOX_ex","BBOX_ey","BBOX_ez"],
                    map(int, (sz, *com, *bb.astuple()))))


def enforce_size_threshold(seg_info_df, size_thr):
    violations = seg_info_df[seg_info_df["size"] < size_thr].index.tolist()
    seg_info_df.drop(violations, inplace=True)

    return {v : 0 for v in violations}


def update_id_map(map1, map2):

    for (k,v) in map1.items():
        map1[k] = map2.get(v,v)

    return map1

