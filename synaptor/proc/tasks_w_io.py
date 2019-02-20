"""
Processing tasks with standardized IO - using seung-lab/CloudVolume, and
either (1) a file-based cloud-storage platform (AWS S3 or Google Cloud
Storage) or (2) a SQLAlchemy-supported database.
"""


from .. import io
from .. import types
from .. import seg_utils

from . import io as taskio
from . import tasks
from .tasks import timed
from . import edge


def cc_task(desc_cvname, seg_cvname, proc_url,
            cc_thresh, sz_thresh, chunk_begin, chunk_end,
            mip=0, parallel=1):

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    desc_vol = timed(f"Reading network output chunk: {chunk_bounds}",
                     io.read_cloud_volume_chunk,
                     desc_cvname, chunk_bounds,
                     mip=mip, parallel=parallel)

    ccs, continuations, seg_info = tasks.cc_task(desc_vol,
                                                 cc_thresh, sz_thresh,
                                                 offset=chunk_begin)

    timed(f"Writing seg chunk: {chunk_bounds}",
          io.write_cloud_volume_chunk,
          ccs, seg_cvname, chunk_bounds,
          mip=mip, parallel=parallel)

    timed("Writing chunk_continuations",
          taskio.write_chunk_continuations,
          continuations, chunk_bounds, proc_url)

    timed("Writing cleft info",
          taskio.write_chunk_cleft_info,
          seg_info, chunk_bounds, proc_url)


def merge_ccs_task(proc_url, size_thr, max_face_shape):

    cont_info_arr, _ = timed("Reading continuations",
                             taskio.read_all_continuations,
                             proc_url)

    cleft_info_arr, local_dir = timed("Reading cleft infos",
                                      taskio.read_all_cleft_infos,
                                      proc_url)

    chunk_bounds = io.extract_sorted_bboxes(local_dir)

    # Processing
    cons_cleft_info, chunk_id_maps = tasks.merge_ccs_task(cont_info_arr,
                                                          cleft_info_arr,
                                                          chunk_bounds,
                                                          size_thr,
                                                          max_face_shape)

    timed("Writing merged cleft info",
          taskio.write_merged_cleft_info,
          cons_cleft_info, proc_url)

    timed("Writing chunk id maps",
          taskio.write_chunk_id_maps,
          chunk_id_maps, chunk_bounds, proc_url)


def edge_task(img_cvname, cleft_cvname, seg_cvname,
              chunk_begin, chunk_end, patchsz, proc_url,
              samples_per_cleft=2, dil_param=5,
              root_seg_cvname=None,
              resolution=(4, 4, 40), num_downsamples=0,
              base_res_begin=None, base_res_end=None,
              parallel=1, hashmax=None):
    """
    Runs tasks.chunk_edges_task after reading the relevant
    cloud volume chunks and downsampling the cleft volume
    to match the others.

    Writes the results as edge information dataframes within
    {proc_url}/chunk_edges

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

    img = timed(f"Reading img chunk at {resolution}",
                io.read_cloud_volume_chunk,
                img_cvname, chunk_bounds,
                MIP=resolution, parallel=parallel)

    # clefts won't be downsampled - will do that myself below
    clefts = timed(f"Reading cleft chunk at MIP 0",
                   io.read_cloud_volume_chunk,
                   cleft_cvname, base_bounds,
                   MIP=0, parallel=parallel)
    seg = timed(f"Reading segmentation chunk at {resolution}",
                io.read_cloud_volume_chunk,
                seg_cvname, chunk_bounds, MIP=resolution,
                parallel=parallel)

    assoc_net = timed("Reading association network",
                      taskio.read_network_from_proc,
                      proc_url).cuda()

    chunk_id_map = timed("Reading chunk id map",
                         taskio.read_chunk_id_map,
                         proc_url, base_bounds)

    # Downsampling clefts to match other volumes
    if num_downsamples > 0:
        clefts = timed(f"Downsampling clefts to MIP {num_downsamples}",
                       seg_utils.downsample_seg_to_MIP,
                       clefts, 0, num_downsamples)

    assert img.shape == clefts.shape == seg.shape, "mismatched volumes"

    edge_info = tasks.edge_task(img, clefts, seg, assoc_net,
                                patchsz, offset=chunk_begin,
                                id_map=chunk_id_map, root_seg=None,
                                samples_per_cleft=samples_per_cleft,
                                dil_param=dil_param, hashmax=hashmax)

    if num_downsamples > 0:
        edge_info = timed("Up-sampling edge information",
                          edge.upsample_edge_info,
                          edge_info, num_downsamples, chunk_begin)

    timed("Writing chunk edges",
          taskio.write_chunk_edge_info,
          edge_info, proc_url, base_bounds)


def merge_edges_task(voxel_res, dist_thr, size_thr, proc_url):

    edges_arr = timed("Reading all edges",
                      taskio.read_all_chunk_edge_infos,
                      proc_url)
    merged_cleft_info = timed("Reading merged cleft info",
                              taskio.read_merged_cleft_info,
                              proc_url)

    full_df, dup_id_map, merged_edge_df = tasks.merge_edges_task(
                                              edges_arr, merged_cleft_info,
                                              voxel_res, dist_thr, size_thr)

    timed("Writing duplicate id mapping",
          taskio.write_dup_id_map,
          dup_id_map, proc_url)
    timed("Writing merged edge list",
          taskio.write_merged_edge_info,
          merged_edge_df, proc_url)
    timed("Writing final & complete DataFrame",
          taskio.write_full_info,
          full_df, proc_url)


def pick_largest_edges_task(proc_url, clefthash=None):

    if clefthash is None:
        edges = timed("Reading all chunkwise edge info",
                      taskio.read_all_chunk_edge_infos,
                      proc_url)
    else:
        edges = timed(f"Reading edge info for cleft id hash {clefthash}",
                      taskio.read_hashed_edge_info,
                      proc_url,
                      clefthash=clefthash, merged=False)

    largest_info = tasks.pick_largest_edges_task(edges, clefthash is not None)

    timed("Writing merged edge list",
          taskio.write_merged_edge_info,
          largest_info, proc_url)


def merge_duplicates_task(voxel_res, dist_thr, size_thr, proc_url, hash_index):

    edge_df = timed(f"Reading edges for hash index {hash_index}",
                    taskio.read_hashed_edge_info,
                    proc_url, hash_index)

    merged_cleft_info = timed("Reading merged cleft info for ind {hash_index}",
                              taskio.read_merged_cleft_info,
                              proc_url, hash_index)

    full_df, dup_id_map = tasks.merge_duplicates_task(merged_cleft_info,
                                                      edge_df, dist_thr,
                                                      voxel_res, size_thr)

    timed("Writing duplicate id mapping for hash index",
          taskio.write_dup_id_map,
          dup_id_map, proc_url)
    timed("Writing final DataFrame for hash index",
          taskio.write_full_info,
          full_df, proc_url)


def chunk_overlaps_task(seg_cvname, base_seg_cvname,
                        chunk_begin, chunk_end,
                        proc_url, mip=0, seg_mip=None,
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
          overlap_matrix, chunk_bounds, proc_url)


def merge_overlaps_task(proc_url):

    overlap_arr = timed("Reading overlap matrices",
                        taskio.read_all_overlap_mats,
                        proc_url)

    max_overlaps = tasks.merge_overlaps_task(overlap_arr)

    timed("Writing max overlaps",
          taskio.write_max_overlaps,
          max_overlaps, proc_url)


def remap_ids_task(seg_in_cvname, seg_out_cvname,
                   chunk_begin, chunk_end, proc_url,
                   mip=0, parallel=1):

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    chunk_id_map = timed("Reading chunk id map",
                         taskio.read_chunk_id_map,
                         proc_url, chunk_bounds)

    dup_id_map = timed("Reading duplicate id map",
                       taskio.read_dup_id_map,
                       proc_url)

    seg = timed("Reading cleft chunk",
                io.read_cloud_volume_chunk,
                seg_in_cvname, chunk_bounds,
                mip=mip, parallel=parallel)

    seg = tasks.remap_ids_task(seg, chunk_id_map, dup_id_map, copy=False)

    timed("Writing results",
          io.write_cloud_volume_chunk,
          seg, seg_out_cvname, chunk_bounds,
          mip=mip, parallel=parallel)


def anchor_task(cleft_cvname, seg_cvname, proc_url,
                chunk_begin, chunk_end, root_seg_cvname=None,
                voxel_res=[4, 4, 40], min_box_width=[100, 100, 5],
                mip=0, seg_mip=None, parallel=1):

    seg_mip = mip if seg_mip is None else seg_mip

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    seg = timed("Reading seg chunk",
                io.read_cloud_volume_chunk,
                seg_cvname, chunk_bounds,
                mip=seg_mip, parallel=parallel)

    clefts = timed("Reading cleft chunk",
                   io.read_cloud_volume_chunk,
                   cleft_cvname, chunk_bounds,
                   mip=mip, parallel=parallel)

    if root_seg_cvname is not None:
        roots = timed(f"Reading root segmentation chunk at mip {seg_mip}",
                      io.read_cloud_volume_chunk,
                      root_seg_cvname, chunk_bounds,
                      mip=seg_mip, parallel=parallel)
        assert roots.shape == seg.shape, "mismatched root segmentation"
    else:
        roots = None

    edge_df = timed("Reading full edge info",
                    taskio.read_full_info,
                    proc_url)

    anchor_df = tasks.anchor_task(edge_df, seg, clefts, chunk_begin,
                                  voxel_res=voxel_res, root_seg=roots,
                                  min_box_width=min_box_width)

    timed("Writing chunk anchor info",
          taskio.write_chunk_anchor,
          anchor_df, chunk_bounds, proc_url)
