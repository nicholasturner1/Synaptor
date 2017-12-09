#!/usr/bin/env python3
__doc__ = """
"""
import synaptor as s

import time


def main(out_cvname,  cc_cvname, proc_dir_path,
         chunk_begin, chunk_end, cc_thresh,
         sz_thresh,   dil_param):

    chunk_bounds = s.bbox.BBox3d(chunk_begin, chunk_end)

    #Reading
    start = time.time()
    output = s.io.read_cloud_volume_chunk(out_cvname, chunk_bounds)
    print("Reading in {} seconds".format(time.time() - start))


    #Processing
    start = time.time()
    dil_ccs = s.dilated_components(output, dil_param, cc_thresh)
    print("dilccs in {} seconds".format(time.time() - start))

    start = time.time()
    continuations = s.extract_all_continuations(dil_ccs)
    cont_ids = set(cont.segid for cont in continuations)
    print("continuations in {} seconds".format(time.time() - start))

    start = time.time()
    dil_ccs, sizes = s.filter_segs_by_size(dil_ccs, sz_thresh,
                                           to_ignore=cont_ids)
    print("filter in {} seconds".format(time.time() - start))

    offset  = chunk_bounds.min()
    start = time.time()
    centers = s.centers_of_mass(dil_ccs, offset=offset)
    print("centers in {} seconds".format(time.time() - start))
    start = time.time()
    bboxes  = s.bounding_boxes(dil_ccs, offset=offset)
    print("bboxes in {} seconds".format(time.time() - start))

    #Writing
    start = time.time()
    s.io.write_cloud_volume_chunk(dil_ccs, cc_cvname, chunk_bounds)
    s.clefts.io.write_chunk_continuations(continuations, chunk_bounds, proc_dir_path)
    s.clefts.io.write_chunk_seg_info(centers, sizes, bboxes, chunk_bounds, proc_dir_path)
    print("writing in {} seconds".format(time.time() - start))


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    # Input & Outputs
    parser.add_argument("out_cvname")
    parser.add_argument("cc_cvname")
    parser.add_argument("proc_dir_path")

    #Chunk Bounds
    parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
    parser.add_argument("--chunk_end", nargs="+", type=int, required=True)

    # Processing Parameters
    parser.add_argument("cc_thresh", type=float)
    parser.add_argument("sz_thresh", type=int)
    parser.add_argument("dil_param", type=int)


    args = parser.parse_args()
    main(**vars(args))
