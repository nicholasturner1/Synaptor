#!/usr/bin/env python3
__doc__ = """
Merge Edges
"""
import synaptor as s


def main(proc_dir_path, dist_thr, voxel_res):

    #Reading
    edges_arr, _  = s.edges.io.read_all_edges(proc_dir_path)
    cleft_info_df = s.clefts.io.read_cons_cleft_info(proc_dir_path)


    #Processing
    full_edge_df = s.consolidate_edges(edges_arr)
    full_df = s.merge_dframes(cleft_info_df, full_edge_df)

    dup_id_map = s.merge_duplicate_clefts(full_df, dist_thr, voxel_res)
    full_df = s.merge_full_df(full_df, dup_id_map)


    #Writing
    s.merge.io.write_dup_id_map(dup_id_map, proc_dir_path)
    s.merge.io.write_cons_edge_list(full_edge_df, proc_dir_path)
    s.merge.io.write_final_df(full_df, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")
    parser.add_argument("dist_thr", type=int)
    parser.add_argument("--voxel_res", nargs="+", type=int, required=True)


    args = parser.parse_args()
    main(**vars(args))
