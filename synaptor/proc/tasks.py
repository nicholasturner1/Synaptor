""" Base processing tasks for cloud workflows """


import time

from .. import seg_utils
from . import seg
from . import edge
from . import overlap
from . import anchor
from . import hashing
from . import utils
from . import colnames as cn


def timed(fn_desc, fn, *args, **kwargs):
    """ Measures the execution time of the passed function """
    print(fn_desc)
    start = time.time()
    result = fn(*args, **kwargs)
    print(f"{fn_desc} complete in {time.time() - start:.3f}s")

    return result


def cc_task(desc_vol, cc_thresh, sz_thresh, offset=(0, 0, 0)):
    """
    - Performs connected components over a data description volume
    - Extracts segments that possibly continue
      to the next chunk (continuations)
    - Filters out any complete segments under the size threshold
    - Records the centroid, size, and bounding box for the surviving
      segments in a DataFrame

    Returns:
    - Connected Components (3d np array)
    - Continuations for the chunk
    - DataFrame of cleft info
    """
    ccs = timed("Running connected components",
                seg.connected_components,
                desc_vol, cc_thresh)

    continuations, cont_ids = timed("Extracting continuations",
                                    seg.continuation.extract_all_continuations,
                                    ccs)

    ccs, sizes = timed("Filtering complete segments by size",
                       seg_utils.filter_segs_by_size,
                       ccs, sz_thresh, to_ignore=cont_ids)

    centers = timed("Computing seg centroids",
                    seg_utils.centers_of_mass,
                    ccs, offset=offset)
    bboxes = timed("Computing seg bounding boxes",
                   seg_utils.bounding_boxes,
                   ccs, offset=offset)

    cleft_info = timed("Making seg info DataFrame",
                       seg.make_seg_info_dframe,
                       centers, sizes, bboxes)

    return ccs, continuations, cleft_info


def merge_ccs_task(cont_info_arr, cleft_info_arr,
                   size_thr, max_face_shape):
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

    cons_cleft_info, chunk_id_maps = timed("Assigning new cleft ids",
                                           seg.merge.assign_unique_ids_serial,
                                           cleft_info_arr)
    print(cons_cleft_info.columns)

    cont_info_arr = timed("Applying chunk_id_maps to continuations",
                          seg.merge.apply_chunk_id_maps,
                          cont_info_arr, chunk_id_maps)

    cont_id_map = timed("Merging connected continuations",
                        seg.merge.merge_continuations,
                        cont_info_arr, max_face_shape)

    chunk_id_maps = timed("Updating chunk id maps",
                          seg.merge.update_chunk_id_maps,
                          chunk_id_maps, cont_id_map)

    cons_cleft_info = timed("Merging cleft dataframes",
                            seg.merge.merge_seg_df,
                            cons_cleft_info, cont_id_map)

    size_thr_map = timed("Enforcing size threshold over merged ccs",
                         seg.merge.enforce_size_threshold,
                         cons_cleft_info, size_thr)

    chunk_id_maps = timed("Updating chunk id maps (for size thresholding)",
                          seg.merge.update_chunk_id_maps,
                          chunk_id_maps, size_thr_map)

    return cons_cleft_info, chunk_id_maps


def match_continuations_task(contins1, contins2, max_face_shape=(1024, 1024),
                             id_map1=None, id_map2=None):

    if id_map1 is not None:
        seg.merge.apply_id_map(contins1, id_map1)

    if id_map2 is not None:
        seg.merge.apply_id_map(contins2, id_map2)

    graph_edges = timed("Matching continuations",
                        seg.merge.match_continuations,
                        contins1, contins2, face_shape=max_face_shape)

    return graph_edges


def seg_graph_cc_task(graph_edges, hashmax, all_ids):
    ccs = timed("Finding connected components",
                utils.find_connected_components,
                graph_edges)

    seg_merge_map = timed("Making seg merge_map",
                          utils.make_id_map,
                          ccs)

    seg_merge_map = timed("Expanding mapping to include all ids",
                          seg.merge.expand_id_map,
                          seg_merge_map, all_ids)

    seg_merge_df = timed("Making map dataframe",
                         seg.merge.misc.make_map_dframe,
                         seg_merge_map)

    seg_merge_df = timed("Hashing dst id",
                         hashing.add_hashed_index,
                         seg_merge_df, [cn.dst_id], hashmax,
                         indexname=cn.dst_id_hash)

    return seg_merge_df


def merge_seginfo_task(seginfo_dframe):

    return timed("Merging seginfo dataframe",
                 seg.merge.merge_seginfo_df,
                 seginfo_dframe, new_id_colname=cn.dst_id)


def edge_task(img, clefts, seg, assoc_net,
              patchsz, offset=(0, 0, 0), root_seg=None,
              samples_per_cleft=2, dil_param=5,
              id_map=None, hashmax=None, hash_fillval=-1):
    """
    -Applies an id map to a chunk (if passed)
    NOTE: Modifies the clefts array if id_map exists
    -Applies an assignment network to each cleft in the chunk
    -Computes the sizes of each cleft to assist later thresholding
    -Returns all of the computed information in a DataFrame

    Returns:
     -A DataFrame of info for each edge within this chunk
    """

    if id_map is not None:
        clefts = timed("Remapping cleft ids",
                       seg_utils.relabel_data,
                       clefts, id_map, copy=False)

    edges = timed("Inferring edges",
                  edge.infer_edges,
                  assoc_net, img, clefts, seg,
                  offset=offset, patchsz=patchsz,
                  samples_per_cleft=samples_per_cleft,
                  root_seg=root_seg, dil_param=dil_param)

    edges = timed("Computing cleft size and adding it to dframe",
                  edge.add_cleft_sizes,
                  edges, clefts)

    if hashmax is not None:
        edges = timed("Hashing partner id combinations",
                      hashing.add_hashed_index,
                      edges, [cn.presyn_id, cn.postsyn_id], hashmax,
                      indexname=cn.partnerhash,
                      null_fillval=hash_fillval)

        edges = timed("Hashing cleft ids",
                      hashing.add_hashed_index,
                      edges, [cn.seg_id], hashmax,
                      indexname=cn.clefthash)

    return edges


def pick_largest_edges_task(edges, single_dframe=False):
    if single_dframe:
        return timed("Merging edges",
                     edge.merge.pick_largest_edges,
                     edges)
    else:
        return timed("Merging edges",
                     edge.merge.pick_largest_edges_arr,
                     edges)


def merge_duplicates_task(cleft_info, edge_info,
                          dist_thr, voxel_res, size_thr):
    """ Parallelizable edge.merge """
    full_df = timed("Merging edge DataFrame to cleft DataFrame",
                    edge.merge.merge_to_cleft_df,
                    edge_info, cleft_info)

    dup_id_map = timed("Merging duplicate clefts",
                       edge.merge.merge_duplicate_clefts,
                       full_df, dist_thr, voxel_res)

    full_df = timed("Merging duplicates within full dataframe",
                    edge.merge.merge_full_df,
                    full_df, dup_id_map)

    size_thr_map = timed("Enforcing size threshold over merged ccs",
                         seg.merge.enforce_size_threshold,
                         full_df, size_thr)

    merged_id_map = timed("Updating duplicate id map with size threshold map",
                          edge.merge.update_id_map,
                          dup_id_map, size_thr_map)

    return full_df, merged_id_map


def merge_edges_task(edge_info, cleft_info, voxel_res,
                     dist_thr, size_thr, single_edge_info=False):
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

    merged_edge_info = pick_largest_edges_task(
                           edge_info, single_dframe=single_edge_info)

    full_df, merged_id_map = merge_duplicates_task(cleft_info,
                                                   merged_edge_info, voxel_res,
                                                   dist_thr, size_thr)

    return full_df, merged_id_map, merged_edge_info


def chunk_overlaps_task(segs, base_segs):
    """
    Determines the overlap matrix between segments of interest overlap with
    a base segmentation
    """
    return timed("Counting overlaps",
                 overlap.count_overlaps,
                 segs, base_segs)


def merge_overlaps_task(overlaps_arr):
    """
    -Merges the chunk overlap matrices into one,
    -Returns a mapping from segment to base segment of max overlap
    """
    full_overlap = timed("Merging overlap matrices",
                         overlap.merge.consolidate_overlaps,
                         overlaps_arr)

    return timed("Finding segments with maximal overlap",
                 overlap.merge.find_max_overlaps,
                 full_overlap)


def remap_ids_task(clefts, *id_maps, copy=False):
    """
    -Maps the ids within clefts according to a list of id_maps
    NOTE: id maps will be applied in the order listed as args

    Returns:
     -Remapped clefts
    """

    id_map = id_maps[0]
    for (i, next_map) in enumerate(id_maps[1:]):
        id_map = timed("Updating id map: round {i}".format(i=i+1),
                       edge.merge.update_id_map,
                       id_map, next_map, reused_ids=True)

    clefts = timed("Relabeling data by id map",
                   seg_utils.relabel_data,
                   clefts, id_map, copy=copy)

    return clefts


def anchor_task(edge_info, seg, clf, chunk_begin,
                voxel_res=[4, 4, 40], min_box_width=[100, 100, 5],
                root_seg=None):
    """
    -Places centralized anchor points for presynaptic and postsynaptic
    terminals
    """

    return timed("Placing anchor points",
                 anchor.place_anchor_pts,
                 edge_info, seg, clf, verbose=True,
                 voxel_res=voxel_res, offset=chunk_begin,
                 min_box_width=min_box_width, root_seg=root_seg)
