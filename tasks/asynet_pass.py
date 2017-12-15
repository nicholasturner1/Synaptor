#!/usr/bin/env python3
__doc__ = """
Asynet Pass
"""
import synaptor as s

import time


def main(img_cvname, cc_cvname, seg_cvname,
         chunk_begin, chunk_end, patchsz,
         num_samples_per_cleft, dil_param,
         proc_dir_path):

    chunk_bounds = s.BBox3d(chunk_begin, chunk_end)
    offset = chunk_bounds.min()

    #Reading
    print("Reading cloud volume chunks"); start = time.time()
    img    = s.io.read_cloud_volume_chunk(img_cvname, chunk_bounds)
    clefts = s.io.read_cloud_volume_chunk(cc_cvname, chunk_bounds)
    seg    = s.io.read_cloud_volume_chunk(seg_cvname, chunk_bounds)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Reading network files"); start = time.time()
    net    = s.edges.io.read_network(proc_dir_path)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    print("Reading chunk id map"); start = time.time()
    chunk_id_map = s.clefts.io.read_chunk_id_map(proc_dir_path, chunk_bounds)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    #Processing
    print("Relabelling clefts"); start = time.time()
    clefts = s.seg_utils.relabel_data_lookup_arr(clefts, chunk_id_map)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Performing Asynet inference"); start = time.time()
    edges = s.edges.infer_edges(net, img, clefts, seg,
                                offset, patchsz,
                                num_samples_per_cleft,
                                dil_param)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))

    print("Computing cleft size and adding to edge dframe"); start = time.time()
    edges = s.edges.add_seg_size(edges, clefts)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


    #Writing
    print("Writing chunk edges"); start = time.time()
    s.edges.io.write_chunk_edges(edges, chunk_bounds, proc_dir_path)
    print("Complete in {0:.3f} seconds\n".format(time.time() - start))


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("img_cvname")
    parser.add_argument("cc_cvname")
    parser.add_argument("seg_cvname")
    parser.add_argument("num_samples_per_cleft", type=int)
    parser.add_argument("dil_param", type=int)
    parser.add_argument("proc_dir_path")

    parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
    parser.add_argument("--chunk_end", nargs="+", type=int, required=True)
    parser.add_argument("--patchsz", nargs="+", type=int, required=True)


    args = parser.parse_args()
    main(**vars(args))
