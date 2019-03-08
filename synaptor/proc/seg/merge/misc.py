""" Miscellaneous Functionality """

import pandas as pd

from ... import colnames as cn


def make_map_dframe(id_map):
    mapping_dict = dict(enumerate(id_map.items()))
    df = pd.DataFrame.from_dict(mapping_dict, orient="index")
    df.columns = [cn.src_id, cn.dst_id]

    return df


def expand_id_map(id_map, all_ids):
    """ Ensures all ids within all_ids are included as keys in the mapping """

    unmapped_ids = list(set(all_ids).difference(id_map.keys()))

    for i in unmapped_ids:
        id_map[i] = i

    return id_map
