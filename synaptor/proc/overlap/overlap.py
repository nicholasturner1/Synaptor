"""
Segment Overlap
"""

import pandas as pd
from scipy import sparse

from ... import seg_utils
from .. import colnames as cn


count_overlaps = seg_utils.count_overlaps


def find_max_overlaps(overlap_mat):

    maxima = {}
    max_overlaps = {}
    for (i, j, v) in zip(overlap_mat.row, overlap_mat.col, overlap_mat.data):
        if (i not in maxima) or (v > maxima[i]):
            maxima[i] = v
            max_overlaps[i] = j

    rs = list(max_overlaps.keys())
    cs = list(max_overlaps[k] for k in rs)
    vs = list(maxima[k] for k in rs)

    return sparse.coo_matrix((vs, (rs, cs)))


def convert_to_dict(overlap_mat):
    """
    Converts an overlap matrix to a dictionary. Assumes that each
    seg overlaps with only one partner.
    """
    return dict(zip(overlap_mat.row, overlap_mat.col))


def add_overlapping_seg(dframe, seg, base_seg, colname=cn.ovl_segid):
    """
    Adds the maximally overlapping base segid as a column to a seginfo DataFrame
    """
    overlaps = count_overlaps(seg, base_seg, orig_ids=True)[0]
    max_overlaps = convert_to_dict(find_max_overlaps(overlaps))

    overlap_df = pd.DataFrame.from_dict(
                     max_overlaps, orient="index", columns=[colname])

    new_dframe = pd.concat((dframe, overlap_df), axis=1)
    new_dframe.index.name = dframe.index.name

    return new_dframe
