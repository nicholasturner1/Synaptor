""" Edge list diagnostics """


from ..proc import colnames as cn
from ..proc.edge.merge import merge_dups
import numpy as np


def predicted_self_loops(edge_dframe):
    subframe = edge_dframe[
                   edge_dframe[cn.presyn_id] == edge_dframe[cn.postsyn_id]]

    count = subframe.shape[0]
    print(f"{count} edges found:")
    return subframe


def surviving_dups(edge_dframe, dist_thr, res):
    dup_id_map = merge_dups.merge_duplicate_clefts(edge_dframe, dist_thr, res)

    count = len(dup_id_map)
    print(f"{count} edges found:")

    return dup_id_map


def pts_far_away(edge_dframe, pts1_cols, pts2_cols, voxel_res, dist_thr):
    pts1 = np.array(edge_dframe[pts1_cols])
    pts2 = np.array(edge_dframe[pts2_cols])

    dists = np.linalg.norm((pts1 - pts2) * voxel_res, axis=1)

    count = np.sum(dists > dist_thr)

    print(f"{count} edges found:")
    return edge_dframe.loc[dists > dist_thr]


def anchors_far_away(edge_dframe, voxel_res, dist_thr):
    return pts_far_away(edge_dframe, cn.presyn_coord_cols,
                        cn.postsyn_coord_cols, voxel_res,
                        dist_thr)


def presyn_far_away(edge_dframe, voxel_res, dist_thr):
    return pts_far_away(edge_dframe, cn.centroid_cols,
                        cn.presyn_coord_cols, voxel_res,
                        dist_thr)


def postsyn_far_away(edge_dframe, voxel_res, dist_thr):
    return pts_far_away(edge_dframe, cn.centroid_cols,
                        cn.postsyn_coord_cols, voxel_res,
                        dist_thr)


def any_pts_far_away(edge_dframe, voxel_res, dist_thr):
    anchor_results = anchors_far_away(edge_dframe, voxel_res, dist_thr)
    presyn_results = presyn_far_away(edge_dframe, voxel_res, dist_thr)
    postsyn_results = postsyn_far_away(edge_dframe, voxel_res, dist_thr)

    return anchor_results, presyn_results, postsyn_results
