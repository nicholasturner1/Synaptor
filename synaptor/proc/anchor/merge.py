def merge_anchors(anchor_dframes, edge_dframe):

    df = pd.concat(anchor_dframes, copy=False)

    df[df["presyn_x"] != -2]  # error code for no point

    return df.groupby("cleft_segid.1").first()  # take random valid pt


def merge_to_edge_df(anchor_dframe, edge_dframe):

    df = pd.merge(anchor_dframe, edge_dframe, copy=False,
                  left_index=True, right_index=True)

    #df.drop(["
