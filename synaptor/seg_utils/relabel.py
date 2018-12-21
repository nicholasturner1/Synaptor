import numpy as np

from . import describe
from . import _relabel


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
    return _relabel.relabel_data(d, mapping)


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
    mapping = {v: i+1 for (i, v) in enumerate(describe.nonzero_unique_ids(d))}
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
