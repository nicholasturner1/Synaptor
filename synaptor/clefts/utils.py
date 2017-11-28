#!/usr/bin/env python3

import numpy as np
from scipy import ndimage

from .. import bbox


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


def centers_of_mass(ccs, offset=(0,0,0), ids=None):

    if ids is None:
        ids = nonzero_unique_ids(ccs)

    coords = ndimage.measurements.center_of_mass(ccs,ccs,ids)

    coords_dict = { i : tuple(map(int,coord))
                    for (i,coord) in zip(ids, coords) }

    if offset == (0,0,0):
        return coords_dict

    add_offset = lambda x: (x[0]+offset[0],
                            x[1]+offset[1],
                            x[2]+offset[2])

    return { i : add_offset(coord) for (i,coord) in coords_dict.items() }


def bounding_boxes(ccs, offset=(0,0,0)):

    ids = nonzero_unique_ids(ccs)

    std_mapping = { v : i+1 for (i,v) in enumerate(ids) }
    standardized = relabel_data_iterative(ccs, std_mapping)

    bbox_slices = ndimage.find_objects(standardized)

    bboxes = { v : bbox.BBox3d(bbox_slices[i]) for (i,v) in enumerate(ids) }

    if offset == (0,0,0):
        return bboxes

    shifted = { segid : bbox.translate(offset) 
                for (segid,bbox) in bboxes.items() }

    return shifted


def segment_sizes(seg):
    """ Computes the voxel sizes of each nonzero segment """

    #unique is best for this since it works over arbitrary vals
    ids, sizes = np.unique(seg, return_counts=True)
    size_dict = { i : sz  for (i,sz) in zip(ids,sizes) }

    if 0 in size_dict:
        del size_dict[0]

    return size_dict


def filter_segs_by_size(seg, thresh, szs=None, to_ignore=None):

    if szs is None:
        szs = segment_sizes(seg)

    to_remove = set(map(lambda x: x[0],
                        filter( lambda pair: pair[1] < thresh, szs.items())))

    if to_ignore is not None:
        to_remove = to_remove.difference(to_ignore)

    remaining_sizes = dict(filter(lambda pair: pair[0] not in to_remove, 
                                  szs.items()))

    return filter_segs_by_id(seg, to_remove), remaining_sizes


def filter_segs_by_id(seg, ids):

    removal_mapping = { v : 0 for v in ids }

    return relabel_data_lookup_arr(seg, removal_mapping)

