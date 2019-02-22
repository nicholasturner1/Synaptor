__doc__ = """
Independent Implementation of HCBS' Synaptic Partner Candidate Generation

See: https://github.com/paragt/EMSynConn/blob/master/vertebrate/candidate/generate_proposals.py
"""

import numpy as np
from scipy import spatial
from scipy.ndimage import distance_transform_edt

from ... import seg_utils
from .. import seg


def extract_prox_candidates(prox, seg, presyn_thresh=0.3, postsyn_thresh=-0.3,
                            term_sz_thresh=0, seg_sz_thresh=0,
                            centroid_dist_thr=200, sep_thr=50,
                            voxel_res=[40, 4, 4],
                            remove_self=False):
    """
    Extract candidate synaptic pairs (and their locations) from
    partner-signed proximity output
    """
    presyn_terms, postsyn_terms = seg.find_prox_terminals(prox, seg,
                                                          presyn_thresh,
                                                          postsyn_thresh,
                                                          term_sz_thresh)

    return extract_terminal_candidates(presyn_terms, postsyn_terms, seg,
                                       term_sz_thresh, seg_sz_thresh,
                                       centroid_dist_thr, sep_thr,
                                       voxel_res=voxel_res,
                                       remove_self=remove_self)


def extract_terminal_candidates(presyn_terms, postsyn_terms, seg,
                                seg_sz_thresh=0, centroid_dist_thresh=200,
                                sep_thresh=50, voxel_res=[40, 4, 4],
                                remove_self=False):
    """
    Extract candidate synaptic pairs (and their locations) from segmented
    terminals
    """
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
                                      centroid_dist_thresh,
                                      voxel_res=voxel_res)

    # Filter set by their separation
    candidates, locs = filter_by_separation(initial_pairs, sep_thresh,
                                            presyn_terms, postsyn_terms,
                                            voxel_res=voxel_res)

    seg_pairs = list((presyn_segs[i], postsyn_segs[j])
                     for (i, j) in candidates)

    if remove_self:
        non_self_loops = [i for i in range(len(seg_pairs))
                          if seg_pairs[i][0] != seg_pairs[i][1]]
        seg_pairs = [seg_pairs[i] for i in non_self_loops]
        locs = [locs[i] for i in non_self_loops]
        candidates = [candidates[i] for i in non_self_loops]

    return seg_pairs, locs, candidates


def filter_terminals(terminals, seg, seg_sz_thresh):
    """
    Remove terminal segments which overlap with segments with size
    under a threshold
    """
    seg_szs = seg_utils.segment_sizes(seg)

    term_nonz = terminals[terminals != 0]
    seg_nonz = seg[terminals != 0]

    term_to_seg = dict(zip(term_nonz, seg_nonz))

    terms_to_remove = [k for (k, v) in term_to_seg.items()
                       if v == 0 or seg_szs[v] < seg_sz_thresh]

    term_to_seg = dict(filter(lambda p: p[0] not in terms_to_remove,
                              term_to_seg.items()))

    terminals = seg_utils.filter_segs_by_id(terminals,
                                            terms_to_remove, copy=False)

    return terminals, term_to_seg


def pairs_within_dist(centroids1, centroids2, dist_thr, voxel_res=[40, 4, 4]):
    """
    Return the keys within two centroid dictionaries which are within
    a threshold distance of one another
    """
    ids1 = list(centroids1.keys())
    ids2 = list(centroids2.keys())

    empty = np.zeros((0, 3), dtype=np.float32)

    if len(centroids1) > 0:
        cents1 = np.array([centroids1[i] for i in ids1]) * voxel_res
    else:
        cents1 = empty

    if len(centroids2) > 0:
        cents2 = np.array([centroids2[i] for i in ids2]) * voxel_res
    else:
        cents2 = empty

    pairs = np.nonzero(spatial.distance.cdist(cents1, cents2) < dist_thr)
    # converting to original ids
    pairs = list((ids1[i], ids2[j]) for (i, j) in zip(*pairs))

    return pairs


def filter_by_separation(candidates, sep_thr,
                         presyn_terms, postsyn_terms,
                         voxel_res=[40, 4, 4]):
    """
    Filter candidate synaptic partners by the separation distance between
    the relevant terminal segments
    """
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
