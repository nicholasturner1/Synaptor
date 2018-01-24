#!/usr/bin/env python3


from collections import Counter

import numpy as np
import scipy.sparse as sp

from .. import seg_utils


def score_overlaps(pred_clefts, gt_clefts, mode="liberal"):
    """ Compute object-wise precision and recall scores """

    overlaps = count_overlaps(pred_clefts, gt_clefts)

    pred_ids = seg_utils.nonzero_unique_ids(pred_clefts)
    gt_ids = seg_utils.nonzero_unique_ids(gt_clefts)

    assert mode in ["bare","liberal","conservative"], "invalid mode"

    if mode == "liberal":
        overlaps = ensure_many_to_one(overlaps)
    elif mode == "conservative":
        overlaps = ensure_one_to_one(overlaps)
    else: #"bare"
        pass

    return precision(overlaps, pred_ids), recall(overlaps, gt_ids)


def count_overlaps(clefts, gt_clefts):
    """
    Count the overlapping voxels under each pair of overlapping
    objects. Returns a scipy.sparse matrix
    """

    overlap_mask = np.logical_and(clefts != 0, gt_clefts != 0)

    num_rows = clefts.max()
    num_cols = gt_clefts.max()

    pred_vals = clefts[overlap_mask]
    gt_vals = gt_clefts[overlap_mask]

    counts = Counter(zip(pred_vals, gt_vals))

    rs, cs, vs = [],[],[]
    for ((r,c),v) in counts.items():
        #subtracting one from indices so val 1 -> index 0
        rs.append(r-1)
        cs.append(c-1)
        vs.append(v)

    return sp.coo_matrix((vs,(rs,cs)), shape=(num_rows, num_cols))


def ensure_many_to_one(overlaps):
    """
    Enforces the rule that each predicted id (row) overlaps with only one
    ground truth object (col). Picks the maximum
    """

    maxima = overlaps.max(1).toarray().ravel()
    inds = np.ravel(overlaps.argmax(1)) #argmax returns a np.matrix

    #limiting indices to rows with nonzero values
    rs = np.nonzero(maxima != 0)[0]
    cs = inds[rs]
    maxima = maxima[rs]

    return sp.coo_matrix((maxima,(rs,cs)), shape=overlaps.shape)


def ensure_one_to_one(overlaps):
    """
    Enforces the rule that each predicted id (row) overlaps with only one
    ground truth object (col) AND vice versa.
    """

    overlaps = ensure_many_to_one(overlaps)

    maxima = overlaps.max(0).toarray().ravel()
    inds = np.ravel(overlaps.argmax(0)) #argmax returns a np.matrix

    #limiting indices to cols with nonzero values
    cs = np.nonzero(maxima != 0)[0]
    rs = inds[cs]
    maxima = maxima[cs]

    return sp.coo_matrix((maxima,(rs,cs)), shape=overlaps.shape)


def precision(overlaps, ids=None):
    """
    Computes precision for an overlap matrix.
    Assumes that predicted objects are represented by rows.

    If ids aren't dense (each row represents a object in the orig volume),
    can pass a list/np.array of ids to handle that.
    """
    return matched_id_rate(overlaps, axis=1, ids=ids, default_rate=1.)


def recall(overlaps, ids=None):
    """
    Computes recall for an overlap matrix.
    Assumes that ground truth objects are represented by cols

    If ids aren't dense (each row represents a object in the orig volume),
    can pass a list/np.array of ids to handle that.
    """
    return matched_id_rate(overlaps, axis=0, ids=ids, default_rate=0.)


def matched_id_rate(overlaps, axis, ids=None, default_rate=None):
    """
    Computes how often a row/col id is matched with a col/row.
    This corresponds to precision or recall when mapped to the
    appropriate axis.

    If ids aren't dense (each row represents a object in the orig volume),
    can pass a list/np.array of ids to handle that.

    If the possibility exists that one axis of comparison will be 0
    (e.g. high CC thresholds), pass in a default value to return
    """

    if overlaps.shape[0] == 0: #no predicted clefts
        return default_rate, []

    maxima = overlaps.max(axis).toarray().ravel()

    if ids is not None:
        inds = np.array(ids) - 1
        maxima = maxima[inds]

    score = (maxima != 0).sum() / maxima.size
    inds  = np.nonzero(maxima == 0)

    if ids is not None:
        inds = np.array(ids)[inds]

    return score, inds


def find_new_comps(old_clefts, new_clefts):
    """
    Finds components with no overlaps in old_clefts. Useful for
    finding "newly-appeared" objects when lowering the cc threshold.
    """

    overlaps = count_overlaps(new_clefts, old_clefts)
    new_overlaps = overlaps.sum(1).flat

    new_ids = seg_utils.nonzero_unique_ids(new_clefts)

    return [ i for i in new_ids if new_overlaps[i-1] == 0 ]
