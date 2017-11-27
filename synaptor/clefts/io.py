#!/usr/bin/env python3


import os
import pandas as pd


from .. import io


COM_SCHEMA  = ["COM_x","COM_y","COM_z"]
BBOX_SCHEMA = ["BBOX_bx","BBOX_by","BBOX_bz",
               "BBOX_ex","BBOX_ey","BBOX_ez"]


def read_seg_infos(proc_dir_path):

    seg_info_dir = os.path.join(proc_dir_path,"seg_infos")
    fnames = io.pull_all_files(seg_info_dir, "seg_infos")

    starts  = [ io.bbox_from_fname(f).min() for f in fnames ]
    dframes = [ read_chunk_seg_info(f) for f in fnames ]

    return make_info_arr({s : df for (s,df) in zip(starts, dframes)})


def make_info_arr(start_lookup):

    ordering = sorted(start_lookup.keys())
    dims     = infer_dims(ordering)

    ordered = [start_lookup[k] for k in ordering]

    return np.array(ordered).reshape(dims)


def infer_dims(ordered_tups):

    #assuming the grid is full and complete, then
    # each dim's first index is repeated a number of times
    # equal to the product of the other dimension lengths.
    # => we can find the length in that dimension by dividing
    # the total # elems by this product

    num_tups = len(ordered_tups)
    first_x, first_y, first_z = ordered_tups[0]

    y_times_z = len(list(filter(lambda v: v[0] == first_x, ordered_tups)))
    x_times_z = len(list(filter(lambda v: v[1] == first_y, ordered_tups)))
    x_times_y = len(list(filter(lambda v: v[2] == first_z, ordered_tups)))

    assert num_tups % y_times_z == 0, "grid incomplete or redundant"
    assert num_tups % x_times_z == 0, "grid incomplete or redundant"
    assert num_tups % x_times_y == 0, "grid incomplete or redundant"

    x = num_tups  // y_times_z
    y = x_times_z // x
    z = x_times_y // x

    return (x,y,z)


def read_chunk_seg_info(fname):
    return io.read_dframe(fname)


def write_chunk_seg_info(centers, sizes, bboxes, chunk_bounds, proc_dir_path):

    sizes_df = pd.Series(sizes, columns=["sizes"])
    centers_df = dframe_from_tuple_dict(centers, COM_SCHEMA)

    bbox_tuples = { k : bbox.astuple() for (k,bbox) in bboxes.items() }
    bbox_df = dframe_from_tuple_dict(bbox_tuples, BBOX_SCHEMA)

    full_dframe = pd.concat((sizes_df, centers_df, bbox_df), axis=1)

    chunk_tag = io.chunk_tag(chunk_bounds)
    seg_info_fname = os.path.join(proc_dir_path,
                                  "seg_infos/seg_info_{tag}".format(tag=chunk_tag))

    io.save_dframe(full_dframe, seg_info_fname)


def dframe_from_tuple_dict(tuple_dict, colnames):

    df = pd.DataFrame.from_dict(tuple_dict, orient="index")
    df.columns = colnames

    return df


def write_chunk_continuations(conts, chunk_bounds, proc_dir_path):

    chunk_tag = io.chunk_tag(chunk_bounds)
    fname = os.path.join(proc_dir_path,
                         "continuations/conts_{tag}".format(tag=chunk_tag))

    fobj = io.make_local_h5(fname)
    for c in conts:
        c.write_to_fobj(fobj)
    fobj.close()

    if io.is_remote_pathname(fname):
        io.send_local_file(fobj.name, fname)
