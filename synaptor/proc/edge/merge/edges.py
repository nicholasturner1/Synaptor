__doc__ = """
Edge consolidation (w/o cleft information)

Nicholas Turner <nturner@cs.princeton.edu>, 2018-9
"""

import pandas as pd

from ...utils import schema as sch


def concat_edge_arr(edge_dframe_arr):

    df = pd.concat(map(lambda x: x.reset_index(), edge_dframe_arr.flat),
                   copy=False, sort=False, axis="index")

    return consolidate_edges(df)


def pick_largest_edges(df, indexname=sch.cleft_id):
    df = df[df[sch.size] == df.groupby([indexname])[sch.size].transform(max)]
    # keeps the first row in the case of a tie (effectively random)
    df = df.drop_duplicates(indexname)

    return df.set_index(indexname)


def merge_to_cleft_df(edge_df, cleft_df):
    # use the cleft_df size column since the
    # edge version might be approximate by downsampling
    sizes = cleft_df[sch.size]
    new_df = pd.merge(cleft_df, edge_df, left_index=True,
                      right_index=True, copy=False)

    new_df[sch.size] = sizes
    new_df.drop([sch.size+"_x", sch.size+"_y"], axis=1, inplace=True)

    return new_df
