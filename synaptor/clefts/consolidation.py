#!/usr/bin/env python3

import copy, itertools
import numpy as np
import pandas as pd
import igraph


from . import continuations
from .. import bbox


def consolidate_info_arr(seg_info_arr):

    chunk_id_maps = empty_info_array(seg_info_arr.shape)
    full_df = None
    next_id = 1

    for (x,y,z) in np.ndindex(seg_info_arr.shape):

        new_df = seg_info_arr[x,y,z]
        chunk_id_maps[x,y,z], next_id = new_id_map(new_df, next_id)

        if full_df is None:
            full_df = remap_ids(new_df, chunk_id_maps[x,y,z])
        else:
            full_df = pd.concat((full_df,
                                remap_ids(new_df, chunk_id_maps[x,y,z])),
                                copy=False)

    return full_df, chunk_id_maps


def new_id_map(df, next_id):
    segids = df.index.tolist()

    id_map = { segid : n for (segid,n) in
               zip(segids,range(next_id, next_id+len(segids)))}

    return id_map, next_id+len(segids)


def remap_ids(df, id_map):
    df.rename(id_map, inplace=True)
    return df


def empty_info_array(shape):
    size = np.prod(shape)
    return np.array([None for _ in range(size)]).reshape(shape)


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
    ccs = find_connected_components(matches)
    return  make_id_map(ccs)


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


def find_connected_components(matches):
    
    all_ids = list(set(itertools.chain(*matches)))
    vertex_mapping = { segid: i for (i,segid) in enumerate(all_ids) }

    g = igraph.Graph(len(all_ids))
    g.vs["ids"] = all_ids

    mapped_edges = map(lambda x: (vertex_mapping[x[0]],vertex_mapping[x[1]]),
                       matches)

    g.add_edges(mapped_edges)

    vertex_ccs = g.components()

    orig_ccs = [g.vs[cc]["ids"] for cc in vertex_ccs]

    return orig_ccs


def make_id_map(ccs):

    mapping = {}

    for cc in ccs:
        target = min(cc)

        for i in cc:
            mapping[i] = target

    return mapping


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


def merge_cont_info(full_seg_info_df, cont_id_map):

    to_drop = []
    for (k,v) in cont_id_map.items():
        if k == v:
            continue

        k_sz, k_com, k_bbox = unwrap_row(full_seg_info_df.loc[k])
        v_sz, v_com, v_bbox = unwrap_row(full_seg_info_df.loc[v])

        sz = k_sz + v_sz
        com = weighted_sum(k_com, k_sz, v_com, v_sz)
        bb = k_bbox.merge(v_bbox)

        full_seg_info_df.loc[v] = wrap_row(sz, com, bb)
        to_drop.append(k)

    full_seg_info_df.drop(to_drop, inplace=True)

    return full_seg_info_df


def unwrap_row(df_row):

    sz = df_row["sizes"]
    
    com = (df_row["COM_x"], df_row["COM_y"], df_row["COM_z"])

    bb = bbox.BBox3d((df_row["BBOX_bx"], df_row["BBOX_by"], df_row["BBOX_bz"]),
                     (df_row["BBOX_ex"], df_row["BBOX_ey"], df_row["BBOX_ez"]))

    return sz, com, bb


def wrap_row(sz, com, bb):
    return list(map(int, (sz, *com, *bb.astuple())))


def weighted_sum(com1, sz1, com2, sz2):
    
    frac1 = sz1 / (sz1+sz2)
    frac2 = sz2 / (sz1+sz2)

    h1 = (com1[0]*frac1, com1[1]*frac1, com1[2]*frac1)
    h2 = (com2[0]*frac2, com2[2]*frac2, com2[2]*frac2)

    return (h1[0]+h2[0], h1[1]+h2[1], h1[2]+h2[2])


def enforce_size_threshold(seg_info_df, size_thr):
    violations = seg_info_df[seg_info_df.sizes < size_thr].index.tolist()
    seg_info_df.drop(violations, inplace=True)

    return {v : 0 for v in violations}
