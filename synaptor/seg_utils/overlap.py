from collections import Counter

import numpy as np
from scipy import sparse

from . import describe
from . import _relabel


def count_overlaps(seg1, seg2):
    """
    Computing an overlap matrix,

    Count the overlapping voxels for each pair of overlapping
    objects. Returns a scipy.sparse matrix

    Args:
        seg1 (3darray): A volume segmentation.
        seg2 (3darray): Another volume segmentation.

    Returns:
        scipy.sparse.coo_matrix: A representation of the overlaps
        1darray: The :param: seg1 ids represented by each row.
        1darray: The :param: seg2 ids represented by each column.
    """

    seg1_ids = describe.nonzero_unique_ids(seg1)
    seg2_ids = describe.nonzero_unique_ids(seg2)

    seg1_index = {v: i for (i, v) in enumerate(seg1_ids)}
    seg2_index = {v: i for (i, v) in enumerate(seg2_ids)}

    overlap_mask = np.logical_and(seg1 != 0, seg2 != 0)

    n_rows = seg1_ids.size
    n_cols = seg2_ids.size

    seg1_vals = seg1[overlap_mask]
    seg2_vals = seg2[overlap_mask]

    counts = Counter(zip(seg1_vals, seg2_vals))

    rs, cs, vs = [], [], []
    for ((r, c), v) in counts.items():
        # subtracting one from indices so val 1 -> index 0
        rs.append(seg1_index[r])
        cs.append(seg2_index[c])
        vs.append(v)

    overlap_mat = sparse.coo_matrix((vs, (rs, cs)), shape=(n_rows, n_cols))
    return overlap_mat, seg1_ids, seg2_ids


def split_by_overlap(seg_to_split, overlap_seg, copy=True):
    """
    Split segments by overlap with a separate segmentation.

    Args:
        seg_to_split (3darray): A segmentation to split.
        overlap_seg (3darray): A segmentation which determines splits.
        copy (bool): Whether to perform the splitting in-place.
            Defaults to True, which creates a new volume.

    Returns:
        3darray: A new volume with each segment in :param:seg_to_split assigned
            a new id based on its overlap with ids in :param:overlap_seg.
    """
    overlaps, row_ids, col_ids = count_overlaps(seg_to_split, overlap_seg)
    rs, cs, _ = sparse.find(overlaps)

    dict_of_dicts = dict((r, dict()) for r in row_ids)
    for (v, (r, c)) in enumerate(zip(rs, cs)):
        row = row_ids[r]
        col = col_ids[c]
        dict_of_dicts[row][col] = v+1

    if copy:
        seg_to_split = np.copy(seg_to_split)

    return _relabel.relabel_paired_data(seg_to_split,
                                          overlap_seg, dict_of_dicts)
