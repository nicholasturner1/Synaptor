import operator

from . import describe
from . import relabel


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
        szs = describe.segment_sizes(seg)

    to_remove = set(segid for (segid, sz) in szs.items() if sz < thresh)

    if to_ignore is not None:
        to_remove = to_remove.difference(to_ignore)

    remaining_sizes = {segid: sz for (segid, sz) in szs.items() 
                       if segid not in to_remove}

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
        return relabel.relabel_data(seg, removal_mapping, copy=copy)
    else:
        return seg
