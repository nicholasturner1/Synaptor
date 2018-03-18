#!/usr/bin/env python3
__doc__ = """
Chunk CCs misc
Only a function to make a DataFrame out of the results at the moment
"""

import itertools

import pandas as pd


SZ_SCHEMA = ["size"]
CENTROID_SCHEMA = ["centroid_x","centroid_y","centroid_z"]
BBOX_SCHEMA = ["BBOX_bx","BBOX_by","BBOX_bz",
               "BBOX_ex","BBOX_ey","BBOX_ez"]


def make_cleft_info_dframe(centers, sizes, bboxes):
    """
    Collects three dictionaries describing the clefts of a volume
    into a DataFrame
    """

    assert len(centers) == len(sizes) == len(bboxes)

    if len(centers) == 0:
        return empty_cleft_df()

    #Cleft Size
    assert len(SZ_SCHEMA) == 1, "SZ_SCHEMA updated without adapting code"
    sizes_df = pd.Series(sizes, name=SZ_SCHEMA[0])

    #Cleft Centroid
    centers_df = dframe_from_tuple_dict(centers, CENTROID_SCHEMA)

    #Cleft Bounding Boxes
    bbox_tuples = { k : bbox.astuple() for (k,bbox) in bboxes.items() }
    bbox_df = dframe_from_tuple_dict(bbox_tuples, BBOX_SCHEMA)

    return pd.concat((sizes_df, centers_df, bbox_df), axis=1)


def empty_cleft_df():
    """Creates an empty DataFrame with the proper columns"""
    return pd.DataFrame({k : []
                         for k in itertools.chain(SZ_SCHEMA,
                                                  CENTROID_SCHEMA,
                                                  BBOX_SCHEMA) })


def dframe_from_tuple_dict(tuple_dict, colnames):
    """ Makes a DataFrame from a dictionary of tuples """
    df = pd.DataFrame.from_dict(tuple_dict, orient="index")
    df.columns = colnames

    return df
