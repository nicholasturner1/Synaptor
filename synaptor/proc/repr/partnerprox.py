#!/usr/bin/env python
__doc__ = """
Transforming original CREMI sample labels into
a similar format to the one used by HCBS's submission

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import numpy as np
from scipy.ndimage.morphology import distance_transform_edt
from skimage.morphology import skeletonize

from ...types import bbox
from ... import seg_utils


def signed_proximity(seg, clf, edges, voxel_res, box_radius):

    clf = skeletonize_clefts(clf)

    dist = compute_signed_distance(seg, clf, edges, res=voxel_res,
                                   box_radius=box_radius)

    return parag_transform(dist)


def skeletonize_clefts(clf):

    msk = (clf != 0).astype(np.bool)
    skeletons = np.zeros(msk.shape, dtype=np.bool)

    for i in range(msk.shape[0]):
        skeletons[i,...] = skeletonize(msk[i,...])

    clf[~skeletons] = 0

    return clf


def compute_signed_distance(seg, clf, edges, box_radius, res):

    # result
    dist = np.zeros(seg.shape, dtype=np.float32)
    dist[:] = np.Inf

    bboxes = seg_utils.bounding_boxes(clf)

    # volume for specifying synaptic points within subregion
    for (i, presyn_segid, postsyn_segid) in edges:
        box = bboxes[i]
        box = box.grow_by(box_radius)
        box = bbox.shift_to_bounds(box, clf.shape)

        clf_box = clf[box.index()] != i
        seg_boxview = seg[box.index()]

        dist_box = distance_transform_edt(clf_box, sampling=res)
        dist_boxview = dist[box.index()]
        seg_boxview = seg[box.index()]

        box_mask = np.abs(dist_box) < np.abs(dist_boxview)
        presyn_mask = np.logical_and(box_mask, seg_boxview == presyn_segid)
        postsyn_mask = np.logical_and(box_mask, seg_boxview == postsyn_segid)

        dist_boxview[presyn_mask] = dist_box[presyn_mask]
        dist_boxview[postsyn_mask] = dist_box[postsyn_mask] * -1

    return dist


def expand_box_within_bounds(box, box_shape, vol_shape):
    return bbox.expand_box_within_bounds(box, box_shape, vol_shape)


def parag_transform(dist, sigma=50, alpha=5):
    return (np.exp( -(dist**2)/(2*sigma**2) ) 
            * (2 / (1 + np.exp(-alpha * dist)) - 1))
