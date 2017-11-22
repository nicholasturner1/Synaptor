#!/usr/bin/env python

import numpy as np
from scipy import ndimage

#import box


def connected_components3D(d, thresh=0):
    """
    Performs basic connected components on network
    output given a threshold value
    """
    return ndimage.label(d > thresh)[0]


def dilate_by_k(d, k):
    """"""
    kernel = make_dilation_kernel(k)
    return ndimage.grey_dilation(d, structure=kernel)


def make_dilation_kernel(k):
    """ 2D Manhattan Distance Kernel """

    kernel = ndimage.generate_binary_structure(2,1)
    return ndimage.iterate_structure(kernel, k)[np.newaxis,:,:]


def relabel_data_iterative(d,mapping):
    """
    Remapping data according to an id mapping using an iterative strategy.
    Best when only modifying a few ids
    """
    r = np.copy(d)
    for k,v in mapping.items():
        r[d==k] = v
    return r


def relabel_data_lookup_arr(d,mapping):
    """
    Remapping data according to an id mapping using a lookup np array.
    Best when modifying several ids at once and ids are approximately dense
    within 1:max
    """
    map_keys = np.array(list(mapping.keys()))
    map_vals = np.array(list(mapping.values()))

    map_arr = np.arange(0,d.max()+1)
    map_arr[map_keys] = map_vals
    return map_arr[d]


def nonzero_unique_ids(seg):
    ids = np.unique(seg)
    return ids[ids!=0]


def centers_of_mass(ccs, ids=None):

    if ids is None:
        ids = nonzero_unique_ids(ccs)

    coords = ndimage.measurements.center_of_mass(ccs,ccs,ids)
    #not sure if I should add one or not to be consistent - will test
    #add_one = lambda x: (x[0]+1,x[1]+1,x[2]+1)
    #return list(map(add_one, coords))
    return coords


def bounding_boxes(ccs):

    ids = nonzero_unique_ids(ccs)

    std_mapping = { v : i+1 for (i,v) in enumerate(ids) }
    standardized = relabel_data_iterative(ccs, std_mapping)

    bbox_slices = ndimage.find_objects(standardized)

    # bboxes = { v : bbox.BBox(bbox_slices[i]) for (i,v) in enumerate(ids) }
    bboxes = { v : bbox_slices[i] for (i,v) in enumerate(ids) }

    return bboxes


def segment_sizes(seg):
    """ Computes the voxel sizes of each nonzero segment """

    #unique is best for this since it works over arbitrary vals
    ids, sizes = np.unique(seg, return_counts=True)
    size_dict = { i : sz  for (i,sz) in zip(ids,sizes) }

    if 0 in size_dict:
        del size_dict[0]

    return size_dict


def filter_segs_by_size(seg, thresh, szs=None):

    if szs is None:
        szs = segment_sizes(seg)

    to_remove = list(map(lambda x: x[0],
                         filter( lambda pair: pair[1] < thresh, szs.items())))

    return filter_segs_by_id(seg, to_remove)


def filter_segs_by_id(seg, ids):

    removal_mapping = { v : 0 for v in ids }

    return relabel_data_lookup_arr(seg, removal_mapping)
