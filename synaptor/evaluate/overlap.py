__doc__ = """
Evaluation functions for scoring segments by overlap

Nicholas Turner, 2017-8
"""

import numpy as np
import scipy.sparse as sp

from .. import seg_utils


def score_overlaps(pred_clf, gt_clf, mode="conservative", to_ignore=[]):
    """ Compute object-wise precision and recall scores """

    overlaps, pred_ids, gt_ids = seg_utils.count_overlaps(pred_clf, gt_clf)

    assert mode in ["bare","liberal","conservative"], "invalid mode"

    #Removing "ignored" segments from affecting the scores
    if len(to_ignore) > 0:
        overlaps, pred_ids, gt_ids = ignore_segments(overlaps, to_ignore,
                                                     pred_ids, gt_ids)

    # Need these sometimes for averaging across datasets
    n_pred = len(pred_ids)
    n_gt = len(gt_ids)

    if overlaps.shape == (0,0):  # no segments
        return precision(overlaps, pred_ids), recall(overlaps, gt_ids), n_pred, n_gt

    if mode == "liberal":
        overlaps = ensure_many_to_one(overlaps)
    elif mode == "conservative":
        overlaps = ensure_one_to_one(overlaps)
    else: #"bare"
        pass

    return precision(overlaps, pred_ids), recall(overlaps, gt_ids), n_pred, n_gt


def ignore_segments(overlaps, to_ignore, pred_ids, gt_ids):
    """
    Removing the rows of the overlap matrix which maximally overlap
    with ignored segments, then removing the ignored segment columns

    Assumes that the ids arrays are sorted and unique
    """

    # Picking columns to rm - assumes sorted and unique
    gt_set = set(gt_ids)
    to_ignore = list(filter(lambda x: x in gt_set, to_ignore))
    col_inds = np.searchsorted(gt_ids, to_ignore)

    max_inds = np.ravel(overlaps.argmax(1)) # argmax returns a np.matrix

    #Picking rows to rm - may be multiple for any col
    row_rm_mask = np.zeros((overlaps.shape[0],), dtype=np.bool)
    for col_i in col_inds:
        row_rm_mask[max_inds == col_i] = True
    row_inds = np.nonzero(row_rm_mask)[0].tolist()

    #Actually removing the proper rows and cols
    overlaps = remove_rows_and_cols(overlaps, row_inds, col_inds)

    pred_ids = np.delete(pred_ids, row_inds)
    gt_ids = np.delete(gt_ids, col_inds)


    return overlaps, pred_ids, gt_ids


def remove_rows_and_cols(overlaps, row_inds, col_inds):
    """ Removing rows and columns from a sparse matrix """

    rs, cs, vs = sp.find(overlaps)

    for r in sorted(row_inds, reverse=True):
        msk = rs != r
        vs = vs[msk]
        cs = cs[msk]
        rs = rs[msk]
        rs[rs > r] -= 1

    for c in sorted(col_inds, reverse=True):
        msk = cs != c
        vs = vs[msk]
        rs = rs[msk]
        cs = cs[msk]
        cs[cs > c] -= 1

    new_shape = (overlaps.shape[0]-len(row_inds),
                 overlaps.shape[1]-len(col_inds))

    return sp.coo_matrix((vs, (rs,cs)), shape=new_shape)


def ensure_many_to_one(overlaps):
    """
    Enforces the rule that each predicted id (row) overlaps with only one
    ground truth object (col). Picks the maximum
    """
    if overlaps.shape[1] == 0:
        return overlaps

    maxima = overlaps.max(1).toarray().ravel()
    inds = np.ravel(overlaps.argmax(1)) # argmax returns a np.matrix

    # limiting indices to rows with nonzero values
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

    if overlaps.shape[0] == 0:
        return overlaps

    maxima = overlaps.max(0).toarray().ravel()
    inds = np.ravel(overlaps.argmax(0)) # argmax returns a np.matrix

    # limiting indices to cols with nonzero values
    cs = np.nonzero(maxima != 0)[0]
    rs = inds[cs]
    maxima = maxima[cs]

    return sp.coo_matrix((maxima,(rs,cs)), shape=overlaps.shape)


def precision(overlaps, ids=None):
    """
    Computes precision for an overlap matrix.
    Assumes that predicted objects are represented by rows.

    If ids aren't dense (each row represents an object in the orig volume),
    can pass a list/np.array of ids to handle that.
    """
    if overlaps.shape[0] == 0:
        return 1, np.array([])

    elif overlaps.shape[1] == 0:
        return 0, np.array(ids)

    else:
        return matched_id_rate(overlaps, axis=1, ids=ids)


def recall(overlaps, ids=None):
    """
    Computes recall for an overlap matrix.
    Assumes that ground truth objects are represented by cols

    If ids aren't dense (each row represents an object in the orig volume),
    can pass a list/np.array of ids to handle that.
    """
    if overlaps.shape[1] == 0:
        return 1, np.array([])

    elif overlaps.shape[0] == 0:
        return 0, np.array(ids)

    else:
        return matched_id_rate(overlaps, axis=0, ids=ids)


def matched_id_rate(overlaps, axis, ids=None):
    """
    Computes how often a row/col id is matched with a col/row.
    This corresponds to precision or recall when mapped to the
    appropriate axis of an overlap matrix.

    Assumes that the sparse matrix has dense indices (e.g. all rows
    and cols refer to an object)

    If the possibility exists that one axis of comparison will be 0
    (e.g. high CC thresholds), pass in a default value to return
    """

    # if overlaps.shape[0] == 0: #no predicted clefts
    #     return default_rate, np.array([])

    maxima = overlaps.max(axis).toarray().ravel()

    score = (maxima != 0).sum() / maxima.size
    errors = np.nonzero(maxima == 0)

    if ids is not None:
        errors = np.array(ids)[errors]

    return score, errors


def find_new_comps(old_clefts, new_clefts):
    """
    Finds components with no overlaps in old_clefts. Useful for
    finding "newly-appeared" objects when lowering the cc threshold.
    """

    overlaps = count_overlaps(new_clefts, old_clefts)
    new_overlaps = overlaps.sum(1).flat

    new_ids = seg_utils.nonzero_unique_ids(new_clefts)

    return [ i for i in new_ids if new_overlaps[i-1] == 0 ]
