from collections import Counter

import numpy as np
from scipy import ndimage
from scipy import sparse

from . import _seg_utils
from .. import bbox


def relabel_data(d, mapping, copy=True):
    """
    Relabel data according to a mapping dict.

    Modify the entries of :param:d according to a :param:mapping dictionary.
    If a value within :param:d doesn't match a key for :param:mapping,
    leave it unchanged.

    Args:
        d (3darray): A data volume.
        mapping (dict): A mapping from data values in d to new desired values.
        copy (bool): Whether or not to perform relabeling in-place. Defaults
            to True, which will create a new volume.

    Returns:
        3darray: A modified or newly created volume with the
            desired modifications.
    """
    if copy:
        d = np.copy(d)
    return _seg_utils.relabel_data(d, mapping)


def relabel_data_1N(d, copy=True):
    """
    Relabel segment values from 1:N

    Args:
        d (3darray): A segmentation.
        copy (bool): Whether or not to perform relabeling in-place. Defaults
            to True, which will create a new volume.

    Returns:
        3darray: A modified or newly created volume with new segids.
    """
    mapping = {v: i+1 for (i, v) in enumerate(nonzero_unique_ids(d))}
    return relabel_data(d, mapping, copy=copy)


def relabel_data_iterative(d, mapping):
    """
    Python-based iterative relabeling

    Remapping data according to an id mapping using an iterative strategy.
    Best when only modifying a few ids. If a value within d doesn't match
    a key for mapping, leave it unchanged.

    Args:
        d (3darray): A segmentation.
        mapping (dict): A mapping from data values in d to new desired values.

    Returns:
        3darray: A new volume with the desired modifications.
    """
    r = np.copy(d)

    src_ids = set(np.unique(d))
    mapping = dict(filter(lambda x: x[0] in src_ids, mapping.items()))

    for (k, v) in mapping.items():
        r[d == k] = v
    return r


def relabel_data_lookup_arr(d, mapping):
    """
    Python-based lookup array relabeling

    Remapping data according to an id mapping using a lookup np array.
    Best when modifying several ids at once and ids are approximately dense
    within 1:max

    Args:
        d (3darray): A segmentation.
        mapping (dict): A mapping from data values in d to new desired values.

    Returns:
        3darray: A new volume with the desired modifications.
    """

    if len(mapping) == 0:
        return d

    map_keys = np.array(list(mapping.keys()))
    map_vals = np.array(list(mapping.values()))

    map_arr = np.arange(0, d.max()+1)
    map_arr[map_keys] = map_vals
    return map_arr[d]


def split_by_overlap(seg_to_split, overlap_seg, copy=True):
    """
    Split segments by overlap with a separate segmentation.

    Args:
        seg_to_split (3darray): A segmentation to split.
        overlap_seg (3darray): A segmentation which determines splits.
        copy (bool): Whether to perform the splitting in-place.
            Defaults to True, which creates a new volume.

    Returns:
        3darray: A new volume with each segment in :param:seg_to_split assigned
            a new id based on its overlap with ids in :param:overlap_seg.
    """
    overlaps, row_ids, col_ids = count_overlaps(seg_to_split, overlap_seg)
    rs, cs, _ = sparse.find(overlaps)

    dict_of_dicts = dict((r, dict()) for r in row_ids)
    for (v, (r, c)) in enumerate(zip(rs, cs)):
        row = row_ids[r]
        col = col_ids[c]
        dict_of_dicts[row][col] = v+1

    if copy:
        seg_to_split = np.copy(seg_to_split)

    return _seg_utils.relabel_paired_data(seg_to_split,
                                          overlap_seg, dict_of_dicts)


def nonzero_unique_ids(seg):
    """ Find the nonzero ids in a np array. """
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
    centroids = _seg_utils.centers_of_mass(seg)

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


def filter_segs_by_size(seg, thresh, szs=None, to_ignore=None, copy=True):
    """
    Remove segments under a size threshold.

    Args:
        seg (3darray): A volume segmentation.
        thresh (int): A size threshold. All segments with a size under this
            value will be removed.
        szs (dict): A mapping from segment id to size. Defaults to None, in
            which case, it will be computed from seg.
        to_ignore (list): A list of segment ids to ignore. Defaults to None.
        copy (bool): Whether to perform the splitting in-place.
            Defaults to True, which creates a new volume.

    Returns:
        3darray: A volume segmentation with the segments of size under
            :param:thresh removed.
        dict: A mapping from segment id to size for the remaining segments.
    """
    if szs is None:
        szs = segment_sizes(seg)

    to_remove = set(map(lambda x: x[0],
                        filter(lambda pair: pair[1] < thresh, szs.items())))

    if to_ignore is not None:
        to_remove = to_remove.difference(to_ignore)

    remaining_sizes = dict(filter(lambda pair: pair[0] not in to_remove,
                                  szs.items()))

    if len(to_remove) > 0:
        return filter_segs_by_id(seg, to_remove, copy=copy), remaining_sizes
    else:
        return seg, remaining_sizes


def filter_segs_by_id(seg, ids, copy=True):
    """
    Remove segments with given ids.

    Args:
        seg (3darray): A volume segmentation.
        ids (list): A list of segment ids to remove.

    Returns:
        3darray: A volume segmentation with the desired segments removed.
    """
    removal_mapping = {v: 0 for v in ids}

    if len(removal_mapping) > 0:
        return relabel_data(seg, removal_mapping, copy=copy)
    else:
        return seg


def downsample_seg_to_mip(seg, mip_start, mip_end):
    """
    Downsample a segmentation to the desired mip level.

    Args:
        seg (3darray): A volume segmentation.
        mip_start (int): The MIP level of seg.
        mip_end (int): The desired MIP level.

    Returns:
        3darray: seg downsampled to :param: mip_end
    """
    assert mip_end > mip_start

    mip = mip_start
    while mip < mip_end:
        seg = downsample_seg(seg)
        mip += 1

    return seg


def downsample_seg(seg):
    """
    Apply the COUNTLESS algorithm slice-wise.

    See: https://towardsdatascience.com/countless-3d-vectorized-2x-downsampling-of-labeled-volume-images-using-python-and-numpy-59d686c2f75 # noqa

    Args:
        seg (3darray): A volume segmentation.

    Returns:
        3darray: A new volume segmentation downsampled by 2 in XY.
    """

    assert len(seg.shape) == 3, "need 3d vol"
    assert seg.shape[2] % 2 == 0, "need even dimensions"
    assert seg.shape[1] % 2 == 0, "need even dimensions"

    new_shape = (seg.shape[0]//2, seg.shape[1]//2, seg.shape[2])
    res = np.empty(new_shape, dtype=seg.dtype)

    for i in range(seg.shape[2]):
        res[..., i] = countless(seg[..., i])

    return res


def countless(data):
    """
    Apply the COUNTLESS algorithm to a single slice.

    Vectorized implementation of downsampling a 2D
    image by 2 on each side using Will Silversmith's COUNTLESS algorithm.
    See: https://towardsdatascience.com/countless-3d-vectorized-2x-downsampling-of-labeled-volume-images-using-python-and-numpy-59d686c2f75 # noqa

    Args:
        data (2darray): An image segmentation.

    Returns:
        2darray: A new image segmentation downsampled by 2 in XY.
    """
    # allows us to prevent losing 1/2 a bit of information
    # at the top end by using a bigger type. Without this
    # 255 is handled incorrectly.
    data, upgraded = upgrade_type(data)

    data = data + 1  # don't use +=, it will affect the original data.

    sections = []

    # This loop splits the 2D array apart into four arrays that are
    # all the result of striding by 2 and offset by (0,0), (0,1), (1,0),
    # and (1,1) representing the A, B, C, and D positions from Figure 1.
    factor = (2, 2)
    for offset in np.ndindex(factor):
        part = data[tuple(np.s_[o::f] for o, f in zip(offset, factor))]
        sections.append(part)

    a, b, c, d = sections

    ab_ac = a * ((a == b) | (a == c))  # PICK(A,B) || PICK(A,C) w/ optimization
    bc = b * (b == c)  # PICK(B,C)

    a = ab_ac | bc  # (PICK(A,B) || PICK(A,C)) or PICK(B,C)
    result = a + (a == 0) * d - 1  # (matches or d) - 1

    if upgraded:
        return downgrade_type(result)

    return result


def upgrade_type(arr):
    """ Represent an integer ndarray as a larger datatype."""
    dtype = arr.dtype

    if dtype == np.uint8:
        return arr.astype(np.uint16), True
    elif dtype == np.uint16:
        return arr.astype(np.uint32), True
    elif dtype == np.uint32:
        return arr.astype(np.uint64), True

    return arr, False


def downgrade_type(arr):
    """ Represent an integer ndarray as a smaller datatype. """
    dtype = arr.dtype

    if dtype == np.uint64:
        return arr.astype(np.uint32)
    elif dtype == np.uint32:
        return arr.astype(np.uint16)
    elif dtype == np.uint16:
        return arr.astype(np.uint8)

    return arr


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


def count_overlaps(seg1, seg2):
    """
    Computing an overlap matrix,

    Count the overlapping voxels for each pair of overlapping
    objects. Returns a scipy.sparse matrix

    Args:
        seg1 (3darray): A volume segmentation.
        seg2 (3darray): Another volume segmentation.

    Returns:
        scipy.sparse.coo_matrix: A representation of the overlaps
        1darray: The :param: seg1 ids represented by each row.
        1darray: The :param: seg2 ids represented by each column.
    """

    seg1_ids = nonzero_unique_ids(seg1)
    seg2_ids = nonzero_unique_ids(seg2)

    seg1_index = {v: i for (i, v) in enumerate(seg1_ids)}
    seg2_index = {v: i for (i, v) in enumerate(seg2_ids)}

    overlap_mask = np.logical_and(seg1 != 0, seg2 != 0)

    n_rows = seg1_ids.size
    n_cols = seg2_ids.size

    seg1_vals = seg1[overlap_mask]
    seg2_vals = seg2[overlap_mask]

    counts = Counter(zip(seg1_vals, seg2_vals))

    rs, cs, vs = [], [], []
    for ((r, c), v) in counts.items():
        # subtracting one from indices so val 1 -> index 0
        rs.append(seg1_index[r])
        cs.append(seg2_index[c])
        vs.append(v)

    overlap_mat = sparse.coo_matrix((vs, (rs, cs)), shape=(n_rows, n_cols))
    return overlap_mat, seg1_ids, seg2_ids


def upsample2d(seg):
    """
    A naive 2d upsampling

    Args:
        seg (3darray): A volume segmentation.

    Returns:
        3darray: A new volume segmentation upsampled by 2 in XY.
    """
    new_shape = tuple(bbox.Vec3d(seg.shape) * (2, 2, 1))
    ups = np.empty(new_shape, dtype=seg.dtype)

    ups[::2, ::2, :] = seg
    ups[1::2, ::2, :] = seg
    ups[::2, 1::2, :] = seg
    ups[1::2, 1::2, :] = seg

    return ups
