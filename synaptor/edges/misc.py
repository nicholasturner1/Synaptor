#!/usr/bin/env python3


import pandas as pd


from .. import seg_utils
from .. import clefts


def add_seg_size(edges_dframe, clefts):
    """ Finds the sizes of the cleft segments, adds it to the edges dframe """

    szs = seg_utils.segment_sizes(clefts)

    szs_s = pd.Series(szs, name="size")
    full_df = pd.concat((edges_dframe, szs_s), axis=1)

    return full_df


def add_seg_locs(edges_dframe, clefts):
    """ 
    Finds the locations of the cleft segments, adds them to the edges dframe
    """

    coms = seg_utils.centers_of_mass(clefts)

    df = pd.DataFrame.from_dict(coms, orient="index")
    df.columns = ["COM_x","COM_y","COM_z"]

    return pd.merge(df, edges_dframe, 
                    left_index=True, right_index=True, 
                    copy=False)
