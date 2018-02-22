#!/usr/bin/env python3

import time

from .. import io
from . import chunk_ccs
from . import merge_ccs


def timed(fn_desc, fn, *args, **kwargs):
    """ Measures the execution time of the passed fn """
    print("{fn_desc}".format(fn_desc=fn_desc))
    start = time.time()
    result = fn(*args, **kwargs)
    print("{fn_desc} complete in {t:.3f}s".format(fn_desc=fn_desc,
                                                  t=time.time()-start))
    return result


def merge_ccs_task(proc_dir_path, size_thr):

    cont_info_arr, _ = timed("Reading continuations",
                             merge_ccs.io.read_all_continuations, 
                             proc_dir_path)

    cleft_info_arr, local_dir = timed("Reading seg infos",
                                      merge_ccs.io.read_seg_infos, 
                                      proc_dir_path)

    chunk_bounds = io.extract_sorted_bboxes(local_dir)

    cons_cleft_info, chunk_id_maps = timed("Consolidating cleft dataframes",
                                           merge_ccs.consolidate_cleft_info_arr,
                                           cleft_info_arr)

    cont_info_arr = timed("Applying chunk_id_maps to continuations",
                          merge_ccs.apply_chunk_id_maps,
                          cont_info_arr, chunk_id_maps)

    cont_id_map = timed("Merging connected continuations",
                        merge_ccs.merge_connected_continuations,
                        cont_info_arr)

    chunk_id_maps = timed("Updating chunk id maps",
                          merge_ccs.update_chunk_id_maps,
                          chunk_id_maps, cont_id_map)

    cons_cleft_info = timed("Merging cleft dataframes",
                            merge_ccs.merge_cleft_df,
                            cons_cleft_info, cont_id_map)

    size_thr_map = timed("Enforcing size threshold over merged ccs",
                         merge_ccs.enforce_size_threshold,
                         cons_cleft_info, size_thr)

    chunk_id_maps = timed("Updating chunk id maps (for size thresholding)",
                          merge_ccs.update_chunk_id_maps,
                          chunk_id_maps, size_thr_map)

    timed("Writing consolidated cleft info",
          merge_ccs.io.write_cons_cleft_info, 
          cons_cleft_info, proc_dir_path)

    timed("Writing chunk id maps",
          merge_ccs.io.write_chunk_id_maps,
          chunk_id_maps, chunk_bounds, proc_dir_path)

    print("Tada!")

#def merge_edges_task(voxel_res, dist_thr, proc_dir_path):

    #edges_arr, _ = timed(merge_edges.
