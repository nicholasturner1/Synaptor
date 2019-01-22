#!/usr/bin/env python3


from collections import Counter

import numpy as np
import scipy.sparse as sp


def count_overlaps(segs, base_segs, type_bits=32):
    """
    Count the overlapping voxels under each pair of overlapping
    objects. Returns a scipy.sparse matrix
    """
    overlap_mask = np.logical_and(segs != 0, base_segs != 0)

    n_rows = np.max(segs) + 1
    n_cols = np.max(base_segs) + 1

    seg_vals = segs[overlap_mask]
    base_vals = base_segs[overlap_mask]

    counts = Counter(zip(seg_vals, base_vals))

    rs, cs, vs = [],[],[]
    for ((r,c),v) in counts.items():
        # subtracting one from indices so val 1 -> index 0
        rs.append(r)
        cs.append(c)
        vs.append(v)

    return sp.coo_matrix((vs,(rs,cs)), shape=(n_rows, n_cols))
