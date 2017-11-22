#!/usr/bin/env python3
__doc__ = """
Connected Component Consolidation

-Read continuations in each chunk
-Read info for psd segments in each chunk
-Find out which continuations are connected, and generate a full list of seg ids
-Write full psd segment info file to proc directory
-Write id mapping for each chunk
"""
import Synaptor as S


def main(proc_dir_path):

    #Reading
    edges_arr = S.IO.read_all_edges(proc_dir_path)


    #Processing
    same_seg_edges, unique_seg_edges = S.find_same_psd_edges(edges_arr)
    consolidated_edges = S.consolidate_edges(same_seg_edges)
    full_edge_list = S.append_edges(unique_seg_edges, consolidated_edges)


    #Writing
    S.IO.write_full_edge_list(full_edge_list, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")


    args = parser.parse_args()
    main(**vars(args))
