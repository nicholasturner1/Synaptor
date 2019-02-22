__doc__ = """
Independent Implementation of HCBS' Synaptic Partner Candidate Generation
"""
import operator
import itertools

import numpy as np
from scipy import spatial
from scipy import sparse
from scipy.ndimage import distance_transform_edt

from ... import seg_utils
from .. import seg


def extract_prox_candidates(proxim, seg, presyn_thr, postsyn_thr,
                            term_sz_thresh, seg_sz_thresh,
                            centroid_dist_thr, sep_thr, voxel_res=[40,4,4]):

    presyn_terms = find_terminals(proxim > presyn_thr, seg, term_sz_thresh)
    postsyn_terms = find_terminals(proxim < postsyn_thr, seg, term_sz_thresh)

    # Filter terminals by the segments with which they overlap
    # (can't be too small)
    presyn_terms, presyn_segs = filter_terminals(presyn_terms,
                                                 seg, seg_sz_thresh)
    postsyn_terms, postsyn_segs = filter_terminals(postsyn_terms,
                                                   seg, seg_sz_thresh)

    # Compute some useful stuff for later
    presyn_centroids = seg_utils.centers_of_mass(presyn_terms)
    postsyn_centroids = seg_utils.centers_of_mass(postsyn_terms)

    # Consider the initial set within some distance
    initial_pairs = pairs_within_dist(presyn_centroids, postsyn_centroids,
                                      centroid_dist_thr, voxel_res=voxel_res)

    # Filter set by their separation
    candidates, locs = filter_by_dist(initial_pairs, sep_thr,
                                      presyn_terms, postsyn_terms,
                                      voxel_res=voxel_res)


    seg_pairs = list((presyn_segs[i], postsyn_segs[j])
                     for (i, j) in candidates)

    return seg_pairs, locs


def find_terminals(threshed_proxim, seg, sz_thresh):

    ccs = seg.connected_components(threshed_proxim)
    ccs = split_ccs_by_overlap(ccs, seg)

    return seg_utils.filter_segs_by_size(ccs, sz_thresh)[0]


def split_ccs_by_overlap(ccs, seg):

    assert ccs.max() < np.iinfo(np.uint32).max, "cc values too high"
    assert seg.max() < np.iinfo(np.uint32).max, "seg values too high"

    ccs = ccs.astype(np.uint32)
    split = (seg.astype(np.uint64) << np.uint64(32)) + ccs
    split[ccs == 0] = 0

    return seg_utils.relabel_data_1N(split, copy=False).astype(np.uint32)


def filter_terminals(terminals, seg, seg_sz_thresh):

    seg_szs = seg_utils.segment_sizes(seg)

    term_nonz = terminals[terminals != 0]
    seg_nonz = seg[terminals != 0]

    term_to_seg = dict(zip(term_nonz, seg_nonz))

    under_thresh = lambda x: x == 0 or seg_szs[x] < seg_sz_thresh

    terms_to_remove = list(map(operator.itemgetter(0),
                               filter(lambda pair: under_thresh(pair[1]),
                                      term_to_seg.items())))

    term_to_seg = dict(filter(lambda p: p[0] not in terms_to_remove,
                              term_to_seg.items()))

    terminals = seg_utils.filter_segs_by_id(terminals,
                                            terms_to_remove, copy=False)

    return terminals, term_to_seg


def pairs_within_dist(centroids1, centroids2, dist_thr, voxel_res=[40,4,4]):

    ids1 = list(centroids1.keys())
    ids2 = list(centroids2.keys())

    cents1 = np.array([centroids1[i] for i in ids1]) * voxel_res
    cents2 = np.array([centroids2[i] for i in ids2]) * voxel_res

    pairs = np.nonzero(spatial.distance.cdist(cents1, cents2) < dist_thr)
    # converting to original ids
    pairs = list((ids1[i], ids2[j]) for (i,j) in zip(*pairs))

    return pairs


def filter_by_dist(candidates, sep_thr,
                   presyn_terms, postsyn_terms, voxel_res=[40,4,4]):

    presyn_bboxes = seg_utils.bounding_boxes(presyn_terms)
    postsyn_bboxes = seg_utils.bounding_boxes(postsyn_terms)

    filtered = list()
    locs = list()
    for (pre, post) in candidates:
        bbox = presyn_bboxes[pre].merge(postsyn_bboxes[post])

        pre_view = presyn_terms[bbox.index()]
        post_view = postsyn_terms[bbox.index()]

        edt = distance_transform_edt(post_view != post, sampling=voxel_res)

        edt[pre_view != pre] = np.inf
        if np.any(edt[pre_view == pre] < sep_thr):
            filtered.append((pre, post))
            # Find closest pt between terminals
            local_loc = np.unravel_index(np.argmin(edt), edt.shape)
            locs.append(tuple(local_loc + bbox.min()))

    return filtered, locs


def extract_label_candidates(clefts, seg, dil_param=5, overlap_thresh=25,
                             filter_self=False):

    if dil_param > 0:
        clefts = clefts.transpose((2, 1, 0))
        clefts = seg_utils.dilate_by_k(clefts, dil_param)
        clefts = clefts.transpose((2, 1, 0))

    candidates = overlapping_pairs(clefts, seg, overlap_thresh)

    if filter_self:
        candidates = [candidate for candidate in candidates
                      if candidate[0] != candidate[1]]

    return candidates


def overlapping_pairs(clefts, seg, overlap_thresh):

    overlaps, cleft_ids, seg_ids = seg_utils.count_overlaps(clefts, seg)

    pairs = list()

    r, c, v = sparse.find(overlaps)
    r = r[v > overlap_thresh]
    c = c[v > overlap_thresh]
    v = v[v > overlap_thresh]

    for i in np.unique(r):
        segs = c[r == i]
        for (seg_i, seg_j) in itertools.product(segs, segs):
            pairs.append((cleft_ids[i], seg_ids[seg_i], seg_ids[seg_j]))

    return pairs
