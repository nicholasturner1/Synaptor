#!/usr/bin/env python3
__doc__ = """
Synaptor Processing Tasks w/ Standardized IO
"""

from .. import io
from .. import types
from .. import seg_utils

from . import io as taskio
from . import tasks
from . import chunk_edges
from .tasks import timed


def chunk_ccs_task(output_cvname, cleft_cvname, proc_dir_path,
                   chunk_begin, chunk_end,
                   cc_thresh, sz_thresh,
                   mip=0, parallel=1):

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)


    net_output = timed("Reading network output chunk: {}".format(chunk_bounds),
                       io.read_cloud_volume_chunk,
                       output_cvname, chunk_bounds,
                       mip=mip, parallel=parallel)

    (ccs, continuations,
     cleft_info) = tasks.chunk_ccs_task(net_output,
                                        chunk_begin, chunk_end,
                                        cc_thresh, sz_thresh)

    timed("Writing cleft chunk: {}".format(chunk_bounds),
          io.write_cloud_volume_chunk,
          ccs, cleft_cvname, chunk_bounds,
          mip=mip, parallel=parallel)

    timed("Writing chunk_continuations",
          taskio.write_chunk_continuations,
          continuations, chunk_bounds, proc_dir_path)

    timed("Writing cleft info",
          taskio.write_chunk_cleft_info,
          cleft_info, chunk_bounds, proc_dir_path)


def merge_ccs_task(proc_dir_path, size_thr, max_face_shape):


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
                                                          size_thr,
                                                          max_face_shape)


    timed("Writing merged cleft info",
          taskio.write_merged_cleft_info,
          cons_cleft_info, proc_dir_path)

    timed("Writing chunk id maps",
          taskio.write_chunk_id_maps,
          chunk_id_maps, chunk_bounds, proc_dir_path)


def chunk_edges_task(img_cvname, cleft_cvname, seg_cvname,
                     chunk_begin, chunk_end, patchsz,
                     num_samples_per_cleft, dil_param,
                     proc_dir_path, wshed_cvname=None,
                     resolution=(4, 4, 40), num_downsamples=0,
                     base_res_begin=None, base_res_end=None,
                     parallel=1):
    """
    Runs tasks.chunk_edges_task after reading the relevant
    cloud volume chunks and downsampling the cleft volume
    to match the others.

    Writes the results as edge information dataframes within
    {proc_dir_path}/chunk_edges

    img_mip refers to the mip level which corresponds to the mip arg
    seg_mip refers to the mip level which corresponds to the mip arg
    these can both be left as None, in which case they'll assume the
    mip arg value

    base_res_{begin,end} specify a base level bbox in case upsampling the
    other chunk bounds doesn't translate to the same box (e.g. 3//2*2)
    """

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    if base_res_begin is None:
        print("Upsampling chunk bounds naively")
        base_bounds = chunk_bounds.scale2d(2 ** num_downsamples)
    else:
        base_bounds = types.BBox3d(base_res_begin, base_res_end)

    img = timed("Reading img chunk at {}".format(resolution),
                io.read_cloud_volume_chunk,
                img_cvname, chunk_bounds,
                mip=resolution, parallel=parallel)
    # clefts won't be downsampled - will do that myself later
    clefts = timed("Reading cleft chunk at mip 0",
                   io.read_cloud_volume_chunk,
                   cleft_cvname, base_bounds,
                   mip=0, parallel=parallel)
    seg = timed("Reading segmentation chunk at {}".format(resolution),
                io.read_cloud_volume_chunk,
                seg_cvname, chunk_bounds, mip=resolution,
                parallel=parallel)

    asynet = timed("Reading asynet",
                   taskio.read_network_from_proc,
                   proc_dir_path).cuda()

    chunk_id_map = timed("Reading chunk id map",
                         taskio.read_chunk_id_map,
                         proc_dir_path, base_bounds)

    #Downsampling clefts to match other volumes
    if num_downsamples > 0:
        clefts = timed("Downsampling clefts to mip {}".format(num_downsamples),
                       seg_utils.downsample_seg_to_mip,
                       clefts, 0, num_downsamples)

    assert img.shape == clefts.shape == seg.shape, "mismatched volumes"

    edges = tasks.chunk_edges_task(img, clefts, seg, asynet,
                                   chunk_begin, chunk_end, patchsz,
                                   id_map=chunk_id_map, wshed=None,
                                   num_samples_per_cleft=num_samples_per_cleft,
                                   dil_param=dil_param)

    if num_downsamples > 0:
        edges = timed("Up-sampling edge information",
                      chunk_edges.upsample_edge_info,
                      edges, num_downsamples, chunk_begin)

    timed("Writing chunk edges",
          taskio.write_chunk_edge_info,
          edges, base_bounds, proc_dir_path)


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


def chunk_overlaps_task(seg_cvname, base_seg_cvname,
                        chunk_begin, chunk_end,
                        proc_dir_path, mip=0, seg_mip=None,
                        parallel=1):

    seg_mip = mip if seg_mip is None else seg_mip

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    seg_chunk = timed("Reading seg chunk",
                      io.read_cloud_volume_chunk,
                      seg_cvname, chunk_bounds,
                      mip=mip, parallel=parallel)

    base_seg_chunk = timed("Reading base seg chunk",
                           io.read_cloud_volume_chunk,
                           base_seg_cvname, chunk_bounds,
                           mip=seg_mip, parallel=parallel)

    overlap_matrix = tasks.chunk_overlaps_task(seg_chunk, base_seg_chunk)

    timed("Writing overlap matrix",
          taskio.write_chunk_overlap_mat,
          overlap_matrix, chunk_bounds, proc_dir_path)


def merge_overlaps_task(proc_dir_path):

    overlap_arr, _ = timed("Reading overlap matrices",
                        taskio.read_all_overlap_mats,
                        proc_dir_path)

    max_overlaps = tasks.merge_overlaps_task(overlap_arr)


    timed("Writing max overlaps",
          taskio.write_max_overlaps,
          max_overlaps, proc_dir_path)


def remap_ids_task(cleft_in_cvname, cleft_out_cvname,
                   chunk_begin, chunk_end, proc_dir_path,
                   mip=0, parallel=1):

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    chunk_id_map = timed("Reading chunk id map",
                         taskio.read_chunk_id_map,
                         proc_dir_path, chunk_bounds)

    dup_id_map = timed("Reading duplicate id map",
                       taskio.read_dup_id_map,
                       proc_dir_path)

    cleft_chunk = timed("Reading cleft chunk",
                        io.read_cloud_volume_chunk,
                        cleft_in_cvname, chunk_bounds,
                        mip=mip, parallel=parallel)

    cleft_chunk = tasks.remap_ids_task(cleft_chunk, chunk_id_map,
                                       dup_id_map, copy=False)

    timed("Writing results",
          io.write_cloud_volume_chunk,
          cleft_chunk, cleft_out_cvname, chunk_bounds,
          mip=mip, parallel=parallel)


def anchor_task(cleft_cvname, seg_cvname, proc_dir_path,
                chunk_begin, chunk_end, wshed_cvname=None,
                voxel_res=[4, 4, 40], min_box_width=[100, 100, 5],
                mip=0, seg_mip=None, parallel=1):

    seg_mip = mip if seg_mip is None else seg_mip

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    seg_chunk = timed("Reading seg chunk",
                      io.read_cloud_volume_chunk,
                      seg_cvname, chunk_bounds,
                      mip=seg_mip, parallel=parallel)

    clf_chunk = timed("Reading cleft chunk",
                      io.read_cloud_volume_chunk,
                      cleft_cvname, chunk_bounds,
                      mip=mip, parallel=parallel)

    if wshed_cvname is not None:
        wshed = timed("Reading watershed chunk at mip {}".format(seg_mip),
                      io.read_cloud_volume_chunk,
                      wshed_cvname, chunk_bounds,
                      mip=seg_mip, parallel=parallel)
        assert wshed.shape == seg_chunk.shape, "mismatched wshed basins"
    else:
        wshed = None

    edge_df = timed("Reading full edge info",
                    taskio.read_full_info,
                    proc_dir_path)

    anchor_df = tasks.anchor_task(edge_df, seg_chunk, clf_chunk, chunk_begin,
                                  voxel_res=voxel_res, wshed=wshed,
                                  min_box_width=min_box_width)

    timed("Writing chunk anchor info",
          taskio.write_chunk_anchor,
          anchor_df, chunk_bounds, proc_dir_path)
