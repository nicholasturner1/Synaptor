#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()


import pandas as pd


from ... import seg_utils
from .. import chunk_ccs

SZ_SCHEMA = chunk_ccs.SZ_SCHEMA
CENTROID_SCHEMA = chunk_ccs.CENTROID_SCHEMA

def add_cleft_sizes(edges_dframe, clefts):
    """ Finds the sizes of the cleft segments, adds it to the edges dframe """

    szs = seg_utils.segment_sizes(clefts)

    szs_s = pd.Series((szs[clf] for clf in edges_dframe["cleft_segid"]), 
                      name=SZ_SCHEMA[0])
    full_df = pd.concat((edges_dframe, szs_s), axis=1)

    return full_df


def add_cleft_locs(edges_dframe, clefts):
    """
    Finds the locations of the cleft segments, adds them to the edges dframe
    """

    coms = seg_utils.centers_of_mass(clefts)

    df = pd.DataFrame.from_dict(coms, orient="index")
    df.columns = CENTROID_SCHEMA
    df = df.reset_index()

    return pd.merge(df, edges_dframe,
                    left_on="index", right_on="cleft_segid",
                    copy=False).drop(["index"], axis=1)

def upsample_edge_info(edges_dframe, mip, offset):
    """pass"""

    assert len(offset) == 3, "invalid coordinate offset"

    coord_factor = 2 ** mip

    edges_dframe["presyn_x"] = upsample_col(edges_dframe["presyn_x"],
                                            coord_factor, offset[0])
    edges_dframe["presyn_y"] = upsample_col(edges_dframe["presyn_y"],
                                            coord_factor, offset[1])

    edges_dframe["postsyn_x"] = upsample_col(edges_dframe["postsyn_x"],
                                             coord_factor, offset[0])
    edges_dframe["postsyn_y"] = upsample_col(edges_dframe["postsyn_y"],
                                             coord_factor, offset[0])

    return edges_dframe


def upsample_col(column, coord_factor, offset):
    #Current ngl convention is to scale offsets too, only need to scale
    return column * coord_factor
