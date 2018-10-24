#!/usr/bin/env python3

import operator

import numpy as np
import scipy.spatial as sp

from .. import seg_utils
from ..types import bbox


def place_edge_points(edges, seg, clf, voxel_res=[40,4,4], box_shape=[5,100,100]):

    edge_points = []
    print("Computing surfaces")
    surfaces3d = seg_utils.label_surfaces3d(seg)
    print("Computing bounding boxes")
    cleft_bboxes = seg_utils.bounding_boxes(clf)

    for (cleft_i, presyn_j, postsyn_k) in edges:
        bb = cleft_bboxes[cleft_i].grow_by(box_shape)
        bb = bbox.shift_to_bounds(bb,seg.shape)
        seg_p = seg[bb.index()]
        clf_p = clf[bb.index()]
        surf_p = surfaces3d[bb.index()]

        postsyn_surfpt = closest_segpt_to_seg(clf_p, surf_p, cleft_i, postsyn_k, voxel_res)
        presyn_surfpt = closest_segpt_to_pt(postsyn_surfpt, surf_p, presyn_j, voxel_res)

        presyn_pt = shifted_point(seg_p, presyn_surfpt,
                                  presyn_j, box_shape, voxel_res)
        postsyn_pt = shifted_point(seg_p, postsyn_surfpt,
                                   postsyn_k, box_shape, voxel_res)

        presyn_pt = tuple(presyn_pt + bb.min())
        postsyn_pt = tuple(postsyn_pt + bb.min())
        edge_points.append((cleft_i, presyn_pt, postsyn_pt))

    return edge_points


def closest_segpt_to_seg(clefts, segs, cleft_i, seg_j, voxel_res):

    #Takes a greedy strategy
    cleft_coords = find_coords(clefts, cleft_i)
    seg_coords = find_coords(segs, seg_j)

    closest_segpt = tuple(seg_coords[0])
    closest_clfpt = tuple(cleft_coords[0])

    while True:
        new_segpt = closest_coord_to_pt(closest_clfpt, seg_coords, voxel_res)
        new_clfpt = closest_coord_to_pt(new_segpt, cleft_coords, voxel_res)

        if new_segpt == closest_segpt and new_clfpt == closest_clfpt:
            break

        closest_segpt = new_segpt
        closest_clfpt = new_clfpt


    return closest_segpt


def closest_segpt_to_pt(point, seg, seg_i, voxel_res):
    seg_coords = find_coords(seg, seg_i)
    return closest_coord_to_pt(point, seg_coords, voxel_res)


def closest_coord_to_pt(point, coords, voxel_res):
    dists = np.linalg.norm((coords-point) * voxel_res,axis=1)
    return tuple(coords[np.argmin(dists)])


def shifted_point(valid_points, anchor_pt, segid, box_shape, voxel_res):

    bb = bbox.containing_box(anchor_pt, box_shape, valid_points.shape)

    local_patch = valid_points[bb.index()]
    local_coords = find_coords(local_patch, segid)
    local_centroid = tuple(np.mean(local_coords,axis=0))
    local_centroid_coord = closest_coord_to_pt(local_centroid, local_coords,
                                               voxel_res)

    return tuple(local_centroid_coord + bb.min())


def create_KDTree(segs, seg_i, voxel_res):
    points = find_coords(segs, seg_i) * voxel_res
    return sp.KDTree(points)


def find_coords(seg, segid):
    return np.array(np.nonzero(seg==segid)).T


def scale_point(point, voxel_res):
    return (point[0]*voxel_res[0],
            point[1]*voxel_res[1],
            point[2]*voxel_res[2])


def inv_scale_point(point, voxel_res):
    return (point[0]//voxel_res[0],
            point[1]//voxel_res[1],
            point[2]//voxel_res[2])
