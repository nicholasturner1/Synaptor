#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
__doc__ = """
Connected Components

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


import numpy as np
from scipy import ndimage


def dilated_components(output, dil_param, cc_thresh):
    """
    Performs a version of connected components with dilation

    Expands the voxels over threshold by dil_param in 2D
    Runs connected components on the dilated mask
    Removes the voxels which weren't originally above threshold
    """

    if dil_param == 0:
        return connected_components3d(output, cc_thresh)

    mask = output > cc_thresh

    dil_mask = dilate_mask_by_k(mask, dil_param)
    ccs = connected_components3d(dil_mask, 0)

    #Removing dilated voxels
    ccs[mask == 0] = 0

    return ccs


def connected_components3d(d, thresh=0):
    """
    Performs basic connected components on network
    output given a threshold value
    """
    if thresh != 0:
        return ndimage.label(d > thresh)[0]
    else:
        return ndimage.label(d)[0]


def dilate_mask_by_k(d, k):
    """ Dilates a volume of data by k """
    kernel = make_dilation_kernel(k)
    return ndimage.binary_dilation(d, structure=kernel)


def make_dilation_kernel(k):
    """ 2D Manhattan Distance Kernel """
    kernel = ndimage.generate_binary_structure(2,1)
    return ndimage.iterate_structure(kernel, k)[np.newaxis,:,:]
