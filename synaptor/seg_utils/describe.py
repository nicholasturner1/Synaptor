import numpy as np
from scipy import ndimage

from . import _describe
from .. import bbox


def nonzero_unique_ids(seg):
    """ Find the nonzero ids in a segmentation. """
    ids = np.unique(seg)
    return ids[ids != 0]


def centers_of_mass(seg, offset=(0, 0, 0)):
    """
    Compute segment centroids.

    Args:
        seg (3darray): A volume segmentation.
        offset (tuple): A 3d coordinate offset for each centroid.

    Returns:
        dict: A mapping from segment id to centroid, where each
            coordinate has been shifted by :param: offset.
    """
    centroids = _describe.centers_of_mass(seg)

    if offset != (0, 0, 0):
        centroids = {i: (c[0]+offset[0], c[1]+offset[1], c[2]+offset[2])
                     for (i, c) in centroids.items()}

    return centroids


def bounding_boxes(ccs, offset=(0, 0, 0)):
    """
    Compute bounding boxes.

    Args:
        seg (3darray): A volume segmentation.
        offset (tuple): A 3d coordinate offset for each bounding box.

    Returns:
        dict: A mapping from segment id to bounding box, where each
            coordinate has been shifted by :param: offset.
    """
    ids = list(map(int, nonzero_unique_ids(ccs)))

    bbox_slices = ndimage.find_objects(ccs)

    bboxes = {i: bbox.BBox3d(bbox_slices[i-1]) for i in ids}

    if offset == (0, 0, 0):
        return bboxes

    shifted = {segid: bbox.translate(offset)
               for (segid, bbox) in bboxes.items()}

    return shifted


def segment_sizes(seg):
    """
    Compute the voxel counts of each nonzero segment.

    Args:
        seg (3darray): A volume segmentation.
        offset (tuple): A 3d coordinate offset for each bounding box.

    Returns:
        dict: A mapping from segment id to voxel count.
    """
    # unique is best for this since it works over arbitrary vals
    ids, sizes = np.unique(seg, return_counts=True)
    size_dict = {i: sz for (i, sz) in zip(ids, sizes)}

    if 0 in size_dict:
        del size_dict[0]

    return size_dict


def label_surfaces3d(seg):
    """
    Label the voxels which change label in any dimension.

    Args:
        seg (3darray): A volume segmentation

    Returns:
        3darray: A surface mask filled with the values from :param: seg.
    """
    surface_mask = np.zeros(seg.shape, dtype=np.bool)

    # Z
    surface_mask[1:, :, :] = seg[1:, :, :] != seg[:-1, :, :]
    surface_mask[:-1, :, :] = np.logical_or(surface_mask[:-1, :, :],
                                            seg[:-1, :, :] != seg[1:, :, :])

    # Y
    surface_mask[:, 1:, :] = np.logical_or(surface_mask[:, 1:, :],
                                           seg[:, 1:, :] != seg[:, :-1, :])
    surface_mask[:, :-1, :] = np.logical_or(surface_mask[:, :-1, :],
                                            seg[:, :-1, :] != seg[:, 1:, :])

    # X
    surface_mask[:, :, 1:] = np.logical_or(surface_mask[:, :, 1:],
                                           seg[:, :, 1:] != seg[:, :, :-1])
    surface_mask[:, :, :-1] = np.logical_or(surface_mask[:, :, :-1],
                                            seg[:, :, :-1] != seg[:, :, 1:])

    surface_voxels = np.zeros(seg.shape, dtype=seg.dtype)

    surface_voxels[surface_mask] = seg[surface_mask]

    return surface_voxels


def label_surfaces2d(seg):
    """
    Label the voxels which change label in XY.

    Args:
        seg (3darray): A volume segmentation

    Returns:
        3darray: A 2d surface mask filled with the values from :param: seg.
    """
    surface_mask = np.zeros(seg.shape, dtype=np.bool)

    # Y
    surface_mask[:, 1:, :] = np.logical_or(surface_mask[:, 1:, :],
                                           seg[:, 1:, :] != seg[:, :-1, :])
    surface_mask[:, :-1, :] = np.logical_or(surface_mask[:, :-1, :],
                                            seg[:, :-1, :] != seg[:, 1:, :])

    # X
    surface_mask[:, :, 1:] = np.logical_or(surface_mask[:, :, 1:],
                                           seg[:, :, 1:] != seg[:, :, :-1])
    surface_mask[:, :, :-1] = np.logical_or(surface_mask[:, :, :-1],
                                            seg[:, :, :-1] != seg[:, :, 1:])

    surface_voxels = np.zeros(seg.shape, dtype=seg.dtype)

    surface_voxels[surface_mask] = seg[surface_mask]

    return surface_voxels
