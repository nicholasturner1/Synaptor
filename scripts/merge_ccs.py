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

import time


def main(proc_dir_path, size_thr):

    #Reading
    print("Reading continuations"); start = time.time()
    cont_info_arr, _ = s.clefts.io.read_all_continuations(proc_dir_path)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Reading cleft info dataframes"); start = time.time()
    cleft_info_arr, local_dir = s.clefts.io.read_seg_infos(proc_dir_path)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))
    chunk_bounds = s.io.extract_sorted_bboxes(local_dir)


    #Processing
    print("Consolidating cleft dataframes"); start = time.time()
    cons_cleft_info, chunk_id_maps = s.consolidate_cleft_info_arr(cleft_info_arr)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Applying chunk id maps to continuations"); start = time.time()
    cont_info_arr = s.apply_chunk_id_maps(cont_info_arr, chunk_id_maps)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Merging connected continuations"); start = time.time()
    cont_id_map = s.merge_connected_continuations(cont_info_arr)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    print("Updating chunk id maps"); start = time.time()
    chunk_id_maps = s.update_chunk_id_maps(chunk_id_maps, cont_id_map)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Merging cleft dataframes"); start = time.time()
    cons_cleft_info = s.merge_cleft_df(cons_cleft_info, cont_id_map)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    print("Enforcing size threshold"); start = time.time()
    size_thr_map  = s.enforce_size_threshold(cons_cleft_info, size_thr)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Updating chunk id maps (for size)"); start = time.time()
    chunk_id_maps = s.update_chunk_id_maps(chunk_id_maps, size_thr_map)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    #Writing
    print("Writing results"); start = time.time()
    s.clefts.io.write_cons_cleft_info(cons_cleft_info, proc_dir_path)
    s.clefts.io.write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_dir_path)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")
    parser.add_argument("size_thr", type=int)


    args = parser.parse_args()
    main(**vars(args))
