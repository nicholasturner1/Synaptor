#!/usr/bin/env python3


import os
import pandas as pd
import numpy as np


from . import continuations
from .. import io


COM_SCHEMA  = ["COM_x","COM_y","COM_z"]
BBOX_SCHEMA = ["BBOX_bx","BBOX_by","BBOX_bz",
               "BBOX_ex","BBOX_ey","BBOX_ez"]

SEG_INFO_DIRNAME     = "seg_infos"
CONTINUATION_DIRNAME = "continuations"
ID_MAP_DIRNAME       = "id_maps"


def read_seg_infos(proc_dir_path):

    seg_info_dir = os.path.join(proc_dir_path, SEG_INFO_DIRNAME)
    fnames = io.pull_all_files(seg_info_dir)

    starts  = [ io.bbox_from_fname(f).min() for f in fnames ]
    dframes = [ read_chunk_seg_info(f) for f in fnames ]

    info_arr = make_info_arr({s : df for (s,df) in zip(starts, dframes)})
    return info_arr, os.path.dirname(fnames[0])


def read_all_continuations(proc_dir_path):

    continuation_dir = os.path.join(proc_dir_path, CONTINUATION_DIRNAME)
    fnames = io.pull_all_files(continuation_dir)

    starts = [io.bbox_from_fname(f).min() for f in fnames ]
    cont_dicts = [ read_chunk_continuations(f) for f in fnames ]

    info_arr = make_info_arr({s : cd for (s,cd) in zip(starts, cont_dicts)})
    return info_arr, os.path.dirname(fnames[0])


def make_info_arr(start_lookup):

    ordering = sorted(start_lookup.keys())
    dims     = infer_dims(ordering)

    ordered = [start_lookup[k] for k in ordering]

    arr = np.array([None for _ in range(len(ordered))]) #object arr
    for i in range(len(ordered)):
        arr[i] = ordered[i]

    return arr.reshape(dims)


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
    y = x_times_y // x
    z = x_times_z // x

    return (x,y,z)


def read_chunk_seg_info(fname):
    return io.read_dframe(fname)


def write_chunk_seg_info(centers, sizes, bboxes, chunk_bounds, proc_dir_path):

    sizes_df = pd.Series(sizes, name="sizes")
    centers_df = dframe_from_tuple_dict(centers, COM_SCHEMA)

    bbox_tuples = { k : bbox.astuple() for (k,bbox) in bboxes.items() }
    bbox_df = dframe_from_tuple_dict(bbox_tuples, BBOX_SCHEMA)

    full_dframe = pd.concat((sizes_df, centers_df, bbox_df), axis=1)

    chunk_tag = io.chunk_tag(chunk_bounds)
    seg_info_fname = os.path.join(proc_dir_path, SEG_INFO_DIRNAME,
                                  "seg_info_{tag}.df".format(tag=chunk_tag))

    io.write_dframe(full_dframe, seg_info_fname)


def write_full_seg_info(full_seg_info, proc_dir_path):

    seg_info_fname = os.path.join(proc_dir_path, "full_seg_info.df")
    io.write_dframe(full_seg_info, seg_info_fname)


def dframe_from_tuple_dict(tuple_dict, colnames):

    df = pd.DataFrame.from_dict(tuple_dict, orient="index")
    df.columns = colnames

    return df


def write_chunk_continuations(conts, chunk_bounds, proc_dir_path):

    chunk_tag = io.chunk_tag(chunk_bounds)
    fname = os.path.join(proc_dir_path, CONTINUATION_DIRNAME,
                         "conts_{tag}".format(tag=chunk_tag))

    fobj = io.make_local_h5(fname)
    for c in conts:
        c.write_to_fobj(fobj)
    fobj.close()

    if io.is_remote_path(fname):
        io.send_local_file(fobj.name, fname)


def read_chunk_continuations(fname):
    return continuations.Continuation.read_all_from_fname(fname)


def write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_dir_path):

    for (id_map, bounds) in zip(chunk_id_maps.flat, chunk_bounds):

        chunk_tag = io.chunk_tag(bounds)
        fname = os.path.join(ID_MAP_DIRNAME,
                             "id_map_{tag}.df".format(tag=chunk_tag))
        write_id_map(id_map, fname)

    if io.is_remote_path(proc_dir_path):
        io.send_directory(proc_dir_path, "id_maps")


def read_chunk_id_map(proc_dir_path, chunk_bounds):

    chunk_tag = io.chunk_tag(chunk_bounds)
    basename = "id_map_{tag}.df".format(tag=chunk_tag)
    fname = io.pull_file(os.path.join(proc_dir_path, ID_MAP_DIRNAME, basename))

    df = io.read_dframe(fname)

    return dict(zip(df.index, df.new_id))


def write_id_map(id_map, fname):

    df = pd.DataFrame(pd.Series(id_map), columns=["new_id"])
    io.write_dframe(df, fname)
