"""
Merging Duplicates - defined as two clefts which connect the same
partners within some distance threshold
"""

import math
import operator

import numpy as np
import scipy.spatial

from ... import utils
from ... import colnames as cn


def merge_duplicate_clefts(full_info_df, dist_thr, res):

    full_info_df = full_info_df.reset_index()
    conn_comps = []

    def find_new_comps(group):
        if len(group) > 1:
            ids = group.cleft_segid.values
            coords = group[cn.centroid_cols].values

            pairs = find_pairs_within_dist(ids, coords, dist_thr, res)

            conn_comps.extend(utils.find_connected_components(pairs))
        return 0

    full_info_df.groupby([cn.presyn_id, cn.postsyn_id]).apply(find_new_comps)

    return utils.make_id_map(conn_comps)


def find_pairs_within_dist(ids, coords, dist_thr, res):

    coord_array = np.vstack(coords) * res

    dists = scipy.spatial.distance.pdist(coord_array)
    under_thr = np.nonzero(dists < dist_thr)[0]

    pairs = [row_col_from_condensed_index(len(ids), i) for i in under_thr]

    return list(map(lambda tup: (ids[tup[0]], ids[tup[1]]), pairs))


def row_col_from_condensed_index(d, i):
    # https://stackoverflow.com/questions/5323818/condensed-matrix-function-to-find-pairs  # noqa
    b = 1 - 2 * d
    x = math.floor((-b - math.sqrt(b**2 - 8*i))/2)
    y = i + x*(b + x + 2)/2 + 1
    return (x, int(y))


def merge_polyad_dups(edge_list, centroids, dist_thr, res):
    """ A quick implementation for CREMI """

    cleft_by_presyn = match_clefts_by_presyn(edge_list)

    conn_comps = []

    for cleft_ids in cleft_by_presyn.values():

        if len(cleft_ids) == 1:
            continue

        cleft_coords = list(centroids[cid] for cid in cleft_ids)

        cleft_pairs = find_pairs_within_dist(cleft_ids, cleft_coords,
                                             dist_thr, res)

        conn_comps.extend(utils.find_connected_components(cleft_pairs))

    return utils.make_id_map(conn_comps)


def match_clefts_by_presyn(edge_list):

    clefts_by_presyn = {}
    for (cid, pre, post) in edge_list:

        if pre not in clefts_by_presyn:
            clefts_by_presyn[pre] = {cid}
        else:
            clefts_by_presyn[pre].add(cid)

    # Converting to lists
    for (k, v) in clefts_by_presyn.items():
        clefts_by_presyn[k] = list(v)

    return clefts_by_presyn
