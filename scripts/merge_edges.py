#!/usr/bin/env python3
__doc__ = """
Merge Edges
"""
import synaptor as s

import time
size_thr = 200


def main(voxel_res, dist_thr, proc_dir_path):

    #Reading
    print("Reading all edges & cons cleft info"); start = time.time()
    edges_arr, _   = s.edges.io.read_all_edges(proc_dir_path)
    cleft_info_df  = s.clefts.io.read_cons_cleft_info(proc_dir_path)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    #Processing
    print("Consolidating edges"); start = time.time()
    full_edge_df = s.consolidate_edges(edges_arr)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Merging edge dataframe to cleft dataframe"); start = time.time()
    full_df = s.merge_dframes(cleft_info_df, full_edge_df)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    print("Merging duplicate clefts"); start = time.time()
    dup_id_map = s.merge_duplicate_clefts(full_df, dist_thr, voxel_res)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Merging full dataframe"); start = time.time()
    full_df = s.merge_full_df(full_df, dup_id_map)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Enforcing size threshold"); start = time.time()
    size_thr_map = s.enforce_size_threshold(full_df, size_thr)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Updating dup id map (size)"); start = time.time()
    s.merge.clefts.update_id_map(dup_id_map, size_thr_map)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    #Writing
    print("Writing id map, cons edge list, and final dataframe"); start = time.time()
    s.merge.io.write_dup_id_map(dup_id_map, proc_dir_path)
    s.merge.io.write_cons_edge_list(full_edge_df, proc_dir_path)
    s.merge.io.write_final_df(full_df, proc_dir_path)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")
    parser.add_argument("dist_thr", type=int)
    parser.add_argument("--voxel_res",nargs="+", type=int)


    args = parser.parse_args()
    main(**vars(args))
