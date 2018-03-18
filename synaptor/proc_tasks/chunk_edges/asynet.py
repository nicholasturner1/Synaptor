#!/usr/bin/env python
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import dict
from builtins import range
from builtins import zip
from builtins import map
from future import standard_library
standard_library.install_aliases()


import random, copy, operator

import torch
from torch.autograd import Variable
from torch.nn import functional as F

import numpy as np
import scipy.ndimage as ndimage
import scipy.ndimage.morphology as morph
import pandas as pd

from ...types import bbox
from ... import seg_utils

import time


RECORD_SCHEMA = ["cleft_segid",     "presyn_segid", "postsyn_segid",
                 "presyn_x",        "presyn_y",     "presyn_z",
                 "postsyn_x",       "postsyn_y",    "postsyn_z",
                 "presyn_wt",       "postsyn_wt",
                 "presyn_sz",       "postsyn_sz" ]
SCHEMA_W_BASINS = RECORD_SCHEMA + ["presyn_basin","postsyn_basin"]


def infer_edges(net, img, cleft, seg, offset, patchsz, wshed=None,
                samples_per_cleft=2, dil_param=5, cleft_ids=None ):
    """
    Runs a trained network over the psds within the valid range
    of the dataset and infers the synaptic partners involved at each synapse

    Returns a DataFrame mapping psd segment id to a tuple of synaptic
    partners (presynaptic,postsynaptic)
    """


    if cleft_ids is None:
        cleft_ids = seg_utils.nonzero_unique_ids(cleft)


    cleft_locs = pick_cleft_locs(cleft, cleft_ids, samples_per_cleft)

    record_basins = wshed is not None

    edges = [] #list of dict records
    for (cid, locs) in cleft_locs.items():

        seg_weights, seg_szs, seg_locs = {},{},{}
        for loc in locs:
            box = random_box(patchsz, cleft, loc)
            box_offset = box.min() + offset

            img_p, clf_p, seg_p = get_patches(img, cleft, seg, box, cid)

            segids = find_close_segments(clf_p, seg_p, dil_param)

            new_weights, new_szs = infer_patch_weights(net, img_p, clf_p,
                                                       seg_p, segids)
            seg_weights, seg_szs = dict_tuple_avg(new_weights, new_szs,
                                                  seg_weights, seg_szs)

            new_locs = random_locs(seg_p[0,0,:].transpose((2,1,0)),
                                   segids, offset=box_offset)
            seg_locs = update_locs(new_locs, seg_locs)

        if len(seg_weights) == 0: #hallucinated synapse - or no segmentation
            continue

        pre_seg, post_seg, pre_w, post_w = make_assignment(seg_weights)
        pre_loc, post_loc = seg_locs[pre_seg], seg_locs[post_seg]
        pre_sz,  post_sz = seg_szs[pre_seg],  seg_szs[post_seg]

        if record_basins:
            pre_basin = pull_basin(wshed, pre_loc, offset)
            post_basin = pull_basin(wshed, post_loc, offset)

            edges.append(make_record(cid, pre_seg, post_seg,
                                     pre_loc, post_loc, pre_w, post_w,
                                     pre_sz, post_sz, pre_basin, post_basin))
        else:
            edges.append(make_record(cid, pre_seg, post_seg,
                                     pre_loc, post_loc,
                                     pre_w, post_w,
                                     pre_sz, post_sz))

    return make_record_dframe(edges, record_basins)


def infer_whole_edge(net, img, cleft, seg, cleft_id, patchsz, dil_param=5):

    cleft_mask = cleft == cleft_id

    seg_weights, seg_szs, seg_locs = {}, {}, {}
    while cleft_mask.max():

        loc = pick_cleft_locs(cleft_mask, [True], 1)[True][0]

        box = random_box(patchsz, cleft, loc)
        box_offset = box.min()
        cleft_mask[box.index()] = False

        img_p, clf_p, seg_p = get_patches(img, cleft, seg, box, cleft_id)

        segids = find_close_segments(clf_p, seg_p, dil_param)

        new_weights, new_szs = infer_patch_weights(net, img_p, clf_p,
                                                   seg_p, segids)
        seg_weights, seg_szs = dict_tuple_avg(new_weights, new_szs,
                                              seg_weights, seg_szs)

        new_locs = random_locs(seg_p[0,0,:].transpose((2,1,0)),
                               segids, offset=box_offset)
        seg_locs = update_locs(new_locs, seg_locs)

    return seg_weights, seg_szs, seg_locs


def pick_cleft_locs(cleft, cleft_ids, num_locs):

    order = np.argsort(cleft.flat)

    first = np.searchsorted(cleft.flat, cleft_ids, "left", order)
    last  = np.searchsorted(cleft.flat, cleft_ids, "right", order)
    bounds = list(zip(first, last))

    indices = { i : list() for i in cleft_ids }
    for (i,cid) in enumerate(cleft_ids):
        lo, hi = bounds[i]
        for j in range(num_locs):
            linear_index = order[random.randint(lo, hi-1)]
            indices[cid].append( np.unravel_index(linear_index, cleft.shape) )

    return indices


def random_box(box_shape, seg, loc):
    """ Returns a BBox3d containing loc within a segmentation """
    return bbox.containing_box(loc, box_shape, seg.shape)


def random_loc(seg, i, offset=(0,0,0)):
    """ Finds a random location where (np array) seg == i """

    start = time.time()
    xs,ys,zs = np.nonzero(seg == i)
    assert len(xs) > 0, "{} not contained in volume".format(i)

    i = random.choice(range(len(xs)))

    return (xs[i]+offset[0],ys[i]+offset[1],zs[i]+offset[2])


def random_locs(seg, segids, offset=(0,0,0)):
    return {segid: random_loc(seg, segid, offset) for segid in segids}


def infer_patch_weights(net, img_p, psd_p, seg_p, segids=None):
    return seg_weights( infer_patch(net, img_p, psd_p), seg_p, segids )


def get_patches(img, psd, seg, box, psdid):
    """ Return 5d patches specified by the bbox for use in torch """

    img_p =  img[box.index()] / 255.0
    psd_p = (psd[box.index()] == psdid).astype("float32")
    seg_p =  seg[box.index()]

    #transposing to fit net's conventions
    img_p = img_p.transpose((2,1,0))
    psd_p = psd_p.transpose((2,1,0))
    seg_p = seg_p.transpose((2,1,0))

    #add two dims to each for torch
    img_p =  img_p[np.newaxis, np.newaxis, :]
    psd_p =  psd_p[np.newaxis, np.newaxis, :]
    seg_p =  seg_p[np.newaxis, np.newaxis, :]

    return img_p, psd_p, seg_p


def find_close_segments(psd_p, seg_p, dil_param):

    kernel = make_dilation_kernel(dil_param).astype("float32")

    psd_mask = torch_dilation( psd_p, kernel, dil_param )

    return seg_utils.nonzero_unique_ids( seg_p[psd_mask] )


def torch_dilation(seg, kernel, dil_param):

    seg_v = make_variable( seg, volatile=True )
    ker_v = make_variable( kernel, volatile=True )
    sz = kernel.shape
    padding = (sz[2]//2,sz[3]//2,sz[4]//2)

    output = torch.nn.functional.conv3d( seg_v, ker_v, padding=padding )

    return output.data.cpu().numpy().astype("bool")


def make_dilation_kernel(dil_param):

    kernel = ndimage.generate_binary_structure(2,1)
    kernel = ndimage.iterate_structure(kernel, dil_param)
    z_component = np.zeros(kernel.shape, dtype=kernel.dtype)

    width = kernel.shape[-1]
    mid = width//2

    z_component[mid,mid] = 1
    kernel = np.stack((z_component,kernel,z_component),axis=0)
    return kernel.reshape((1,1,3,width,width))


def infer_patch(net, img_p, psd_p):
    """
    Runs an assignment network over a single patch, and returns
    the weights over each segment within the passed segmentation patch

    Returns 4d output
    """
    #formatting
    net_input = np.concatenate((img_p,psd_p), axis=1).astype("float32")
    net_input = make_variable(net_input, volatile=True)

    #network has only one output
    # and batch size = 1
    output = F.sigmoid(net( net_input )[0])[0,:,:,:,:]

    return output


def seg_weights( output, seg, segids=None ):
    """
    Finds the sum over the pre and post synaptic weights
    contained in each segment of seg

    output should be a torch.cuda Tensor, and
    seg should be a numpy array
    """

    if segids is None:
        segids = seg_utils.nonzero_unique_ids(seg)

    weights = {}
    sizes = {}

    presyn_output  = output[0,:,:,:]
    postsyn_output = output[1,:,:,:]

    for i in segids:

        seg_mask = torch.from_numpy((seg == i).astype("uint8")).cuda()
        sizes[i] = torch.sum(seg_mask)

        pre_avg  = torch.sum(presyn_output[seg_mask]).data[0] / sizes[i]
        post_avg = torch.sum(postsyn_output[seg_mask]).data[0] / sizes[i]

        weights[i] = (pre_avg, post_avg)

    return weights, sizes


def dict_tuple_avg(d1, s1, d2, s2):
    """
    Averages the 2-tuple entry of each dict together weighted by size
    if a key doesn't exist in either dict, it assumes the default
    value (0,0)

    Assumes that each pair of dictionaries (e.g. d1 and s1) has identical keys
    """

    weights = copy.copy(d1)
    sizes   = copy.copy(s1)

    for (k,v) in d2.items():
        if k in weights:

            nv, ns = d2[k],s2[k]
            ov, os = weights[k], sizes[k]

            sz = sizes[k] = os + ns

            weights[k] = ( (ov[0]*os+nv[0]*ns)/sz,
                           (ov[1]*os+nv[1]*ns)/sz )
        else:
            weights[k] = v
            sizes[k]   = s2[k]

    return weights, sizes


def dict_tuple_sum(d1, d2):

    weights = copy.copy(d1)

    for (k,v) in d2.items():
        if k in weights:
            weights[k] += v
        else:
            weights[k] = v

    return weights


def update_locs(new_locs, all_locs):

    for (k,v) in new_locs.items():
        all_locs[k] = v

    return all_locs


def pull_basin(wshed, loc, offset=(0,0,0)):
    return wshed[tuple(map(operator.sub,loc,offset))]


def make_assignment(weights):
    """
    Assigns a synapse to partners

    The synapse is represented by a dict of
      segid => (pre_weight, post_weight)
    """

    #lists of tuple (segid, weight)
    pre_weights = []
    post_weights = []

    for (k,v) in weights.items():
        pre, post = v
        pre_weights.append((k,pre))
        post_weights.append((k,post))


    pre_seg,  pre_weight  = max(pre_weights,  key=operator.itemgetter(1))
    post_seg, post_weight = max(post_weights, key=operator.itemgetter(1))

    return pre_seg, post_seg, pre_weight, post_weight


def make_record(psdid,
                pre_seg, post_seg,
                pre_loc, post_loc,
                pre_weight, post_weight,
                pre_size, post_size,
                pre_basin=None, post_basin=None):

    data = [psdid,            pre_seg,      post_seg,
            pre_loc[0],       pre_loc[1],   pre_loc[2],
            post_loc[0],      post_loc[1],  post_loc[2],
            pre_weight,       post_weight,
            pre_size,         post_size]

    assert len(data) == len(RECORD_SCHEMA), "mismatched data and schema"

    if pre_basin is None:
        return dict(zip(RECORD_SCHEMA, data))

    else:
        assert post_basin is not None, "pre but no post basin"
        data += [pre_basin, post_basin]

        return dict(zip(SCHEMA_W_BASINS, data))



def make_record_dframe(record_list, record_basins=True):

    if len(record_list) == 0:
        if record_basins:
            return pd.DataFrame({k : {} for k in SCHEMA_W_BASINS})
        else:
            return pd.DataFrame({k : [] for k in RECORD_SCHEMA})
    else:
        return pd.DataFrame.from_records(record_list, index="cleft_segid")


def make_variable(np_arr, requires_grad=True, volatile=False):
    """ Creates a torch.autograd.Variable from a np array """
    if not volatile:
      return Variable(torch.from_numpy(np_arr.copy()), requires_grad=requires_grad).cuda()
    else:
      return Variable(torch.from_numpy(np_arr.copy()), volatile=True).cuda()
