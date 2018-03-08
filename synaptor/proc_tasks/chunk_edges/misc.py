#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()


import pandas as pd


from ... import seg_utils


def add_cleft_sizes(edges_dframe, clefts):
    """ Finds the sizes of the cleft segments, adds it to the edges dframe """

    szs = seg_utils.segment_sizes(clefts)

    szs_s = pd.Series(szs, name="size")
    full_df = pd.concat((edges_dframe, szs_s), axis=1)

    return full_df


def add_cleft_locs(edges_dframe, clefts):
    """ 
    Finds the locations of the cleft segments, adds them to the edges dframe
    """

    coms = seg_utils.centers_of_mass(clefts)

    df = pd.DataFrame.from_dict(coms, orient="index")
    df.columns = ["COM_x","COM_y","COM_z"]

    return pd.merge(df, edges_dframe, 
                    left_index=True, right_index=True, 
                    copy=False)
