#!/usr/bin/env python3

#Pasteurize
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import dict
from builtins import zip
from builtins import map
from builtins import filter
from future import standard_library
standard_library.install_aliases()


import numpy as np
from scipy import ndimage

from . import _seg_utils
from .. import bbox
import time


def relabel_data(d,mapping, copy=True):
    """
    Remapping data according to an id mapping using cython loops
    """

    if copy:
        d = np.copy(d)
    return _seg_utils.relabel_data(d,mapping)


def relabel_data_iterative(d,mapping):
    """
    Remapping data according to an id mapping using an iterative strategy.
    Best when only modifying a few ids
    """
    r = np.copy(d)

    src_ids = set(np.unique(d))
    mapping = dict(filter(lambda x: x[0] in src_ids, mapping.items()))

    for k,v in mapping.items():
        r[d==k] = v
    return r


def relabel_data_lookup_arr(d,mapping):
    """
    Remapping data according to an id mapping using a lookup np array.
    Best when modifying several ids at once and ids are approximately dense
    within 1:max
    """

    if len(mapping) == 0:
        return d

    map_keys = np.array(list(mapping.keys()))
    map_vals = np.array(list(mapping.values()))

    map_arr = np.arange(0,d.max()+1)
    map_arr[map_keys] = map_vals
    return map_arr[d]


def nonzero_unique_ids(seg):
    """ Finds the nonzero ids in a np array """
    ids = np.unique(seg)
    return ids[ids!=0]


def centers_of_mass(ccs, offset=(0,0,0)):

    coords = _seg_utils.centers_of_mass(ccs, offset)

    #keeping the datatype consistent until we can test it
    coords_dict = { i : tuple(map(int,coord))
                    for (i,coord) in coords.items() }

    return coords_dict


def bounding_boxes(ccs, offset=(0,0,0)):

    ids = nonzero_unique_ids(ccs)

    bbox_slices = ndimage.find_objects(ccs)

    bboxes = { i : bbox.BBox3d(bbox_slices[i-1]) for i in ids }

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


def filter_segs_by_size(seg, thresh, szs=None, to_ignore=None, copy=True):

    if szs is None:
        szs = segment_sizes(seg)

    to_remove = set(map(lambda x: x[0],
                        filter( lambda pair: pair[1] < thresh, szs.items())))

    if to_ignore is not None:
        to_remove = to_remove.difference(to_ignore)

    remaining_sizes = dict(filter(lambda pair: pair[0] not in to_remove,
                                  szs.items()))

    if len(to_remove) > 0:
        return filter_segs_by_id(seg, to_remove, copy=copy), remaining_sizes
    else:
        return seg, remaining_sizes


def filter_segs_by_id(seg, ids, copy=True):

    removal_mapping = { v : 0 for v in ids }

    if len(removal_mapping) > 0:
        return relabel_data(seg, removal_mapping, copy=copy)
    else:
        return seg


def downsample_seg_to_mip(seg, mip_start, mip_end):
    """Downsamples a segmentation to the desired mip level"""

    assert mip_end > mip_start

    mip = mip_start
    while mip < mip_end:
        seg = downsample_seg(seg)
        mip += 1

    return seg


def downsample_seg(seg):
    """
    Applying the COUNTLESS algorithm slice-wise
    https://towardsdatascience.com/countless-3d-vectorized-2x-downsampling-of-labeled-volume-images-using-python-and-numpy-59d686c2f75
    """

    assert len(seg.shape) == 3, "need 3d vol"
    assert seg.shape[2] % 2 == 0, "need even dimensions"
    assert seg.shape[1] % 2 == 0, "need even dimensions"

    new_shape = (seg.shape[0]//2, seg.shape[1]//2, seg.shape[2])
    res = np.empty(new_shape, dtype=seg.dtype)

    for i in range(seg.shape[2]):
        res[...,i] = countless(seg[...,i])

    return res


def countless(data):
    """
    Vectorized implementation of downsampling a 2D
    image by 2 on each side using Will Silversmith's COUNTLESS algorithm.
    https://towardsdatascience.com/countless-3d-vectorized-2x-downsampling-of-labeled-volume-images-using-python-and-numpy-59d686c2f75

    data is a 2D numpy array with even dimensions.
    """
    # allows us to prevent losing 1/2 a bit of information
    # at the top end by using a bigger type. Without this 255 is handled incorrectly.
    data, upgraded = upgrade_type(data)

    data = data + 1 # don't use +=, it will affect the original data.

    sections = []

    # This loop splits the 2D array apart into four arrays that are
    # all the result of striding by 2 and offset by (0,0), (0,1), (1,0),
    # and (1,1) representing the A, B, C, and D positions from Figure 1.
    factor = (2,2)
    for offset in np.ndindex(factor):
        part = data[tuple(np.s_[o::f] for o, f in zip(offset, factor))]
        sections.append(part)

    a, b, c, d = sections

    ab_ac = a * ((a == b) | (a == c)) # PICK(A,B) || PICK(A,C) w/ optimization
    bc = b * (b == c) # PICK(B,C)

    a = ab_ac | bc # (PICK(A,B) || PICK(A,C)) or PICK(B,C)
    result = a + (a == 0) * d - 1 # (matches or d) - 1

    if upgraded:
        return downgrade_type(result)

    return result


def upgrade_type(arr):
    dtype = arr.dtype

    if dtype == np.uint8:
        return arr.astype(np.uint16), True
    elif dtype == np.uint16:
        return arr.astype(np.uint32), True
    elif dtype == np.uint32:
        return arr.astype(np.uint64), True

    return arr, False


def downgrade_type(arr):
  dtype = arr.dtype

  if dtype == np.uint64:
    return arr.astype(np.uint32)
  elif dtype == np.uint32:
    return arr.astype(np.uint16)
  elif dtype == np.uint16:
    return arr.astype(np.uint8)

  return arr


def label_surfaces3d(seg):

    surface_mask = np.zeros(seg.shape, dtype=np.bool)

    #Z
    surface_mask[1:,:,:] = seg[1:,:,:] != seg[:-1,:,:]
    surface_mask[:-1,:,:] = np.logical_or(surface_mask[:-1,:,:],
                                          seg[:-1,:,:] != seg[1:,:,:])

    #Y
    surface_mask[:,1:,:] = np.logical_or(surface_mask[:,1:,:],
                                         seg[:,1:,:] != seg[:,:-1,:])
    surface_mask[:,:-1,:] = np.logical_or(surface_mask[:,:-1,:],
                                          seg[:,:-1,:] != seg[:,1:,:])


    #X
    surface_mask[:,:,1:] = np.logical_or(surface_mask[:,:,1:],
                                         seg[:,:,1:] != seg[:,:,:-1])
    surface_mask[:,:,:-1] = np.logical_or(surface_mask[:,:,:-1],
                                          seg[:,:,:-1] != seg[:,:,1:])

    surface_voxels = np.zeros(seg.shape, dtype=seg.dtype)

    surface_voxels[surface_mask] = seg[surface_mask]

    return surface_voxels


def label_surfaces2d(seg):

    surface_mask = np.zeros(seg.shape, dtype=np.bool)

    #Y
    surface_mask[:,1:,:] = np.logical_or(surface_mask[:,1:,:],
                                         seg[:,1:,:] != seg[:,:-1,:])
    surface_mask[:,:-1,:] = np.logical_or(surface_mask[:,:-1,:],
                                          seg[:,:-1,:] != seg[:,1:,:])


    #X
    surface_mask[:,:,1:] = np.logical_or(surface_mask[:,:,1:],
                                         seg[:,:,1:] != seg[:,:,:-1])
    surface_mask[:,:,:-1] = np.logical_or(surface_mask[:,:,:-1],
                                          seg[:,:,:-1] != seg[:,:,1:])

    surface_voxels = np.zeros(seg.shape, dtype=seg.dtype)

    surface_voxels[surface_mask] = seg[surface_mask]

    return surface_voxels
