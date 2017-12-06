#!/usr/bin/env python3
__doc__ = """
Connected Component Consolidation

-Read continuations in each chunk
-Read info for psd segments in each chunk
-Find out which continuations are connected, and generate a full list of seg ids
-Write full psd segment info file to proc directory
-Write id mapping for each chunk
"""
import synaptor as s


def main(proc_dir_path, size_thr):

    #Reading
    cont_info_arr, _ = s.clefts.io.read_all_continuations(proc_dir_path)
    seg_info_arr, local_dir = s.clefts.io.read_seg_infos(proc_dir_path)
    chunk_bounds = s.io.extract_sorted_bboxes(local_dir)


    #Processing
    full_seg_info, chunk_id_maps = s.clefts.consolidate_info_arr(seg_info_arr)
    cont_info_arr = s.clefts.apply_chunk_id_maps(cont_info_arr, chunk_id_maps)
    cont_id_map = s.clefts.merge_connected_continuations(cont_info_arr)

    chunk_id_maps = s.clefts.update_chunk_id_maps(chunk_id_maps, cont_id_map)
    full_seg_info = s.clefts.merge_cont_info(full_seg_info, cont_id_map)

    size_thr_map  = s.clefts.enforce_size_threshold(full_seg_info, size_thr)
    chunk_id_maps = s.clefts.update_chunk_id_maps(chunk_id_maps, size_thr_map)


    #Writing
    s.clefts.io.write_full_seg_info(full_seg_info, proc_dir_path)
    s.clefts.io.write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")
    parser.add_argument("size_thr", type=int)


    args = parser.parse_args()
    main(**vars(args))
