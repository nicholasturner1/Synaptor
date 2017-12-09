#!/usr/bin/env python3
__doc__ = """
Merge Edges
"""
import synaptor as s


def main(voxel_res, dist_thr, proc_dir_path):

    #Reading
    edges_arr, _   = s.edges.io.read_all_edges(proc_dir_path)
    cleft_info_df  = s.clefts.io.read_cons_cleft_info(proc_dir_path)


    #Processing
    full_edge_df = s.edges.consolidate_edges(edges_arr)
    full_df = s.edges.merge_dframes(cleft_info_df, full_edge_df)

    dup_id_map = s.clefts.merge_duplicate_clefts(full_df, dist_thr, voxel_res)
    full_df = s.edges.merge_edge_info(full_df, dup_id_map)


    #Writing
    s.edges.io.write_dup_id_map(dup_id_map, proc_dir_path)
    s.edges.io.write_full_edge_list(full_edge_df, proc_dir_path)
    s.edges.io.write_final_dataframe(full_df, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")


    args = parser.parse_args()
    main(**vars(args))
