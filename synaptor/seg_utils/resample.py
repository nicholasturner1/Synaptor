import numpy as np

from .. import bbox


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
