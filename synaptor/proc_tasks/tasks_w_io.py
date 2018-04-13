#!/usr/bin/env python3
__doc__ = """
Synaptor Processing Tasks w/ Standardized IO
"""

from .. import io
from .. import types

from . import io as taskio
from . import tasks
from .tasks import timed


def chunk_ccs_task(output_cvname, cleft_cvname, proc_dir_path,
                   chunk_begin, chunk_end,
                   cc_thresh, sz_thresh, mip=0):

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)


    net_output = timed("Reading network output chunk: {}".format(chunk_bounds),
                       io.read_cloud_volume_chunk,
                       output_cvname, chunk_bounds, mip=mip)

    (ccs, continuations,
     cleft_info) = tasks.chunk_ccs_task(net_output,
                                        chunk_begin, chunk_end,
                                        cc_thresh, sz_thresh)

    timed("Writing cleft chunk: {}".format(chunk_bounds),
          io.write_cloud_volume_chunk,
          ccs, cleft_cvname, chunk_bounds, mip=mip)

    timed("Writing chunk_continuations",
          taskio.write_chunk_continuations,
          continuations, chunk_bounds, proc_dir_path)

    timed("Writing cleft info",
          taskio.write_chunk_cleft_info,
          cleft_info, chunk_bounds, proc_dir_path)


def merge_ccs_task(proc_dir_path, size_thr):


    cont_info_arr, _ = timed("Reading continuations",
                             taskio.read_all_continuations,
                             proc_dir_path)

    cleft_info_arr, local_dir = timed("Reading cleft infos",
                                      taskio.read_all_cleft_infos,
                                      proc_dir_path)

    chunk_bounds = io.extract_sorted_bboxes(local_dir)

    #Processing
    cons_cleft_info, chunk_id_maps = tasks.merge_ccs_task(cont_info_arr,
                                                          cleft_info_arr,
                                                          chunk_bounds,
                                                          size_thr)


    timed("Writing merged cleft info",
          taskio.write_merged_cleft_info,
          cons_cleft_info, proc_dir_path)

    timed("Writing chunk id maps",
          taskio.write_chunk_id_maps,
          chunk_id_maps, chunk_bounds, proc_dir_path)


def chunk_edges_task(img_cvname, cleft_cvname, seg_cvname,
                     chunk_begin, chunk_end, patchsz,
                     num_samples_per_cleft, dil_param,
                     proc_dir_path, wshed_cvname=None):

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    img = timed("Reading img chunk",
                io.read_cloud_volume_chunk,
                img_cvname, chunk_bounds)
    clefts = timed("Reading cleft chunk",
                   io.read_cloud_volume_chunk,
                   cleft_cvname, chunk_bounds)
    seg = timed("Reading segmentation chunk",
                io.read_cloud_volume_chunk,
                seg_cvname, chunk_bounds)
    if wshed_cvname is not None:
        wshed = timed("Reading watershed chunk",
                      io.read_cloud_volume_chunk,
                      wshed_cvname, chunk_bounds)
    else:
        wshed = None

    asynet = timed("Reading asynet",
                   taskio.read_network_from_proc,
                   proc_dir_path)

    chunk_id_map = timed("Reading chunk id map",
                         taskio.read_chunk_id_map,
                         proc_dir_path, chunk_bounds)

    edges = tasks.chunk_edges_task(img, clefts, seg, asynet,
                                   chunk_begin, chunk_end, patchsz,
                                   id_map=chunk_id_map, wshed=wshed,
                                   num_samples_per_cleft=num_samples_per_cleft,
                                   dil_param=dil_param)

    timed("Writing chunk edges",
          taskio.write_chunk_edge_info,
          edges, chunk_bounds, proc_dir_path)


def merge_edges_task(voxel_res, dist_thr, size_thr, proc_dir_path):

    edges_arr, _ = timed("Reading all edges",
                         taskio.read_all_edge_infos,
                         proc_dir_path)
    merged_cleft_info = timed("Reading merged cleft info",
                              taskio.read_merged_cleft_info,
                              proc_dir_path)

    (full_df,
     dup_id_map,
     merged_edge_df) = tasks.merge_edges_task(edges_arr, merged_cleft_info,
                                              voxel_res, dist_thr, size_thr)

    timed("Writing duplicate id mapping",
          taskio.write_dup_id_map,
          dup_id_map, proc_dir_path)
    timed("Writing merged edge list",
          taskio.write_final_edge_info,
          merged_edge_df, proc_dir_path)
    timed("Writing final & complete DataFrame",
          taskio.write_full_info,
          full_df, proc_dir_path)


def remap_ids_task(cleft_in_cvname, cleft_out_cvname,
                   chunk_begin, chunk_end, proc_dir_path, mip=0):

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    chunk_id_map = timed("Reading chunk id map",
                         taskio.read_chunk_id_map,
                         proc_dir_path, chunk_bounds)

    dup_id_map = timed("Reading duplicate id map",
                       taskio.read_dup_id_map,
                       proc_dir_path)

    cleft_chunk = timed("Reading cleft chunk",
                        io.read_cloud_volume_chunk,
                        cleft_in_cvname, chunk_bounds, mip=mip)

    cleft_chunk = tasks.remap_ids_task(cleft_chunk, chunk_id_map,
                                       dup_id_map, copy=False)

    timed("Writing results",
          io.write_cloud_volume_chunk,
          cleft_chunk, cleft_out_cvname, chunk_bounds, mip=mip)
