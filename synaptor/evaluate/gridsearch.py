#!/usr/bin/env python3


import itertools

import numpy as np

from .. import clefts
from .. import seg_utils
from . import overlap


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
