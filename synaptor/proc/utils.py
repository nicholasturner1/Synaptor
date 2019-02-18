import itertools

import numpy as np
import pandas as pd
import igraph


def merge_info_df(df, id_map, merge_fn):

    to_drop = []
    new_rows = {}
    indices = set([])

    for (k,v) in id_map.items():
        if k == v:
            continue

        if v in new_rows:
            row_v = new_rows[v]
        else:
            row_v = df.loc[v]

        new_rows[v] = merge_fn(df.loc[k], row_v)

        to_drop.append(k)
        indices.add(v)

    if len(new_rows) > 0:
        index = sorted(list(indices))
        replacements = pd.DataFrame.from_dict(new_rows, orient="index")

        # indexing by columns ensures that they have the same order
        df.loc[index] = replacements[df.columns]
        df.drop(to_drop, inplace=True)

    return df


def find_connected_components(matches):

    all_ids = list(set(itertools.chain(*matches)))
    vertex_mapping = { segid: i for (i,segid) in enumerate(all_ids) }

    g = igraph.Graph(len(all_ids))
    g.vs["ids"] = all_ids

    mapped_edges = map(lambda x: (vertex_mapping[x[0]],vertex_mapping[x[1]]),
                       matches)

    g.add_edges(mapped_edges)

    vertex_ccs = g.components()

    # This is horribly slow for some reason
    # orig_ccs = [g.vs[cc]["ids"] for cc in vertex_ccs]
    orig_ccs = deal_cc_ids(g, vertex_ccs)

    return orig_ccs


def deal_cc_ids(g, vertex_ccs, ids_key="ids"):

    #Init bookkeeping objects
    mapping = np.zeros((len(g.vs),), dtype=np.uint32)
    cc_ids = [list() for _ in range(len(vertex_ccs))]

    for (cc_i,cc) in enumerate(vertex_ccs):
        for seg_j in cc:
            mapping[seg_j] = cc_i

    for (segid, cc) in zip(g.vs[ids_key], iter(mapping)):
        cc_ids[cc].append(segid)

    return cc_ids


def make_id_map(ccs):

    mapping = {}

    for cc in ccs:
        target = min(cc)

        for i in cc:
            mapping[i] = target

    return mapping


def weighted_avg(com1, sz1, com2, sz2):

    frac1 = sz1 / (sz1+sz2)
    frac2 = sz2 / (sz1+sz2)

    h1 = (com1[0]*frac1, com1[1]*frac1, com1[2]*frac1)
    h2 = (com2[0]*frac2, com2[1]*frac2, com2[2]*frac2)

    return (h1[0]+h2[0], h1[1]+h2[1], h1[2]+h2[2])
