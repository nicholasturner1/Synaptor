#!/usr/bin/env python3


import numpy as np

from ..proc_tasks import chunk_ccs
from .. import seg_utils
from . import toolbox as tb
from . import overlap
from . import cremi
from . import score


def cremi_gridsearch_dset(dset, cc_threshs, sz_threshs,
                          dist_thr=200, voxel_res=[4,4,40],
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

        #Looping over volumes
        tps, fps, fns = 0, 0, 0

        print("Scoring...")
        new_score, setwise_scores = multi_cremi_score(preds, dset.labels,
                                                      label_edts, dist_thr,
                                                      voxel_res)

        scores[cc_i, sz_i] = new_score

    if delete:
        dset.delete()

    return scores


def multi_cremi_score(preds, labels, edts=None, dist_thr=200, voxel_res=[4,4,40]):

    if edts is None:
        edts = [cremi.edt_to_nonzero(label != 0) for label in labels]

    setwise_scores = []
    tps, fps, fns, dgt, df = 0, 0, 0, 0, 0
    for (p,l,dt) in zip(preds, labels, edts):

        (new_score, new_tps, new_fps, 
        new_fns, new_dgt, new_df) = cremi.cremi_score(p,l,
                                                      dist_thr=dist_thr,
                                                      labels_edt=dt,
                                                      voxel_res=voxel_res)
        tps += new_tps
        fps += new_fps
        fns += new_fns
        dgt += new_dgt
        df  += new_df
        setwise_scores.append(new_score)

    full_fscore = 1-score.single_f1score(tps, fps, fns)
    return ((dgt/fns + df/fps)/2), full_fscore, setwise_scores


def gridsearch(net_output, gt_clefts, cc_threshs, sz_threshs,
               score_mode="liberal"):

    precs = np.zeros((len(cc_threshs), len(sz_threshs)))
    recs = np.zeros((len(cc_threshs), len(sz_threshs)))

    for (cc_i, sz_i) in np.ndindex(precs.shape):

        cc_thr, sz_thr = cc_threshs[cc_i], sz_threshs[sz_i]
        print("PARAMS: CC @ {cc}, SZ @ {sz}".format(cc=cc_thr, sz=sz_thr))

        print("Thresholding and filtering...")
        ccs = clefts.dilated_components(net_output, 0, cc_thr)
        ccs, _ = seg_utils.filter_segs_by_size(ccs, sz_thr)

        print("Scoring...")
        prec, rec = overlap.score_overlaps(ccs, gt_clefts,
                                           mode=score_mode)

        precs[cc_i, sz_i] = prec[0] # score only
        recs[cc_i, sz_i] = rec[0] # score only

    return precs, recs
