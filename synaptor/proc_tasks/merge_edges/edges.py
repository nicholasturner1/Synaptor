#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import zip
from future import standard_library
standard_library.install_aliases()

__doc__ = """
Edge consolidation (w/o cleft information)

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import pandas as pd


def consolidate_edges(edge_dframe_arr):

    full_dframe = None
    for new_dframe in edge_dframe_arr.flat:

        full_dframe = merge_dframes(new_dframe, full_dframe)

    return full_dframe


def merge_to_cleft_df(edge_df, cleft_df):
    sizes = cleft_df["size"] #edge version might be approximate by downsampling
    new_df = pd.merge(cleft_df, edge_df, left_index=True,
                      right_index=True, copy=False)

    new_df["size"] = sizes
    new_df.drop(columns=["size_x","size_y"], inplace=True)

    return new_df


def merge_dframes(dframe1, dframe2):

    if  dframe1 is None:
        return dframe2
    elif dframe2 is None:
        return dframe1


    segids = find_segs_in_common(dframe1, dframe2)

    if len(segids) == 0:
        return pd.concat((dframe1, dframe2), copy=False)

    larger_in_1, not_larger_in_1 = compare_sizes(dframe1["size"],
                                                 dframe2["size"],
                                                 segids)


    dframe1 = dframe1.drop(not_larger_in_1, axis=0)
    dframe2 = dframe2.drop(larger_in_1,     axis=0)

    return pd.concat((dframe1, dframe2), copy=False)


def find_segs_in_common(dframe1, dframe2):

    segs1 = set(dframe1.index)
    segs2 = set(dframe2.index)

    return list(segs1.intersection(segs2))


def compare_sizes(szs1, szs2, segids):

    segid_szs1 = szs1[segids]
    segid_szs2 = szs2[segids]

    larger_in_1, not_larger_in_1 = [], []

    for (segid, sz1,sz2) in zip(segids, segid_szs1,segid_szs2):

        if sz1 > sz2:
            larger_in_1.append(segid)
        else:
            not_larger_in_1.append(segid)

    return larger_in_1, not_larger_in_1
