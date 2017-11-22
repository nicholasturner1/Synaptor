#!/usr/bin/env python3
__doc__ = """
Chunkwise Connected Components

-Pull a chunk of PSD output
-Perform dilated connected components
-Threshold components by size
-Write components back to a new cloud volume
-Write info for each segment (COM, size, bounding box) to the proc directory
-Write continuations (segments contacting the chunk edges) to the proc directory
"""
import Synaptor as S


def main(psd_cvname, cc_cvname, chunk_bounds, cc_thresh,
         sz_thresh, dil_param, proc_dir_path):

    chunk_bounds = S.IO.parse_chunk_bounds(chunk_bounds)

    #Reading
    psd_output = S.IO.read_cloud_volume_chunk(psd_cvname, chunk_bounds)


    #Processing
    dil_ccs = S.dilated_conncomps(psd_output, cc_thresh, dil_param)
    dil_ccs, sizes = S.filter_segs_by_size(dil_ccs, sz_thresh)

    offset  = S.extract_offset(chunk_bounds)
    centers = S.centers_of_mass(dil_ccs, chunk_bounds)
    bboxes  = S.bounding_boxes(dil_ccs, chunk_bounds)

    continuations = S.find_continuations(dil_ccs)
    sizes,   cont_sizes   = split_seg_cont_info(sizes, continuations)
    bboxes,  cont_bboxes  = split_seg_cont_info(bboxes, continuations)
    centers, cont_centers = split_seg_cont_info(centers, continuations)


    #Writing
    S.IO.write_cloud_volume_chunk(dil_ccs, cc_cvname, chunk_bounds)
    S.IO.write_chunk_continuations(continuations, cont_centers, cont_bboxes,
                                   cont_sizes, proc_dir_path)
    S.IO.write_chunk_seg_info(centers, sizes, bboxes, proc_dir_path)


def split_seg_cont_info(info_dict, continuations):
    """
    Splits a dictionary into two:
     -one containing the ids for continuations
     -one containing info for full segments
    """

    seg_dict = {}
    cont_dict = {}

    cont_ids = Set([ c.getid() for c in continuations ])

    for (i,value) in info_dict.items():

        if i in cont_ids:
            cont_dict[i] = value
        else:
            seg_dict[i]  = value

    return seg_dict, cont_dict


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("psd_cvname")
    parser.add_argument("cc_cvname")
    parser.add_argument("chunk_bounds")

    parser.add_argument("cc_thresh")
    parser.add_argument("sz_thresh")
    parser.add_argument("dil_param")
    parser.add_argument("proc_dir_path")


    args = parser.parse_args()
    main(**vars(args))
