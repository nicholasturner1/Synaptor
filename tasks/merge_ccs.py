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
    cleft_info_arr, local_dir = s.clefts.io.read_seg_infos(proc_dir_path)
    chunk_bounds = s.io.extract_sorted_bboxes(local_dir)


    #Processing
    cons_cleft_info, chunk_id_maps = s.consolidate_cleft_info_arr(cleft_info_arr)
    cont_info_arr = s.apply_chunk_id_maps(cont_info_arr, chunk_id_maps)
    cont_id_map = s.merge_connected_continuations(cont_info_arr)

    chunk_id_maps = s.update_chunk_id_maps(chunk_id_maps, cont_id_map)
    cons_cleft_info = s.merge_cleft_df(cons_cleft_info, cont_id_map)

    size_thr_map  = s.enforce_size_threshold(cons_cleft_info, size_thr)
    chunk_id_maps = s.update_chunk_id_maps(chunk_id_maps, size_thr_map)


    #Writing
    s.clefts.io.write_cons_cleft_info(cons_cleft_info, proc_dir_path)
    s.clefts.io.write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")
    parser.add_argument("size_thr", type=int)


    args = parser.parse_args()
    main(**vars(args))
