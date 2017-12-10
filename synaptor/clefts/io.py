#!/usr/bin/env python3


import os, itertools
import pandas as pd
import numpy as np


from ..merge import continuations
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
    assert len(fnames) > 0, "No filenames returned"

    starts  = [ io.bbox_from_fname(f).min() for f in fnames ]
    dframes = [ read_chunk_seg_info(f) for f in fnames ]

    info_arr = io.utils.make_info_arr({s : df
                                       for (s,df) in zip(starts, dframes)})
    return info_arr, os.path.dirname(fnames[0])


def read_all_continuations(proc_dir_path):

    continuation_dir = os.path.join(proc_dir_path, CONTINUATION_DIRNAME)
    fnames = io.pull_all_files(continuation_dir)

    starts = [io.bbox_from_fname(f).min() for f in fnames ]
    cont_dicts = [ read_chunk_continuations(f) for f in fnames ]

    info_arr = io.utils.make_info_arr({s : cd
                                       for (s,cd) in zip(starts, cont_dicts)})
    return info_arr, os.path.dirname(fnames[0])


def read_chunk_seg_info(fname):
    return io.read_dframe(fname)


def write_chunk_seg_info(centers, sizes, bboxes, chunk_bounds, proc_dir_path):

    assert len(centers) == len(sizes) == len(bboxes)

    chunk_tag = io.chunk_tag(chunk_bounds)
    seg_info_fname = os.path.join(proc_dir_path, SEG_INFO_DIRNAME,
                                  "seg_info_{tag}.df".format(tag=chunk_tag))

    if len(centers) == 0:
        df = empty_seg_df()
        return io.write_dframe(df, seg_info_fname)

    sizes_df = pd.Series(sizes, name="size")
    centers_df = dframe_from_tuple_dict(centers, COM_SCHEMA)

    bbox_tuples = { k : bbox.astuple() for (k,bbox) in bboxes.items() }
    bbox_df = dframe_from_tuple_dict(bbox_tuples, BBOX_SCHEMA)

    full_dframe = pd.concat((sizes_df, centers_df, bbox_df), axis=1)

    io.write_dframe(full_dframe, seg_info_fname)


def empty_seg_df():
    return pd.DataFrame({k : [] for k in itertools.chain(("size",),
                                                         COM_SCHEMA,
                                                         BBOX_SCHEMA) })


def read_cons_cleft_info(proc_dir_path):

    full_fname = os.path.join(proc_dir_path, "cons_cleft_info.df")
    fname = io.pull_file(full_fname)

    return io.read_dframe(fname)


def write_cons_cleft_info(cons_cleft_info, proc_dir_path):

    fname = os.path.join(proc_dir_path, "cons_cleft_info.df")
    io.write_dframe(cons_cleft_info, fname)


def dframe_from_tuple_dict(tuple_dict, colnames):

    df = pd.DataFrame.from_dict(tuple_dict, orient="index")
    df.columns = colnames

    return df


def write_chunk_continuations(conts, chunk_bounds, proc_dir_path):

    chunk_tag = io.chunk_tag(chunk_bounds)
    fname = os.path.join(proc_dir_path, CONTINUATION_DIRNAME,
                         "conts_{tag}.h5".format(tag=chunk_tag))

    fobj = io.make_local_h5(fname)
    local_fname = fobj.filename
    for c in conts:
        c.write_to_fobj(fobj)
    fobj.close()

    if io.is_remote_path(fname):
        io.send_local_file(local_fname, fname)


def read_chunk_continuations(fname):
    return continuations.Continuation.read_all_from_fname(fname)


def write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_dir_path):

    if not os.path.exists(ID_MAP_DIRNAME):
        os.makedirs(ID_MAP_DIRNAME)

    for (id_map, bounds) in zip(chunk_id_maps.flat, chunk_bounds):

        chunk_tag = io.chunk_tag(bounds)
        fname = os.path.join(ID_MAP_DIRNAME,
                             "id_map_{tag}.df".format(tag=chunk_tag))
        write_id_map(id_map, fname)

    io.send_directory(ID_MAP_DIRNAME, proc_dir_path)


def read_chunk_id_map(proc_dir_path, chunk_bounds):

    chunk_tag = io.chunk_tag(chunk_bounds)
    basename = "id_map_{tag}.df".format(tag=chunk_tag)
    fname = io.pull_file(os.path.join(proc_dir_path, ID_MAP_DIRNAME, basename))

    df = io.read_dframe(fname)

    return dict(zip(df.index, df.new_id))


def write_id_map(id_map, fname):

    df = pd.DataFrame(pd.Series(id_map), columns=["new_id"])
    io.write_dframe(df, fname)
