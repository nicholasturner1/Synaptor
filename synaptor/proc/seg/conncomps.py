""" Connected Components """


import numpy as np
from scipy import ndimage
import cc3d

from ... import seg_utils


def connected_components(d, thresh=0, overlap_seg=None, dtype=np.uint32):
    """
    Performs basic connected components on network
    output given a threshold value. Returns the components
    as a desired datatype (default: np.uint32)
    """
    mask = d > thresh

    if overlap_seg is None:
        # C-order speeds up continuation extraction by a LOT
        mask = np.ascontiguousarray(mask)
        return cc3d.connected_components(mask, connectivity=6).astype(dtype)

    else:
        temp = np.zeros(d.shape, dtype=overlap_seg.dtype, order='C')
        temp[mask] = overlap_seg[mask]

        return cc3d.connected_components(temp, connectivity=6).astype(dtype)



def dilated_components(output, dil_param, cc_thresh):
    """
    Performs a version of connected components with dilation

    Expands the voxels over threshold by dil_param in 2D
    Runs connected components on the dilated mask
    Removes the voxels which weren't originally above threshold
    """

    if dil_param == 0:
        return connected_components(output, cc_thresh)

    mask = output > cc_thresh

    dil_mask = seg_utils.dilate_by_k(mask, dil_param)
    ccs = connected_components(dil_mask, 0)

    # Removing dilated voxels
    ccs[mask == 0] = 0

    return ccs


def dilate_mask_by_k(d, k):
    """ Dilates a volume of data by k """
    kernel = make_dilation_kernel(k)

    return ndimage.binary_dilation(d, structure=kernel)


def make_dilation_kernel(k):
    """ 2D Manhattan Distance Kernel """
    kernel = ndimage.generate_binary_structure(2, 1)

    return ndimage.iterate_structure(kernel, k)[np.newaxis, :, :]
