""" HCBS Pruning Network Inference """

import torch

import numpy as np

from ...types import bbox
from ... import seg_utils
from . import locs


def prune_candidates(net, img, seg, patchsz, candidates, cleft=None,
                     output_thresh=0, cleft_locs=None, prox=None,
                     cleft_ids=None, loc_type="centroid"):
    """
    Apply pruner network to candidate list w/ threshold.

    Applies a pruner network to a list of candidate synaptic pairs.
    Each resulting pair with output greater than :param:output_thresh is
    returned within a list.

    Args:
        net (PyTorch model): The pruner network.
        img (3darray): An image volume.
        seg (3darray): A volume segmentation matching :param:img.
        patchsz (tuple): A length 3 tuple specifying the shape of the pruner
            network patch size.
        candidates (list): A list of (pair_id, presyn_id, postsyn_id) which
            represents the candidates to evaluate within this volume.
        cleft (3darray): A segmentation of the clefts within this volume.
            Only required if using a loc_type which uses cleft segments.
            Defaults to None.
        output_thresh (int/float): The threshold applied to each pruner output.
        cleft_locs (dict): A mapping from pair_id to a sampling location. Only
            required if :param:loc_type is "manual". Defaults to None.
        prox (3darray): A volume of partner signed cleft proximity. Provide
            this if you desire this to be used for pruning instead of cleft
            masks. Defaults to None.
        cleft_ids (list): A list of cleft ids to evaluate. Only required if
            loc_type is not manual. Defaults to None.
        loc_type (str): A string specifying how to determine sample locations.
            See locs.py. Defaults to "centroid".

    Returns:
        list: A subset of candidates whose output was greater than threshold.
        list: The output values for each candidate within the first return
            value.
    """
    if cleft_ids is None:
        cleft_ids = seg_utils.nonzero_unique_ids(cleft)

    if loc_type != "manual":
        assert cleft is not None, f"need cleft volume for loc_type {loc_type}"
        cleft_locs = locs.pick_cleft_locs(cleft, cleft_ids,
                                          loc_type, 1, patchsz)
    else:
        assert cleft_locs is not None, "manual loc mode w/o cleft_locs"

    pruned = list()
    outputs = list()
    for (cid, presyn_id, postsyn_id) in candidates:
        loc = cleft_locs[cid][0]
        box = bbox.containing_box(loc, patchsz, img.shape)

        img_p, syn_p, seg_p = get_patches(img, cleft, seg,
                                          box, cid, prox=prox)

        output = predict_candidate(net, img_p, syn_p, seg_p,
                                   presyn_id, postsyn_id)

        if output > output_thresh:
            pruned.append((cid, presyn_id, postsyn_id))
            outputs.append(output)

    return pruned, outputs


def max_candidates(net, img, seg, patchsz, candidates, cleft=None,
                   cleft_locs=None, prox=None, cleft_ids=None,
                   loc_type="centroid"):
    """
    Apply pruner network to candidate list, select maxima.

    Applies a pruner network to a list of candidate synaptic pairs.
    Each resulting pair with the greatest output for each pair id is returned.

    Args:
        net (PyTorch model): The pruner network.
        img (3darray): An image volume.
        seg (3darray): A volume segmentation matching :param:img.
        patchsz (tuple): A length 3 tuple specifying the shape of the pruner
            network patch size.
        candidates (list): A list of (pair_id, presyn_id, postsyn_id) which
            represents the candidates to evaluate within this volume.
        cleft (3darray): A segmentation of the clefts within this volume.
            Only required if using a loc_type which uses cleft segments.
            Defaults to None.
        cleft_locs (dict): A mapping from pair_id to a sampling location. Only
            required if :param:loc_type is "manual". Defaults to None.
        prox (3darray): A volume of partner signed cleft proximity. Provide
            this if you desire this to be used for pruning instead of cleft
            masks. Defaults to None.
        cleft_ids (list): A list of cleft ids to evaluate. Only required if
            loc_type is not manual. Defaults to None.
        loc_type (str): A string specifying how to determine sample locations.
            See locs.py. Defaults to "centroid".

    Returns:
        list: A subset of candidates whose output was maximal for each pair_id.
        list: The output values for each candidate within the first return
            value.
    """
    if cleft_ids is None:
        assert cleft is not None, f"need cleft volume for loc_type {loc_type}"
        cleft_ids = seg_utils.nonzero_unique_ids(cleft)

    if loc_type != "manual":
        cleft_locs = locs.pick_cleft_locs(cleft, cleft_ids,
                                          loc_type, 1, patchsz)
    else:
        assert cleft_locs is not None, "manual loc type w/o cleft_locs"

    pruned = dict()
    max_outputs = dict()
    for (cid, presyn_id, postsyn_id) in candidates:
        loc = cleft_locs[cid][0]
        box = bbox.containing_box(loc, patchsz, img.shape)

        img_p, syn_p, seg_p = get_patches(img, cleft, seg,
                                          box, cid, prox=prox)

        output = predict_candidate(net, img_p, syn_p, seg_p,
                                   presyn_id, postsyn_id)

        if cid in pruned:
            if output > max_outputs[cid]:
                pruned[cid] = (cid, presyn_id, postsyn_id)
                max_outputs[cid] = output
        else:
            pruned[cid] = (cid, presyn_id, postsyn_id)
            max_outputs[cid] = output

    pruned = list(pruned.values())
    return pruned


def get_patches(img, clf, seg, box, clfid, prox=None):
    """ Return 5d patches specified by the bbox for use in torch """

    img_p = format_patch(img[box.index()]) / 255.
    seg_p = format_patch(seg[box.index()])

    if prox is not None:
        syn_p = format_patch(prox[box.index()]).astype("float32")
    else:
        syn_p = format_patch(clf[box.index()] == clfid).astype("float32")

    return img_p, syn_p, seg_p


def format_patch(patch):
    """
    Formatting to fit common network conventions.

    Applies a transpose operation (reversing axis order in this case),
    and adds two dimensions for PyTorch.
    """
    return patch.transpose((2, 1, 0))[np.newaxis, np.newaxis, :]


def predict_candidate(net, img_p, syn_p, seg_p, presyn_id, postsyn_id):
    """
    Runs an pruner network over a single patch

    Returns a float
    """
    with torch.no_grad():
        # formatting
        presyn_p = (seg_p == presyn_id).astype("float32")
        postsyn_p = (seg_p == postsyn_id).astype("float32")
        net_input = np.concatenate((img_p, syn_p, presyn_p, postsyn_p),
                                   axis=1).astype("float32")
        net_input = torch.from_numpy(net_input.copy()).cuda()

        # network has only one output
        # and batch size = 1
        return net(net_input)[0].item()
