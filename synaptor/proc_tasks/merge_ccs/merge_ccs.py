#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import dict
from builtins import zip
from builtins import map
from builtins import range
from future import standard_library
standard_library.install_aliases()


import itertools

import numpy as np
import pandas as pd

from ...types import continuation
from ...types import bbox
from .. import chunk_ccs
from . import misc


SZ_SCHEMA = chunk_ccs.SZ_SCHEMA
CENTROID_SCHEMA = chunk_ccs.CENTROID_SCHEMA
BBOX_SCHEMA = chunk_ccs.BBOX_SCHEMA


def consolidate_cleft_info_arr(cleft_info_arr):
    """ Assigns new ids to every cleft segment """

    chunk_id_maps = misc.empty_obj_array(cleft_info_arr.shape)
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
    """ Applies id maps to each set of continuations """
    for (c_dict, id_map) in zip(continuation_arr.flat, chunk_id_maps.flat):
        apply_id_map(c_dict, id_map)

    return continuation_arr


def apply_id_map(cont_dict, id_map):
    """
    Applies an id map to a set of continuations organized in
    dictionaries: face -> [continuations]
    """
    for (face,conts) in cont_dict.items():
        for continuation in conts:
            continuation.segid = id_map[continuation.segid]


def merge_connected_continuations(continuation_arr):
    """
    Finds an id mapping to merge the continuations which match across faces
    """

    matches = find_connected_continuations(continuation_arr)
    ccs = misc.find_connected_components(matches)
    return misc.make_id_map(ccs)


def find_connected_continuations(continuation_arr, max_face_shape=(1024,1024)):
    """
    Finds the edges of a graph which describes the continuation connectivity
    """

    sizes   = continuation_arr.shape
    face_checked = np.zeros((3,) + continuation_arr.shape, dtype=np.bool)
    matches = []

    for index in np.ndindex(sizes):

        for face in continuation.Face.all_faces():

            #bounds checking
            if face.hi_index and index[face.axis] == sizes[face.axis] - 1:
                continue
            if not face.hi_index and index[face.axis] == 0:
                continue

            #if we've processed the other side already
            if face_checked[(face.axis,)+index]:
                continue
            else:
                face_checked[(face.axis,)+index] = True

            index_to_check = list(index)
            if face.hi_index:
                index_to_check[face.axis] += 1
            else:
                index_to_check[face.axis] -= 1
            index_to_check = tuple(index_to_check)
            face_checked[(face.axis,)+index_to_check] = True

            conts_here  = continuation_arr[index][face]
            conts_there = continuation_arr[index_to_check][face.opposite()]

            new_matches = match_continuations(conts_here, conts_there, 
                                              face_shape=max_face_shape)

            matches.extend(new_matches)


    return matches


def match_continuations(conts1, conts2, face_shape=(1024,1024)):
    """ Determines which continuations match within the two lists """

    face1 = reconstruct_face(conts1, shape=face_shape)
    face2 = reconstruct_face(conts2, shape=face_shape)

    intersection_mask = np.logical_and(face1 !=0, face2 !=0)

    matches1 = face1[intersection_mask]
    matches2 = face2[intersection_mask]

    return list(set(zip(matches1,matches2)))


def reconstruct_face(continuations, shape=(1024,1024)):

    face = np.zeros(shape, dtype=np.uint32)

    for c in continuations:
        face[tuple(c.face_coords.T)] = c.segid

    return face


def update_chunk_id_maps(chunk_id_maps, cont_id_map):
    """
    Creates a new chunkwise id map as if cont_id_map is applied after each
    chunk id map
    """

    for mapping in chunk_id_maps.flat:
        for (k,v) in mapping.items():
            mapping[k] = cont_id_map.get(v,v)

    return chunk_id_maps


#I can hopefully refactor the code below soon, it's a bit strange...
def merge_cleft_df(cleft_info_df, id_map):
    return misc.merge_info_df(cleft_info_df, id_map, merge_cleft_rows)


def merge_cleft_rows(row1, row2):

    sz1, com1, bbox1 = unwrap_row(row1)
    sz2, com2, bbox2 = unwrap_row(row2)

    sz  = sz1 + sz2
    com = misc.weighted_avg(com1, sz1, com2, sz2)
    bb  = bbox1.merge(bbox2)

    return wrap_row(sz, com, bb)


def unwrap_row(df_row):

    sz = df_row[SZ_SCHEMA[0]]

    com = tuple(df_row[col] for col in CENTROID_SCHEMA)

    bb_b = tuple(df_row[col] for col in BBOX_SCHEMA[:3])
    bb_e = tuple(df_row[col] for col in BBOX_SCHEMA[3:])
    bb = bbox.BBox3d(bb_b, bb_e)

    return sz, com, bb


def wrap_row(sz, com, bb):
    return dict(zip(itertools.chain(SZ_SCHEMA, CENTROID_SCHEMA, BBOX_SCHEMA),
                    map(int, itertools.chain((sz,), com, bb.astuple()))))


def enforce_size_threshold(cleft_info_df, size_thr):
    """Finds a mapping that removes clefts under the size threshold"""
    violations = cleft_info_df[cleft_info_df[SZ_SCHEMA[0]] < size_thr].index
    cleft_info_df.drop(violations.tolist(), inplace=True)

    return {v : 0 for v in violations}


def update_id_map(map1, map2):

    for (k,v) in map1.items():
        map1[k] = map2.get(v,v)

    return map1
