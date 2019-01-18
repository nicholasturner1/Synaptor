__doc__ = """
Connectivity Edge Candidate Generation Using Cleft Segments

Nicholas Turner, 2018
"""

import itertools

import numpy as np
from scipy import spatial
from scipy import sparse

from ... import seg_utils


def extract_label_candidates(clefts, seg, dil_param=5, overlap_thresh=25):

    if dil_param > 0:
        clefts = seg_utils.dilate_by_k(clefts, dil_param)

    return overlapping_pairs(clefts, seg, overlap_thresh)


def overlapping_pairs(clefts, seg, overlap_thresh):

    overlaps, cleft_ids, seg_ids = seg_utils.count_overlaps(clefts, seg)

    pairs = list()

    r, c, v = sparse.find(overlaps)
    r = r[v > overlap_thresh]
    c = c[v > overlap_thresh]
    v = v[v > overlap_thresh]

    for i in np.unique(r):
        segs = c[r == i]
        for (seg_i, seg_j) in itertools.product(segs, segs):
            pairs.append((cleft_ids[i], seg_ids[seg_i], seg_ids[seg_j]))

    return pairs
