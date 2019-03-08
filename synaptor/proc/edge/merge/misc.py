""" Miscellaneous Functionality """


def update_id_map(id_map, next_map, reused_ids=False):

    # need to keep track of which keys are accounted
    # for within the current id_map
    new_keys = set(next_map.keys())

    for (k, v) in id_map.items():
        id_map[k] = next_map.get(v, v)
        new_keys.discard(v)

    # make a new mapping for each new key
    if not reused_ids:
        for k in new_keys:
            id_map[k] = next_map[k]

    return id_map


def expand_id_map(id_map, all_ids):
    """ Ensures all ids within all_ids are included as keys in the mapping """

    unmapped_ids = list(set(all_ids).difference(id_map.keys()))

    for i in unmapped_ids:
        id_map[i] = i

    return id_map
