__doc__ = """
Connected Components for Synaptic Partner-Signed Proximity

See: https://github.com/paragt/EMSynConn/blob/master/vertebrate/candidate/generate_proposals.py # noqa
"""

import numpy as np

from ... import seg_utils
from . import conn_comps


def find_prox_terminals(prox, seg=None, presyn_thresh=0,
                        postsyn_thresh=0, sz_thresh=0):
    """
    Threshold partner-signed proximity and make segments which represent
    pre- and post-synaptic terminals
    """
    presyn_v = prox > presyn_thresh
    postsyn_v = prox < postsyn_thresh

    presyn_ccs = conn_comps.connected_components3d(presyn_v).astype(np.uint32)
    postsyn_ccs = conn_comps.connected_components3d(postsyn_v).astype(np.uint32)

    if seg is not None:
        presyn_ccs = seg_utils.split_by_overlap(presyn_ccs, seg)
        postsyn_ccs = seg_utils.split_by_overlap(postsyn_ccs, seg)

        presyn_ccs[seg == 0] = 0
        postsyn_ccs[seg == 0] = 0

    if sz_thresh > 0:
        presyn_ccs = seg_utils.filter_segs_by_size(presyn_ccs, sz_thresh)[0]
        postsyn_ccs = seg_utils.filter_segs_by_size(postsyn_ccs, sz_thresh)[0]

    return presyn_ccs, postsyn_ccs
