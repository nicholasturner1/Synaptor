#!/usr/bin/env python3


import pandas as pd


from .. import seg_utils


def add_seg_size(edges_dframe, clefts):
    """ Finds the sizes of the cleft segments, adds it to the edges dframe """

    szs = seg_utils.segment_sizes(clefts)

    szs_s = pd.Series(szs, name="size")
    full_df = pd.concat((edges_dframe, szs_s), axis=1)

    return full_df
