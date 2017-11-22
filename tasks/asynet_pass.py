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


def main(img_cvname, cc_cvname, chunk_bounds, proc_dir_path):

    chunk_bounds = S.IO.parse_chunk_bounds(chunk_bounds)

    #Reading
    img = S.IO.read_cloud_volume_chunk(img_cvname, chunk_bounds)
    cc  = S.IO.read_cloud_volume_chunk(cc_cvname,  chunk_bounds)
    net = S.IO.import_network(proc_dir_path)


    #Processing
    edges = S.infer_edges(img, cc, net)


    #Writing
    S.IO.write_chunk_edges(edges, chunk_bounds, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("img_cvname")
    parser.add_argument("cc_cvname")
    parser.add_argument("chunk_bounds", nargs="+", type=int)
    parser.add_argument("proc_dir_path")


    args = parser.parse_args()
    main(**vars(args))
