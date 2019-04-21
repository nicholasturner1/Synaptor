"""
Processing tasks with standardized IO - using seung-lab/CloudVolume, and
either (1) a file-based cloud-storage platform (AWS S3 or Google Cloud
Storage) or (2) a SQLAlchemy-supported database.
"""


import time

from .. import io
from .. import types
from .. import seg_utils
from . import io as taskio
from . import tasks
from .tasks import timed
from . import seg
from . import edge
from . import colnames as cn


def cc_task(desc_cvname, seg_cvname, proc_url,
            cc_thresh, sz_thresh, chunk_begin, chunk_end,
            mip=0, parallel=1, proc_dir=None, hashmax=100,
            timing_tag=None):

    start_time = time.time()

    proc_dir = proc_url if proc_dir is None else proc_dir
    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    desc_vol = timed(f"Reading network output chunk: {chunk_bounds}",
                     io.read_cloud_volume_chunk,
                     desc_cvname, chunk_bounds,
                     mip=mip, parallel=parallel)

    ccs, continuations, seg_info = tasks.cc_task(desc_vol,
                                                 cc_thresh, sz_thresh,
                                                 offset=chunk_begin)

    face_hashes = seg.hash_chunk_faces(chunk_begin, chunk_end,
                                       maxval=hashmax)

    timed(f"Writing seg chunk: {chunk_bounds}",
          io.write_cloud_volume_chunk,
          ccs, seg_cvname, chunk_bounds,
          mip=mip, parallel=parallel)

    timed("Writing chunk_continuations",
          taskio.write_chunk_continuations,
          continuations, proc_dir, chunk_bounds)

    fhash_df, fhash_tablename = timed("Formatting chunk face hashes",
                                      taskio.prep_face_hashes,
                                      face_hashes, chunk_bounds, proc_dir)

    seginfo_df, seginfo_tablename = timed("Formatting segment info",
                                          taskio.prep_chunk_seg_info,
                                          seg_info, chunk_bounds)

    timed("Writing results to database",
          io.write_db_dframes,
          [fhash_df, seginfo_df], proc_url,
          [fhash_tablename, seginfo_tablename])

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "ccs", timing_tag, proc_url)


def merge_ccs_task(proc_url, size_thr, max_face_shape, timing_tag=None):

    start_time = time.time()

    cont_info_arr, _ = timed("Reading continuations",
                             taskio.read_all_continuations,
                             proc_url)

    cleft_info_arr, local_dir = timed("Reading cleft infos",
                                      taskio.read_all_chunk_seg_infos,
                                      proc_url)

    chunk_bounds = io.extract_sorted_bboxes(local_dir)

    # Processing
    cons_cleft_info, chunk_id_maps = tasks.merge_ccs_task(cont_info_arr,
                                                          cleft_info_arr,
                                                          size_thr,
                                                          max_face_shape)

    timed("Writing merged cleft info",
          taskio.write_merged_seg_info,
          cons_cleft_info, proc_url)

    timed("Writing chunk id maps",
          taskio.write_chunk_id_maps,
          chunk_id_maps, chunk_bounds, proc_url)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "merge_ccs", timing_tag, proc_url)


def match_continuations_task(proc_url, facehash, max_face_shape=(1024, 1024),
                             timing_tag=None):

    start_time = time.time()

    contin_files = timed("Fetching continuation files by hash",
                         taskio.continuations_by_hash,
                         proc_url, facehash)

    paired_files = timed("Pairing continuation files",
                         seg.merge.pair_continuation_files,
                         contin_files)

    graph_edges = list()

    for pair in paired_files:
        # Skipping an unmatched face (e.g. at the edge of volume)
        # or some other poorly formed case
        if len(pair) != 2:
            print(f"Skipping set with {len(pair)} elements")
            continue

        pair_filenames = (pair[0].filename, pair[1].filename)
        pair_contins = timed("Reading pair continuations",
                             taskio.read_face_filenames,
                             pair_filenames)

        # Skipping empty face
        if len(pair_contins[0]) == 0 or len(pair_contins[1]) == 0:
            continue

        map1 = timed("Reading id map 1",
                     taskio.read_chunk_unique_ids,
                     proc_url, pair[0].bbox)
        map2 = timed("Reading id map 2",
                     taskio.read_chunk_unique_ids,
                     proc_url, pair[1].bbox)
        pair_maps = (map1, map2)

        new_graph_edges = tasks.match_continuations_task(
                          pair_contins[0], pair_contins[1],
                          max_face_shape=max_face_shape,
                          id_map1=pair_maps[0], id_map2=pair_maps[1])

        graph_edges.extend(new_graph_edges)

    timed("Writing graph edges",
          taskio.write_contin_graph_edges,
          graph_edges, proc_url)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "match_contins", timing_tag, proc_url)


def seg_graph_cc_task(proc_url, hashmax, timing_tag=None):

    start_time = time.time()

    graph_edges = timed("Reading seg graph edges",
                        taskio.read_continuation_graph,
                        proc_url)

    all_ids = timed("Reading all unique seg ids",
                    taskio.read_all_unique_seg_ids,
                    proc_url)

    seg_merge_df = tasks.seg_graph_cc_task(graph_edges, hashmax, all_ids)

    timed("Writing seg merge_map",
          taskio.write_seg_merge_map,
          seg_merge_df, proc_url)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "seg_graph_ccs", timing_tag, proc_url)


def chunk_seg_merge_map(proc_url, timing_tag=None):

    start_time = time.time()

    if io.is_db_url(proc_url):
        timed("Creating chunked seg merge map",
              taskio.write_chunked_seg_map,
              proc_url)

    else:
        raise(Exception("not implemented for file IO"))

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "chunked_seg_map",
              timing_tag, proc_url)


def merge_seginfo_task(proc_url, hashval, aux_proc_url=None, timing_tag=None):

    start_time = time.time()

    seginfo_w_new_id = timed(f"Reading seginfo for dst hash {hashval}",
                             taskio.read_mapped_seginfo_by_dst_hash,
                             proc_url, hashval)

    merged_seginfo = tasks.merge_seginfo_task(seginfo_w_new_id)

    if aux_proc_url is not None:
        timed(f"Writing merged seginfo for dst hash {hashval} to aux",
              taskio.write_merged_seg_info,
              merged_seginfo, aux_proc_url, hash_tag=hashval)

    timed(f"Writing merged seginfo for dst hash {hashval}",
          taskio.write_merged_seg_info,
          merged_seginfo, proc_url, hash_tag=hashval)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "merge_seginfo", timing_tag, proc_url)


def edge_task(img_cvname, cleft_cvname, seg_cvname,
              chunk_begin, chunk_end, patchsz, proc_url,
              samples_per_cleft=2, dil_param=5,
              root_seg_cvname=None,
              resolution=(4, 4, 40), num_downsamples=0,
              base_res_begin=None, base_res_end=None,
              parallel=1, hashmax=None, proc_dir=None,
              timing_tag=None):
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

    start_time = time.time()

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    if base_res_begin is None:
        print("Upsampling chunk bounds naively")
        base_bounds = chunk_bounds.scale2d(2 ** num_downsamples)
    else:
        base_bounds = types.BBox3d(base_res_begin, base_res_end)

    proc_dir = proc_url if proc_dir is None else proc_dir

    img = timed(f"Reading img chunk at {resolution}",
                io.read_cloud_volume_chunk,
                img_cvname, chunk_bounds,
                mip=resolution, parallel=parallel)

    # clefts won't be downsampled - will do that myself below
    clefts = timed(f"Reading cleft chunk at MIP 0",
                   io.read_cloud_volume_chunk,
                   cleft_cvname, base_bounds,
                   mip=0, parallel=parallel)
    seg = timed(f"Reading segmentation chunk at {resolution}",
                io.read_cloud_volume_chunk,
                seg_cvname, chunk_bounds, mip=resolution,
                parallel=parallel)

    assoc_net = timed("Reading association network",
                      taskio.read_network_from_proc,
                      proc_dir).cuda()

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

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "edge", timing_tag, proc_url)


def merge_edges_task(voxel_res, dist_thr, size_thr, proc_url, timing_tag=None):

    start_time = time.time()

    edges_arr = timed("Reading all edges",
                      taskio.read_all_chunk_edge_infos,
                      proc_url)
    merged_cleft_info = timed("Reading merged cleft info",
                              taskio.read_merged_seg_info,
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

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "merge_edges", timing_tag, proc_url)


def pick_largest_edges_task(proc_url, clefthash=None, timing_tag=None):

    start_time = time.time()

    if clefthash is None:
        edges = timed("Reading all chunkwise edge info",
                      taskio.read_all_chunk_edge_infos,
                      proc_url)
    else:
        edges = timed(f"Reading edge info for cleft id hash {clefthash}",
                      taskio.read_hashed_edge_info,
                      proc_url,
                      clefthash=clefthash, merged=False)

    if edges.index.name == cn.seg_id:
        edges = edges.reset_index()

    largest_info = tasks.pick_largest_edges_task(edges, clefthash is not None)

    timed("Writing merged edge list",
          taskio.write_merged_edge_info,
          largest_info, proc_url)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "pick_edge", timing_tag, proc_url)


def merge_duplicates_task(voxel_res, dist_thr, size_thr,
                          src_proc_url, hash_index, fulldf_proc_url=None,
                          timing_tag=None):

    start_time = time.time()

    fulldf_proc_url = (src_proc_url if fulldf_proc_url is None
                       else fulldf_proc_url)

    edge_df = timed(f"Reading edges for hash index {hash_index}",
                    taskio.read_hashed_edge_info,
                    src_proc_url, hash_index, dedup=True)

    merged_cleft_info = timed(f"Reading merged seg info for ind {hash_index}",
                              taskio.read_merged_seg_info,
                              src_proc_url, hash_index)

    full_df, dup_id_map = tasks.merge_duplicates_task(merged_cleft_info,
                                                      edge_df, dist_thr,
                                                      voxel_res, size_thr)

    # Considered using a transaction here, but that breaks generality
    # when src_proc_url != fulldf_proc_url and writing the dup_id_map
    # twice shouldn't cause any bad effects. Testing should evaluate this
    # call.
    timed("Writing duplicate id mapping for hash index",
          taskio.write_dup_id_map,
          dup_id_map, src_proc_url)
    timed("Writing final DataFrame for hash index",
          taskio.write_full_info,
          full_df, fulldf_proc_url,
          tag=hash_index)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "merge_dups", timing_tag, src_proc_url)


def chunk_overlaps_task(seg_cvname, base_seg_cvname,
                        chunk_begin, chunk_end,
                        proc_url, mip=0, seg_mip=None,
                        parallel=1, timing_tag=None):

    start_time = time.time()

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

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "chunk_overlap", timing_tag, proc_url)


def merge_overlaps_task(proc_url, timing_tag=None):

    start_time = time.time()

    overlap_arr = timed("Reading overlap matrices",
                        taskio.read_all_overlap_mats,
                        proc_url)

    max_overlaps = tasks.merge_overlaps_task(overlap_arr)

    timed("Writing max overlaps",
          taskio.write_max_overlaps,
          max_overlaps, proc_url)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "merge_overlap", timing_tag, proc_url)


def remap_ids_task(seg_in_cvname, seg_out_cvname,
                   chunk_begin, chunk_end, proc_url,
                   dup_map_proc_url=None,
                   mip=0, parallel=1, timing_tag=None):

    dup_map_proc_url = (proc_url
                        if dup_map_proc_url is None else dup_map_proc_url)

    start_time = time.time()

    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    chunk_id_map = timed("Reading chunk id map",
                         taskio.read_chunk_id_map,
                         proc_url, chunk_bounds)

    dup_id_map = timed("Reading duplicate id map",
                       taskio.read_dup_id_map,
                       dup_map_proc_url)

    seg = timed("Reading cleft chunk",
                io.read_cloud_volume_chunk,
                seg_in_cvname, chunk_bounds,
                mip=mip, parallel=parallel)

    seg = tasks.remap_ids_task(seg, chunk_id_map, dup_id_map, copy=False)

    timed("Writing results",
          io.write_cloud_volume_chunk,
          seg, seg_out_cvname, chunk_bounds,
          mip=mip, parallel=parallel)

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "remap", timing_tag, proc_url)


def anchor_task(cleft_cvname, seg_cvname, proc_url,
                chunk_begin, chunk_end, root_seg_cvname=None,
                voxel_res=[4, 4, 40], min_box_width=[100, 100, 5],
                mip=0, seg_mip=None, parallel=1, timing_tag=None):

    start_time = time.time()

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

    if timing_tag is not None:
        timed("Writing total task time",
              taskio.write_task_timing,
              time.time() - start_time, "chunk_anchor", timing_tag, proc_url)
