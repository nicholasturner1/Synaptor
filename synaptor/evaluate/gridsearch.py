__doc__ = """
Grid search functions

Nicholas Turner, 2018
"""

import itertools

import numpy as np

from .. import proc
from .. import seg_utils
from .auto import toolbox as tb
from . import cremi
from . import score
from . import edge


def gridsearch_edgethresh(seg_weights, labels, pre_threshs, post_threshs):

    max_f1 = 0.
    opt_preds = list()
    opt_pre_t, opt_post_t = 0., 0.

    for (pre_t, post_t) in itertools.product(pre_threshs, post_threshs):
        preds = proc.edge.assign.assign_all_by_thresh(seg_weights,
                                                      pre_t, post_t)
        new_f1 = score.f1score(preds, labels)[0]

        if new_f1 > max_f1:
            max_f1 = new_f1
            opt_preds = preds
            opt_pre_t, opt_post_t = pre_t, post_t

    return opt_pre_t, opt_post_t, max_f1, opt_preds


def gridsearch_edgethresh_avg(dset_avgs, dset_sums, dset_szs, dset_labels,
                              pre_threshs=None, post_threshs=None,
                              assign_type="double thresh",
                              score_type="avg",
                              alphas=[1], pre_type=None, post_type=None):

    # Init
    max_avg_f1 = -1.
    opt_preds = list()
    opt_pre_t, opt_post_t = 0., 0.
    opt_alpha = 0.

    for alpha in alphas:
        # for each dataset - precompute scores to use for thresholding
        dset_scores = list()
        for (avgs, sums, szs) in zip(dset_avgs, dset_sums, dset_szs):
            new_scores = proc.edge.score.compute_all(avgs, sums, szs,
                                                     alpha=alpha,
                                                     pre_type=pre_type,
                                                     post_type=post_type,
                                                     score_type=score_type)
            dset_scores.append(new_scores)

        # for each pair of thresholds
        for (pre_t, post_t) in itertools.product(pre_threshs, post_threshs):
            # for each dataset - assign edges using the scores and eval them
            dset_preds = list()
            for scores in dset_scores:
                new_preds = proc.edge.assign.assign_all(
                                scores, thresh=pre_t, thresh2=post_t,
                                assign_type=assign_type)

                dset_preds.append(new_preds)

            # evaluation
            f1s = [score.f1score(preds, labels)[0]
                   for (preds, labels) in zip(dset_preds, dset_labels)]

            new_avg_f1 = sum(f1s) / len(f1s)

            if new_avg_f1 > max_avg_f1:
                max_avg_f1 = new_avg_f1
                opt_preds = dset_preds
                opt_pre_t, opt_post_t = pre_t, post_t
                opt_alpha = alpha

    return opt_pre_t, opt_post_t, opt_alpha, max_avg_f1, opt_preds


def cremi_gridsearch_dset(dset, cc_threshs, sz_threshs,
                          dist_thr=200, voxel_res=[4, 4, 40],
                          delete=True):

    tb.read_dataset(dset)
    scores = np.zeros((len(cc_threshs), len(sz_threshs)))

    print("Precomputing label_edts")
    label_edts = [cremi.edt_to_nonzero(label != 0)
                  for label in dset.labels]

    for (cc_i, sz_i) in np.ndindex(scores.shape):

        cc_thr, sz_thr = cc_threshs[cc_i], sz_threshs[sz_i]
        print("PARAMS: CC @ {cc}, SZ @ {sz}".format(cc=cc_thr, sz=sz_thr))

        print("Thresholding and filtering...")
        preds = tb.make_clefts_at_params(dset, cc_thr, sz_thr)

        print("Scoring...")
        new_score, setwise_scores = multi_cremi_score(preds, dset.labels,
                                                      label_edts, dist_thr,
                                                      voxel_res)

        scores[cc_i, sz_i] = new_score

    if delete:
        dset.delete()

    return scores


def multi_cremi_score(preds, labels, edts=None,
                      dist_thr=200, voxel_res=[4, 4, 40]):

    if edts is None:
        edts = [cremi.edt_to_nonzero(label != 0) for label in labels]

    setwise_scores = []
    tps, fps, fns, dgt, df = 0, 0, 0, 0, 0
    for (p, l, dt) in zip(preds, labels, edts):

        (new_score, new_tps, new_fps,
         new_fns, new_dgt, new_df) = cremi.cremi_score(p, l,
                                                       dist_thr=dist_thr,
                                                       labels_edt=dt,
                                                       voxel_res=voxel_res)
        tps += new_tps
        fps += new_fps
        fns += new_fns
        dgt += new_dgt
        df += new_df
        setwise_scores.append(new_score)

    full_fscore = 1-score.single_f1score(tps, fps, fns)
    return ((dgt/fns + df/fps)/2), full_fscore, setwise_scores


def gridsearch(img, seg, net_output, cleft_lbls, edge_lbls,
               cc_threshs, asynet, patchsz, sz_threshs,
               score_mode="conservative", beta=1):

    precs = np.zeros((len(cc_threshs), len(sz_threshs)))
    recs = np.zeros((len(cc_threshs), len(sz_threshs)))
    fscores = np.zeros((len(cc_threshs), len(sz_threshs)))

    max_fscore = 0.

    for (cc_i, sz_i) in np.ndindex(precs.shape):

        cc_thr, sz_thr = cc_threshs[cc_i], sz_threshs[sz_i]
        print("PARAMS: CC @ {cc}, SZ @ {sz}".format(cc=cc_thr, sz=sz_thr))

        print("Thresholding and filtering...")
        ccs = proc.seg.connected_components(net_output, cc_thr)
        ccs, _ = seg_utils.filter_segs_by_size(ccs, sz_thr)

        edge_df = proc.edge.infer_edges(asynet, img, ccs, seg,
                                        patchsz=patchsz,
                                        samples_per_cleft=1)

        preds = list(zip(edge_df.cleft_segid,
                         edge_df.presyn_segid,
                         edge_df.postsyn_segid))

        print("Scoring...")
        prec, rec = edge.score_segmented_edges(ccs, preds,
                                               cleft_lbls, edge_lbls)

        precs[cc_i, sz_i] = prec[0]  # score only
        recs[cc_i, sz_i] = rec[0]  # score only
        fscore = score.single_fscore_PR(prec[0], rec[0], beta)
        fscores[cc_i, sz_i] = fscore

        if fscore > max_fscore:
            max_fscore = fscore
            max_cc_thr = cc_thr
            max_sz_thr = sz_thr

    return precs, recs, fscores, (max_fscore, max_cc_thr, max_sz_thr)
