#!/usr/bin/env python3
__doc__ = """
Connected Component ID management

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import numpy as np
import pandas as pd

from ...types import continuation


def consolidate_cleft_info_arr(cleft_info_arr):
    """ Assigns new ids to every cleft segment """

    #init
    #full_df = None
    chunk_id_maps = empty_obj_array(cleft_info_arr.shape)
    df_parts = []
    next_id = 1

    for (x,y,z) in np.ndindex(cleft_info_arr.shape):

        new_df = cleft_info_arr[x,y,z]
        chunk_id_maps[x,y,z], next_id = new_id_map(new_df, next_id)

        df_parts.append(remap_ids(new_df, chunk_id_maps[x,y,z]))
        #if full_df is None:
        #    full_df = remap_ids(new_df, chunk_id_maps[x,y,z])
        #else:
        #    full_df = pd.concat((full_df,
        #                        remap_ids(new_df, chunk_id_maps[x,y,z])),
        #                        copy=False)

    full_df = pd.concat(df_parts, copy=False)

    return full_df, chunk_id_maps


def empty_obj_array(shape):
    size = np.prod(shape)
    return np.array([None for _ in range(size)]).reshape(shape)


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


def update_chunk_id_maps(chunk_id_maps, cont_id_map):
    """
    Creates a new chunkwise id map as if cont_id_map is applied after each
    chunk id map
    """

    for mapping in chunk_id_maps.flat:
        for (k,v) in mapping.items():
            mapping[k] = cont_id_map.get(v,v)

    return chunk_id_maps
