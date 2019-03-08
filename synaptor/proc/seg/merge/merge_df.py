""" Merging Segment Info Dataframes. """


import pandas as pd

from ... import colnames as cn


def merge_seginfo_df(seginfo_df, new_id_colname="new_ids"):

    seginfo_df = seginfo_df.reset_index()
    if "index" in seginfo_df.columns:
        seginfo_df = seginfo_df.drop(["index"], axis=1)

    # computing grouped stats
    grouped = seginfo_df.groupby(new_id_colname)
    szs = grouped[cn.size].sum()
    bbox1 = grouped[cn.bbox_cols[:3]].min()
    bbox2 = grouped[cn.bbox_cols[-3:]].max()
    coms = compute_centroids(seginfo_df, szs, new_id_colname=new_id_colname)

    # setting index to the original if not remapped
    no_new_id = pd.isnull(seginfo_df[new_id_colname])
    seginfo_df.loc[no_new_id, new_id_colname] = seginfo_df.loc[no_new_id,
                                                              cn.seg_id]
    # taking all other fields from largest cleft
    new_df = seginfo_df.sort_values([cn.size]).drop_duplicates(new_id_colname)

    # recreating index
    new_df = new_df.drop([cn.seg_id], axis=1)
    new_df = new_df.rename(columns={new_id_colname: cn.seg_id})
    new_df = new_df.set_index(cn.seg_id)

    new_df.update(coms)
    new_df.update(bbox1)
    new_df.update(bbox2)
    new_df.update(szs)

    return new_df


def compute_centroids(df, szs, new_id_colname="new_ids"):

    szs = szs.reset_index()
    szs = szs.rename(columns={cn.size: "total_size"})

    centroid_df = pd.merge(df[cn.centroid_cols + [cn.size, new_id_colname]],
                           szs, how="left", on=new_id_colname)

    # This will create NANs, but those will disappear after grouping
    centroid_df[cn.size] /= centroid_df["total_size"]

    centroid_df[cn.centroid_x] *= centroid_df[cn.size]
    centroid_df[cn.centroid_y] *= centroid_df[cn.size]
    centroid_df[cn.centroid_z] *= centroid_df[cn.size]

    return centroid_df.groupby(new_id_colname)[cn.centroid_cols].sum().astype(int)


def enforce_size_threshold(seginfo_df, size_thr):
    violations = seginfo_df.index[seginfo_df[cn.size] < size_thr]
    seginfo_df.drop(violations.tolist(), inplace=True)

    return {v: 0 for v in violations}
