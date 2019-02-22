#!/usr/bin/env python3

import numpy as np
import pandas as pd

from ... import seg_utils
from ...types import bbox


def place_anchor_pts(edge_df, seg, clf, voxel_res=[4, 4, 40],
                     offset=(0, 0, 0), min_box_width=[100, 100, 5],
                     wshed=None, cleft_ids=None, verbose=False):

    if cleft_ids is None:
        cleft_ids = seg_utils.nonzero_unique_ids(clf)
    if len(cleft_ids) == 0:
        return pd.DataFrame()

    cleft_bboxes = seg_utils.bounding_boxes(clf)
    edge_df = edge_df.loc[cleft_ids]
    edges = dict(zip(edge_df.index,
                     zip(edge_df.presyn_segid,
                         edge_df.postsyn_segid)))

    anchor_pts = list()
    presyn_wshed_id = -1
    postsyn_wshed_id = -1
    for cleft_id in cleft_ids:
        presyn, postsyn = edges[cleft_id]
        bbox = cleft_bboxes[cleft_id]

        presyn_pt = place_anchor_pt(cleft_id, presyn, clf, seg, bb=bbox,
                                    voxel_res=voxel_res, verbose=verbose,
                                    min_box_width=min_box_width)
        postsyn_pt = place_anchor_pt(cleft_id, postsyn, clf, seg, bb=bbox,
                                     voxel_res=voxel_res, verbose=verbose,
                                     min_box_width=min_box_width)

        if wshed is not None:
            presyn_wshed_id = wshed[presyn_pt]
            postsyn_wshed_id = wshed[postsyn_pt]

        # Formatting
        anchor_pts.append(make_record(cleft_id, presyn_pt, postsyn_pt,
                                      presyn_wshed_id, postsyn_wshed_id,
                                      offset=offset))

    return pd.DataFrame.from_records(anchor_pts)


def place_anchor_pt(cleft_id, seg_id, clf, seg,
                    bb=None, surfaces=None, verbose=False,
                    voxel_res=[4, 4, 40], min_box_width=[100, 100, 5]):

    if verbose:
        print(f"Placing anchor for cleft {cleft_id} on segment {seg_id}")

    if np.isnan(seg_id):
        return (-1,-1,-1)
    if bb is None:
        bb = seg_utils.bounding_boxes(clf)[cleft_id]
    clf_b = clf[bb.index()]

    bb = bb.grow_by(min_box_width)
    bb = bbox.shift_to_bounds(bb, seg.shape)

    # Extra checking that the bbox coordinates are valid
    bounds = bbox.BBox3d((0, 0, 0), seg.shape)
    bb = bb.intersect(bounds)

    if verbose:
        print(f"local bbox: {bb}")

    # v = "view"
    seg_v = seg[bb.index()]
    clf_v = clf[bb.index()]

    if seg_id not in seg_v:
        return (-2,-2,-2)

    base_pt = closest_pt_to_seg(cleft_id, seg_id, clf_v, seg_v, voxel_res)
    shifted = shift_pt(base_pt, seg_id, seg_v, min_box_width, voxel_res)
    anchor_pt = tuple(shifted + bb.min())

    return anchor_pt


def closest_pt_to_seg(seg1_id, seg2_id, seg1, seg2, voxel_res):
    """Greedily estimates the closest point in seg2 to seg1"""

    # Takes a greedy strategy
    seg1_coords = find_coords(seg1, seg1_id)
    seg2_coords = find_coords(seg2, seg2_id)

    closest_seg1pt = tuple(seg1_coords[0])
    closest_seg2pt = tuple(seg2_coords[0])

    while True:
        new_pt2 = closest_coord_to_pt(closest_seg1pt, seg2_coords, voxel_res)
        new_pt1 = closest_coord_to_pt(new_pt2, seg1_coords, voxel_res)

        if new_pt1 == closest_seg1pt and new_pt2 == closest_seg2pt:
            break

        closest_seg1pt = new_pt1
        closest_seg2pt = new_pt2

    return closest_seg2pt


def find_coords(seg, segid):
    return np.array(np.nonzero(seg == segid)).T


def closest_coord_to_pt(point, coords, voxel_res):
    dists = np.linalg.norm((coords - point) * voxel_res, axis=1)
    return tuple(coords[np.argmin(dists)])


def shift_pt(base_pt, seg_id, seg_v, box_width, voxel_res):

    bb = bbox.containing_box(base_pt, box_width, seg_v.shape)

    local_patch = seg_v[bb.index()]
    local_coords = find_coords(local_patch, seg_id)
    local_centroid = tuple(np.mean(local_coords, axis=0))
    local_centroid_coord = closest_coord_to_pt(local_centroid, local_coords,
                                               voxel_res)

    return tuple(local_centroid_coord + bb.min())


def make_record(cleft_segid, presyn_pt, postsyn_pt,
                presyn_wshed_id, postsyn_wshed_id,
                offset=(0, 0, 0)):

    # valid coordinates are > 0, others are error codes
    add_if_valid = lambda x, y: x + y if x >= 0 else x

    record = {
        "cleft_segid": cleft_segid,
        "presyn_x": add_if_valid(presyn_pt[0], offset[0]),
        "presyn_y": add_if_valid(presyn_pt[1], offset[1]),
        "presyn_z": add_if_valid(presyn_pt[2], offset[2]),
        "postsyn_x": add_if_valid(postsyn_pt[0], offset[0]),
        "postsyn_y": add_if_valid(postsyn_pt[1], offset[1]),
        "postsyn_z": add_if_valid(postsyn_pt[2], offset[2]),
        "presyn_basin": presyn_wshed_id,
        "postsyn_basin": postsyn_wshed_id
    }

    return record
