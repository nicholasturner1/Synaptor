#!/usr/bin/env python3
__doc__ = """
Merging Cleft Info Dataframes with Edge Information ("Full" Dataframes)

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import pandas as pd

from ....types import bbox
from ... import utils
from ...utils import schema as sch


RECORD_KEYS = [sch.presyn_id, sch.postsyn_id,
               *sch.presyn_coord_cols, *sch.postsyn_coord_cols,
               sch.presyn_wt, sch.postsyn_wt,
               sch.presyn_sz, sch.postsyn_sz,
               sch.size]
BASIN_KEYS = sch.basin_cols


def merge_full_df(full_info_df, id_map):
    return utils.merge_info_df(full_info_df, id_map, merge_full_records)


def merge_full_df1(full_info_df, id_map):

    new_ids = pd.DataFrame.from_dict(id_map, orient="index")

    if len(new_ids) == 0:
        return full_info_df

    full_info_df["new_ids"] = new_ids
    full_info_df = full_info_df.reset_index()

    # computing grouped stats
    grouped = full_info_df.groupby("new_ids")
    szs = grouped[sch.size].sum()
    bbox1 = grouped[sch.bbox_cols[:3]].min()
    bbox2 = grouped[sch.bbox_cols[-3:]].max()
    coms = compute_centroids(full_info_df, szs)

    # setting index to the original if not remapped
    no_new_id = pd.isnull(full_info_df["new_ids"])
    full_info_df.loc[no_new_id, "new_ids"] = full_info_df.loc[no_new_id,
                                                              sch.cleft_id]
    # taking all other fields from largest cleft
    new_df = full_info_df.sort_values([sch.size]).drop_duplicates("new_ids")

    # recreating index
    new_df = new_df.drop([sch.cleft_id], axis=1)
    new_df = new_df.rename(columns={"new_ids": sch.cleft_id})
    new_df = new_df.set_index(sch.cleft_id)

    new_df.update(coms)
    new_df.update(bbox1)
    new_df.update(bbox2)
    new_df.update(szs)

    return new_df


def compute_centroids(df, szs):

    szs = szs.reset_index()
    szs = szs.rename(columns={sch.size: "total_size"})

    centroid_df = pd.merge(df[sch.centroid_cols + [sch.size, "new_ids"]], szs,
                           how="left", on="new_ids")

    # This will create NANs, but those will disappear after grouping
    centroid_df[sch.size] /= centroid_df["total_size"]

    centroid_df[sch.centroid_x] *= centroid_df[sch.size]
    centroid_df[sch.centroid_y] *= centroid_df[sch.size]
    centroid_df[sch.centroid_z] *= centroid_df[sch.size]

    return centroid_df.groupby("new_ids")[sch.centroid_cols].sum()


def merge_full_records(record1, record2):

    record_dict1 = unwrap_row(record1)
    record_dict2 = unwrap_row(record2)

    # Pick the aux params for the larger cleft
    if record_dict1[sch.size] > record_dict2[sch.size]:
        base_dict = record_dict1
    else:
        base_dict = record_dict2

    sz1, sz2 = record_dict1[sch.size], record_dict2[sch.size]
    com1, com2 = record_dict1["COM"], record_dict2["COM"]
    bb1, bb2 = record_dict1["BBOX"], record_dict2["BBOX"]

    base_dict[sch.size] = sz1 + sz2
    base_dict["COM"] = utils.weighted_avg(com1, sz1, com2, sz2)
    base_dict["BBOX"] = bb1.merge(bb2)

    return wrap_row(base_dict)


def unwrap_row(df_row):

    com = tuple(df_row[col] for col in sch.centroid_cols)

    bb_b = tuple(df_row[col] for col in sch.bbox_cols[:3])
    bb_e = tuple(df_row[col] for col in sch.bbox_cols[3:])
    bb = bbox.BBox3d(bb_b, bb_e)

    complete_row = {k: df_row[k] for k in RECORD_KEYS}
    complete_row["COM"] = com
    complete_row["BBOX"] = bb

    # Adding watershed basins if they're in the row
    for k in BASIN_KEYS:
        if k in df_row:
            complete_row[k] = df_row[k]

    return complete_row


def wrap_row(row_dict):

    new_row = {k: row_dict[k] for k in RECORD_KEYS}

    (new_row[sch.centroid_x],
     new_row[sch.centroid_y],
     new_row[sch.centroid_z]) = row_dict["COM"]
    (new_row[sch.bbox_bx],
     new_row[sch.bbox_by],
     new_row[sch.bbox_bz]) = row_dict["BBOX"].min()
    (new_row[sch.bbox_ex],
     new_row[sch.bbox_ey],
     new_row[sch.bbox_ez]) = row_dict["BBOX"].max()

    # Adding watershed basins if they're in the row
    for k in BASIN_KEYS:
        if k in row_dict:
            new_row[k] = row_dict[k]

    return new_row
