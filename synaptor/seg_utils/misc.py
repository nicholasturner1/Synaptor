import numpy as np

from . import _seg_utils


def manhattan_dist2d(seg, modify_seg=False):
    """
    Compute the 2d Manhattan Distance.

    Computes the manhattan distance in 2d to the nearest segment.

    Args:
        seg (3darray): A volume segmentation.
        modify_seg (bool): Whether to replace seg values with nearest segment id.

    Returns:
        3darray: The 2d Manhattan Distance to the nearest segment.
        3darray: The nearest segment from each voxel.
    """
    dists = np.empty_like(seg)

    if not modify_seg:
        seg = np.copy(seg)

    return _seg_utils.manhattan_dist2d(seg, dists), seg


def dilate_by_k(seg, k, copy=True):
    """
    Dilate a segment by k in 2d Manhattan Distance.

    Args:
        seg (3darray): A volume segmentation.
        k (int): The amount to dilate each segment.
        copy (bool): Whether to modify the segmentation in-place. 
            Defaults to True, which will create a new volume.

    Returns:
        3darray: :param: seg dilated by k in 2d Manhattan Distance.              
    """
    dists = np.empty_like(seg)

    if copy:
        seg = np.copy(seg)

    return _seg_utils.dilate_by_k(seg, dists, k)
