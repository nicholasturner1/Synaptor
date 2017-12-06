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


def main(proc_dir_path):

    #Reading
    edges_arr, _ = s.edges.io.read_all_edges(proc_dir_path)


    #Processing
    full_edge_list = s.edges.consolidate_edges(edges_arr)


    #Writing
    s.edges.io.write_full_edge_list(full_edge_list, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("proc_dir_path")


    args = parser.parse_args()
    main(**vars(args))
