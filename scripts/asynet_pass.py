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


def main(img_fname, cc_fname, seg_fname,
         chunk_begin, chunk_end, patchsz,
         num_samples_per_cleft, dil_param,
         proc_dir_path):

    chunk_bounds = s.BBox3d(chunk_begin, chunk_end)
    offset = chunk_bounds.min()

    #Reading
    img    = s.io.local.read_h5(img_fname)
    clefts = s.io.local.read_h5(cc_fname)
    seg    = s.io.local.read_h5(seg_fname)
    net    = s.edges.io.read_network(proc_dir_path)


    #Processing
    edges = s.edges.infer_edges(net, img, psd, seg,
                                offset, patchsz,
                                num_samples_per_cleft,
                                dil_param)

    edges = s.edges.add_seg_size(edges, psd)


    #Writing
    s.edges.io.write_chunk_edges(edges, chunk_bounds, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("img_fname")
    parser.add_argument("cc_fname")
    parser.add_argument("num_samples_per_cleft", type=int)
    parser.add_argument("dil_param", type=int)
    parser.add_argument("proc_dir_path")

    parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
    parser.add_argument("--chunk_end", nargs="+", type=int, required=True)
    parser.add_argument("--patchsz", nargs="+", type=int, required=True)


    args = parser.parse_args()
    main(**vars(args))
