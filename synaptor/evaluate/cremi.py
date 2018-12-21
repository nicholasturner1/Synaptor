#!/usr/bin/env python3
__doc__ == """
An implementation of the CREMI score metrics for synaptic clefts
(should be accurate as of June 2018)

Nicholas Turner, 2018
"""

import numpy as np
from scipy import ndimage

from . import score


def cremi_score(preds, labels, dist_thr=200,
                labels_edt=None, voxel_res=[4,4,40]):

    #binarize
    preds = (preds != 0)
    labels = (labels != 0)

    preds_edt = edt_to_nonzero(preds, voxel_res)
    if labels_edt is None:
        labels_edt = edt_to_nonzero(labels, voxel_res)

    fps = preds[labels_edt > dist_thr].sum()
    fns = labels[preds_edt > dist_thr].sum()

    tps = preds[labels_edt <= dist_thr].sum()

    dgt = preds_edt[np.logical_and(labels, preds_edt>dist_thr)].sum()
    df  = labels_edt[np.logical_and(preds, labels_edt>dist_thr)].sum()

    fscore = score.single_f1score(tps, fps, fns)

    return (1-fscore), tps, fps, fns, dgt, df


def edt_to_nonzero(vol, voxel_res=[4,4,40]):
    return ndimage.distance_transform_edt(np.logical_not(vol),
                                          sampling=voxel_res)
