"""
Misc Functionality

Only a function to make a DataFrame out of the results at the moment
"""

import itertools

import pandas as pd

from .. import colnames as cn


def make_seg_info_dframe(centers, sizes, bboxes, index_name=cn.seg_id):
    """
    Collects the three dictionaries describing the segments of a volume
    into a DataFrame
    """
    assert len(centers) == len(sizes) == len(bboxes), "mismatched inputs"

    if len(centers) == 0:
        return empty_cleft_df(index_name)

    # Segment Size
    sizes_df = pd.Series(sizes, name=cn.size)

    # Segment Centroid
    centers_df = dframe_from_tuple_dict(centers, cn.centroid_cols)

    # Segment Bounding Boxes
    bbox_tuples = {k: bbox.astuple() for (k, bbox) in bboxes.items()}
    bbox_df = dframe_from_tuple_dict(bbox_tuples, cn.bbox_cols)

    df = pd.concat((sizes_df, centers_df, bbox_df), axis=1)
    df.index.name = index_name

    return df


def empty_cleft_df(index_name=cn.seg_id):
    """Creates an empty DataFrame with the proper columns"""
    columns = itertools.chain([cn.size], cn.centroid_cols, cn.bbox_cols)

    df = pd.DataFrame({k: [] for k in columns})
    df.index.name = index_name

    return df


def dframe_from_tuple_dict(tuple_dict, colnames):
    """ Makes a DataFrame from a dictionary of tuples """
    df = pd.DataFrame.from_dict(tuple_dict, orient="index")
    df.columns = colnames

    return df
