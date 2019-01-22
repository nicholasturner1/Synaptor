__doc__ = """
Edge consolidation (w/o cleft information)

Nicholas Turner <nturner@cs.princeton.edu>, 2018-9
"""

import pandas as pd


def consolidate_edge_arr(edge_dframe_arr):

    df = pd.concat(map(lambda x: x.reset_index(), edge_dframe_arr.flat),
                   copy=False, sort=False, axis="index")
    return consolidate_edges(df)


def consolidate_edges(df, indexname="cleft_segid"):
    df = df[df["size"] == df.groupby([indexname])["size"].transform(max)]
    # keeps the first row in the case of a tie (effectively random)
    df = df.drop_duplicates(indexname)
    return df.set_index(indexname)


def merge_to_cleft_df(edge_df, cleft_df):
    sizes = cleft_df["size"] #edge version might be approximate by downsampling
    new_df = pd.merge(cleft_df, edge_df, left_index=True,
                      right_index=True, copy=False)

    new_df["size"] = sizes
    new_df.drop(["size_x","size_y"], axis=1, inplace=True)

    return new_df
