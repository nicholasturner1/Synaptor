""" Resolving edge assignments across chunks. """

import pandas as pd

from ... import colnames as cn


def pick_largest_edges_arr(edge_dframe_arr):

    df = pd.concat(map(lambda x: x.reset_index(), edge_dframe_arr.flat),
                   copy=False, sort=False, axis="index")

    return pick_largest_edges(df)


def pick_largest_edges(df, indexname=cn.seg_id):
    df = df[df[cn.size] == df.groupby([indexname])[cn.size].transform(max)]

    # keeps the first row in the case of a tie (effectively random)
    df = df.drop_duplicates(indexname)

    return df.set_index(indexname)


def merge_to_cleft_df(edge_df, cleft_df):
    # use the cleft_df size column since the
    # edge version might be approximate by downsampling
    sizes = cleft_df[cn.size]
    new_df = pd.merge(cleft_df, edge_df, left_index=True,
                      right_index=True, copy=False)

    new_df[cn.size] = sizes
    new_df.drop([cn.size+"_x", cn.size+"_y"], axis=1, inplace=True)

    return new_df
