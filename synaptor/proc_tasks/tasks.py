#!/usr/bin/env python3
__doc__ = """
Synaptor Processing Tasks
"""

import time

from .. import io
from .. import types
from .. import seg_utils

from . import chunk_ccs
from . import merge_ccs
from . import chunk_edges
from . import merge_edges


def timed(fn_desc, fn, *args, **kwargs):
    """ Measures the execution time of the passed fn """
    print("{fn_desc}".format(fn_desc=fn_desc))
    start = time.time()
    result = fn(*args, **kwargs)
    print("{fn_desc} complete in {t:.3f}s".format(fn_desc=fn_desc,
                                                  t=time.time()-start))
    return result


def chunk_ccs_task(net_output, chunk_begin, chunk_end,
                   cc_thresh, sz_thresh):
    """
    - Performs connected components over a chunk of data
    - Extracts clefts that possibly continue to the next chunk (continuations)
    - Filters out any complete segments under the size threshold
    - Records the centroid, size, and bounding box for the surviving
      clefts in a DataFrame

    Returns:
    - Cleft Components (3d np array)
    - Continuations for the chunk
    - DataFrame of cleft info
    """
    chunk_bounds = types.BBox3d(chunk_begin, chunk_end)

    #Processing
    ccs = timed("Running connected components",
                chunk_ccs.connected_components3d,
                net_output, cc_thresh).astype("uint32")


    continuations = timed("Extracting continuations",
                          types.continuation.extract_all_continuations,
                          ccs)
    cont_ids = set(cont.segid for cont in continuations)


    ccs, sizes = timed("Filtering complete segments by size",
                       seg_utils.filter_segs_by_size,
                       ccs, sz_thresh, to_ignore=cont_ids)


    offset = chunk_bounds.min()
    centers = timed("Computing cleft centroids",
                    seg_utils.centers_of_mass,
                    ccs, offset=offset)
    bboxes = timed("Computing cleft bounding boxes",
                   seg_utils.bounding_boxes,
                   ccs, offset=offset)

    cleft_info = timed("Making cleft info DataFrame",
                       chunk_ccs.make_cleft_info_dframe,
                       centers, sizes, bboxes)

    return ccs, continuations, cleft_info


def merge_ccs_task(cont_info_arr, cleft_info_arr, chunk_bounds, size_thr):
    """
    -Assigns a global set of cleft segment ids
    -Finds which continuations match across chunks
    -Makes an id mapping that merges the matching continuations for each chunk
    -Merges the cleft info dataframes into one for the entire dataset
    -Maps any newly merged cleft segments to 0 if they're under the
     size threshold

    Returns:
        -A single DataFrame for all merged clefts
        -A nparray of id maps for each chunk
    """

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

    return cons_cleft_info, chunk_id_maps


def chunk_edges_task(img, clefts, seg, asynet,
                     chunk_bounds, patchsz,
                     num_samples_per_cleft=2,
                     dil_param=5, id_map=None):
    """
    -Applies an id map to a chunk (if passed)
    -Applies an assignment network to each cleft in the chunk
    -Computes the sizes of each cleft to assist later thresholding
    -Returns all of the computed information in a DataFrame
    NOTE: Modifies the clefts array if id_map exists

    Returns:
     -A DataFrame of info for each edge within this chunk
    """

    if id_map is not None:
        clefts = timed("Remapping cleft ids",
                       seg_utils.relabel_data,
                       clefts, id_map, copy=False)

    offset = chunk_bounds.min()
    edges = timed("Inferring edges",
                  chunk_edges.infer_edges,
                  asynet, img, clefts, seg,
                  offset, patchsz, sampler_per_cleft=num_samples_per_cleft,
                  dil_param=dil_param)

    edges = timed("Computing cleft size and adding to edge dframe",
                  chunk_edges.add_seg_size,
                  edges, clefts)

    return edges


def merge_edges_task(edges_arr, merged_cleft_info,
                     voxel_res, dist_thr, size_thr):
    """
    -Maps together any edges that connect the same partners
     and are within some distance apart
    -Maps any newly merged cleft segments to 0 if they're under the
     size threshold

    Returns:
     -Combined cleft & edge dataframe
     -An id map that implements the duplicate and sz mapping
     -A merged edge dataframe (mostly for debugging along with #1)
    """

    merged_edge_df = timed("Merging edges",
                           merge_edges.consolidate_edges,
                           edges_arr)

    full_df = timed("Merging edge DataFrame to cleft DataFrame",
                    merge_edges.merge_dframes,
                    merged_cleft_info, merged_edge_df)

    dup_id_map = timed("Merging duplicate clefts",
                       merge_edges.merge_duplicate_clefts,
                       full_df, dist_thr, voxel_res)

    full_df = timed("Merging duplicates within full dataframe",
                    merge_edges.merge_full_df,
                    full_df, dup_id_map)

    size_thr_map = timed("Enforcing size threshold over merged ccs",
                         merge_ccs.enforce_size_threshold,
                         full_df, size_thr)

    merged_id_map = timed("Updating duplicate id map with size threshold map",
                          merge_edges.update_id_map,
                          dup_id_map, size_thr_map)

    return full_df, merged_id_map, merged_edge_df


def remap_ids_task(clefts, *id_maps, copy=False):
    """
    -Maps the ids within clefts according to a list of id_maps
    NOTE: id maps will be applied in the order listed as args

    Returns:
     -Remapped clefts
    """

    id_map = id_maps[0]
    for (i,next_map) in enumerate(id_maps[2:]):
        id_map = timed("Updating id map: round {i}".format(i=i+1),
                       merge_edges.update_id_map,
                       id_map, next_map)

    clefts = s.seg_utils.relabel_data(clefts, id_map, copy=copy)

    return clefts
