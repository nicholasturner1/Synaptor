""" Selecting locations for inference """


import random

import numpy as np

from ... import seg_utils
from ...types import bbox


IMPLEMENTED = ["random", "centroid", "coverage", "vol_center"]


def pick_cleft_locs(cleft, cleft_ids, loc_type, num_samples, patchsz):
    """
    General function for picking inference locations
    """
    assert loc_type in IMPLEMENTED, f"loc type {loc_type} not supported"

    if loc_type == "random":
        return pick_random_locs(cleft, cleft_ids, num_samples)

    elif loc_type == "centroid":
        return pick_centroids(cleft, cleft_ids)

    elif loc_type == "coverage":
        return covering_patches(cleft, cleft_ids, patchsz)

    elif loc_type == "vol_center":
        return vol_center(cleft, cleft_ids, patchsz)


def pick_random_locs(cleft, cleft_ids, num_locs):
    """
    Finds random locations within cleft for each id in cleft ids. Finds a
    number of locations equal to num_locs, and returns a dictionary mapping
    each id to its locations within a list.
    """
    order = np.argsort(cleft.flat)

    first = np.searchsorted(cleft.flat, cleft_ids, "left", order)
    last = np.searchsorted(cleft.flat, cleft_ids, "right", order)
    bounds = list(zip(first, last))

    indices = {i: list() for i in cleft_ids}
    for (i, cid) in enumerate(cleft_ids):
        lo, hi = bounds[i]

        for j in range(num_locs):
            linear_index = order[random.randint(lo, hi-1)]
            indices[cid].append(np.unravel_index(linear_index, cleft.shape))

    return indices


def pick_centroids(cleft, cleft_ids):
    """
    Computes the centroid coordinates for the clefts within
    a volume specified by cleft_ids.

    Returns a dictionary mapping each id to its centroid within a list. The
    list allows us to fit the general interface used by other loc functions.
    """
    centroids = seg_utils.centers_of_mass(cleft)
    locs = {cid: [centroids[cid]] for cid in cleft_ids}

    return locs


def covering_patches(cleft, cleft_ids, patchsz):
    """
    Selects locations which (when turned into patches) will at least cover
    the entire cleft.

    Returns a dictionary mapping each id to a list of locations
    """
    bboxes = seg_utils.bounding_boxes(cleft)
    locs = {i: list() for i in cleft_ids}

    for cid in cleft_ids:
        bbox_cid = bboxes[cid]
        cleft_msk = cleft[bbox_cid.index()] == cid
        msk_offset = bbox_cid.min()

        while cleft_msk.max():
            cid_locs = list(zip(*np.nonzero(cleft_msk)))

            loc = random.choice(cid_locs) + msk_offset
            patch = bbox.containing_box(loc, patchsz, cleft.shape)

            coverage = bbox_cid.intersect(patch).translate(-msk_offset)
            cleft_msk[coverage.index()] = False

            locs[cid].append(loc)

    return locs


def vol_center(cleft, cleft_ids, patchsz):

    assert all(c >= p for (c, p) in zip(cleft.shape, patchsz))

    middle = tuple(bbox.Vec3d(cleft.shape) // 2)

    return {cid: [middle] for cid in cleft_ids}
