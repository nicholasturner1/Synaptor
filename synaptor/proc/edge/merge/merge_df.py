""" Merging Edge Assignments to Cleft Info Dataframes. """


import pandas as pd

from ....types import bbox
from ... import utils
from ... import colnames as cn


RECORD_KEYS = [cn.presyn_id, cn.postsyn_id,
               *cn.presyn_coord_cols, *cn.postsyn_coord_cols,
               cn.presyn_wt, cn.postsyn_wt,
               cn.presyn_sz, cn.postsyn_sz,
               cn.size]
BASIN_KEYS = cn.basin_cols


def merge_full_df(full_info_df, id_map):

    new_ids = pd.DataFrame.from_dict(id_map, orient="index")

    if len(new_ids) == 0:
        return full_info_df

    full_info_df["new_ids"] = new_ids
    full_info_df = full_info_df.reset_index()

    # computing grouped stats
    grouped = full_info_df.groupby("new_ids")
    szs = grouped[cn.size].sum()
    bbox1 = grouped[cn.bbox_cols[:3]].min()
    bbox2 = grouped[cn.bbox_cols[-3:]].max()
    coms = compute_centroids(full_info_df, szs)

    # setting index to the original if not remapped
    no_new_id = pd.isnull(full_info_df["new_ids"])
    full_info_df.loc[no_new_id, "new_ids"] = full_info_df.loc[no_new_id,
                                                              cn.seg_id]
    # taking all other fields from largest cleft
    new_df = full_info_df.sort_values([cn.size]).drop_duplicates("new_ids")

    # recreating index
    new_df = new_df.drop([cn.seg_id], axis=1)
    new_df = new_df.rename(columns={"new_ids": cn.seg_id})
    new_df = new_df.set_index(cn.seg_id)

    new_df.update(coms)
    new_df.update(bbox1)
    new_df.update(bbox2)
    new_df.update(szs)

    return new_df


def compute_centroids(df, szs):

    szs = szs.reset_index()
    szs = szs.rename(columns={cn.size: "total_size"})

    centroid_df = pd.merge(df[cn.centroid_cols + [cn.size, "new_ids"]], szs,
                           how="left", on="new_ids")

    # This will create NANs, but those will disappear after grouping
    centroid_df[cn.size] /= centroid_df["total_size"]

    centroid_df[cn.centroid_x] *= centroid_df[cn.size]
    centroid_df[cn.centroid_y] *= centroid_df[cn.size]
    centroid_df[cn.centroid_z] *= centroid_df[cn.size]

    return centroid_df.groupby("new_ids")[cn.centroid_cols].sum()
