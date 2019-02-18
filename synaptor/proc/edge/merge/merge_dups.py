__doc__ = """
Merging Duplicates - defined as two clefts which connect the same
partners within some threshold distance
"""

import math
import operator

import numpy as np
import scipy.spatial

from ... import utils
from ... import colnames as cn


def merge_duplicate_clefts(full_info_df, dist_thr, res):

    cleft_by_partners = match_clefts_by_partners(full_info_df)

    conn_comps = []

    for cleft_list in cleft_by_partners.values():

        if len(cleft_list) == 1:
            continue

        cleft_ids = list(map(operator.itemgetter(0), cleft_list))
        cleft_coords = list(map(operator.itemgetter(1), cleft_list))

        cleft_pairs = find_pairs_within_dist(cleft_ids, cleft_coords,
                                             dist_thr, res)

        conn_comps.extend(utils.find_connected_components(cleft_pairs))

    return utils.make_id_map(conn_comps)


def merge_duplicate_clefts1(full_info_df, dist_thr, res):

    conn_comps = []
    for _, df in full_info_df.groupby([cn.presyn_id, cn.postsyn_id]):

        if df.shape[0] == 1:
            continue

        cleft_ids = df.cleft_segid.values
        cleft_coords = df[cn.centroid_cols].values

        cleft_pairs = find_pairs_within_dist(cleft_ids, cleft_coords,
                                             dist_thr, res)

        conn_comps.extend(utils.find_connected_components(cleft_pairs))

    return utils.make_id_map(conn_comps)


def merge_duplicate_clefts2(full_info_df, dist_thr, res):

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


def merge_polyad_dups(edge_list, centroids, dist_thr, res):

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


def find_pairs_within_dist(ids, coords, dist_thr, res):

    coord_array = np.vstack(coords) * res

    dists = scipy.spatial.distance.pdist(coord_array)
    under_thr = np.nonzero(dists < dist_thr)[0]

    pairs = [row_col_from_condensed_index(len(ids), i) for i in under_thr]

    return list(map(lambda tup: (ids[tup[0]], ids[tup[1]]), pairs))


def match_clefts_by_partners(cleft_info_df):

    cleft_by_partners = {}
    for (cid, pre, post, x, y, z) in zip(cleft_info_df[cn.cleft_id],
                                         cleft_info_df[cn.presyn_id],
                                         cleft_info_df[cn.postsyn_id],
                                         cleft_info_df[cn.centroid_x],
                                         cleft_info_df[cn.centroid_y],
                                         cleft_info_df[cn.centroid_z]):

        partners = (pre, post)

        if partners not in cleft_by_partners:
            cleft_by_partners[partners] = [(cid, (x, y, z))]
        else:
            cleft_by_partners[partners].append((cid, (x, y, z)))

    return cleft_by_partners


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


def row_col_from_condensed_index(d, i):
    # https://stackoverflow.com/questions/5323818/condensed-matrix-function-to-find-pairs  # noqa
    b = 1 - 2 * d
    x = math.floor((-b - math.sqrt(b**2 - 8*i))/2)
    y = i + x*(b + x + 2)/2 + 1
    return (x, int(y))
