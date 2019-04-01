__doc__ = """
Evaluation functions for comparing partner signed proximity-based output
to cleft edge labels

Nicholas Turner, 2018
"""

import operator

import numpy as np

from .. import proc
from ..proc import seg
from ..proc import candidate
from ..proc import edge
from .. import seg_utils
from . import score


def score_at_thresholds(net, prox, img, seg, clf, labels,
                        presyn_thresh=0., postsyn_thresh=0., term_sz_thresh=0,
                        centroid_dist_thresh=200, sep_thr=50, seg_sz_thresh=0,
                        voxel_res=[40, 4, 4], patchsz=(160, 160, 16),
                        return_aux_data=False):
    """ TODO """
    # Making terminals
    find_prox_terminals = proc.seg.find_prox_terminals
    pre_terms, post_terms = find_prox_terminals(prox, seg,
                                                presyn_thresh=presyn_thresh,
                                                postsyn_thresh=postsyn_thresh,
                                                sz_thresh=term_sz_thresh)

    # Extracting candidates
    find_candidates = candidate.extract_terminal_candidates
    pairs, locs, cands = find_candidates(pre_terms, post_terms, seg,
                                         seg_sz_thresh=seg_sz_thresh,
                                         centroid_dist_thresh=centroid_dist_thresh,
                                         voxel_res=voxel_res,
                                         remove_self=True)

    # Formatting for pruner functions
    cands_fmt = [(cand, pair[0], pair[1])
                 for (cand, pair) in zip(cands, pairs)]
    locs_fmt = {cand: (loc,) for (cand, loc) in zip(cands, locs)}

    # Get all outputs
    _, scores = edge.prune_candidates(net, img, seg, patchsz, cands_fmt,
                                             output_thresh=-np.inf,
                                             cleft_locs=locs_fmt, prox=prox,
                                             loc_type="manual")

    assoc_clefts = find_max_cleft_overlaps(cands, pre_terms,
                                           post_terms, clf)

    preds_fmt = [(cleft, pair[0], pair[1])
                 for (cleft, pair) in zip(assoc_clefts, pairs)]

    returns = prec_rec_curve(preds_fmt, scores, labels)

    if return_aux_data:
        aux_returns = (pre_terms, post_terms, cands_fmt,
                       preds_fmt, locs_fmt, scores, assoc_clefts)
        return returns, aux_returns
    else:
        return returns


def find_max_cleft_overlaps(term_pairs, presyn_terms, postsyn_terms, clf):

    pre_ovl, pre_ids, clf_ids = seg_utils.count_overlaps(presyn_terms, clf)
    post_ovl, post_ids, _ = seg_utils.count_overlaps(postsyn_terms, clf)

    pre_ovl = pre_ovl.tocsr()
    post_ovl = post_ovl.tocsr()

    pre_lookup = {termid: i for (i, termid) in enumerate(pre_ids)}
    post_lookup = {termid: i for (i, termid) in enumerate(post_ids)}

    overlapping_clefts = list()
    for (presyn_id, postsyn_id) in term_pairs:
        pre_index = pre_lookup[presyn_id]
        post_index = post_lookup[postsyn_id]
        sum_ovl = pre_ovl[pre_index, :] + post_ovl[post_index, :]
        overlapping_clefts.append(clf_ids[np.argmax(sum_ovl)])

    return overlapping_clefts


def prec_rec_curve(edges, scores, labels):

    edges_w_scores = sorted(zip(edges, scores), key=operator.itemgetter(1))

    sorted_edges = list(map(operator.itemgetter(0), edges_w_scores))
    sorted_scores = list(map(operator.itemgetter(1), edges_w_scores))

    _, fps = score.precision(sorted_edges, labels)
    _, fns = score.recall(sorted_edges, labels)
    correct = 1 - np.array(fps)

    all_ps = 1 + np.array(range(len(fps)))[::-1]
    fps = np.cumsum(np.array(fps)[::-1])[::-1]
    tps = all_ps - fps
    fns = (np.cumsum(correct) - correct) + sum(fns)

    precs = tps / (tps + fps)
    recs = tps / (tps + fns)

    return precs, recs, sorted_edges, sorted_scores
