#!/usr/bin/env python3

def update_id_map(id_map, next_map, reused_ids=False):

    #need to keep track of which keys are accounted
    # for within the current id_map
    new_keys = set(next_map.keys())

    for (k,v) in id_map.items():
        id_map[k] = next_map.get(v,v)
        new_keys.discard(v)

    #make a new mapping for each new key
    if not reused_ids:
        for k in new_keys:
            id_map[k] = next_map[k]

    return id_map
