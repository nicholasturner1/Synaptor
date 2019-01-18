__doc__ = """
Evaluation functions for scoring connectivity graph edges

Nicholas Turner, 2018
"""
import numpy as np

from . import score
from .. import seg_utils


def score_edges(preds, labels):
    """
    Find the precision & recall scores for edge predicions
    """
    return score.precision(preds, labels), score.recall(preds, labels)


def score_segmented_edges(pred_seg, pred_edges, lbl_seg, lbl_edges):
    """
    Find the precision & recall scores for a set of predictions tied to
    segments within a volume. Each predicted segment is mapped to its
    maximally overlapping segment within the label segments.
    """
    overlaps, pred_ids, lbl_ids = seg_utils.count_overlaps(pred_seg, lbl_seg)

    max_overlap_mapping = find_max_overlaps(overlaps, pred_ids, lbl_ids)

    remapped_edges = map_pred_edges(pred_edges, max_overlap_mapping)

    prec = score.precision(remapped_edges, lbl_edges)
    rec = score.recall(remapped_edges, lbl_edges)

    return prec, rec


def find_max_overlaps(overlaps, row_ids, col_ids):
    """
    Pairs each row id with it's maximally overlapping column by a dictionary
    """
    if overlaps.shape[0] == 0:
        return dict()

    max_inds = np.array(overlaps.argmax(1)).ravel()

    return {row_ids[i]: col_ids[j] for (i, j) in enumerate(max_inds)}


def map_pred_edges(pred_edges, mapping):
    """
    Returns a new list of edges where the segment id is remapped based
    on the provided dictionary.
    """
    return list((mapping[edge[0]], edge[1], edge[2]) for edge in pred_edges)
