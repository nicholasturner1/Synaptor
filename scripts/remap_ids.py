#!/usr/bin/env python3
__doc__ = """
Remap IDs

-Read connected components for a chunk
-Read id mapping for the same chunk
-Apply the id mapping
-Write the new chunk to the same location
"""
import synaptor as s


def main(cc_fname_in, cc_fname_out, chunk_begin, chunk_end, proc_dir_path):

    chunk_bounds = s.BBox3d(chunk_begin, chunk_end)

    #Reading
    chunk_id_map = s.clefts.io.read_chunk_id_map(proc_dir_path, chunk_bounds)
    dup_id_map = s.merge.io.read_dup_id_map(proc_dir_path)
    cc_chunk = s.io.local.read_h5(cc_fname_in)


    #Processing
    chunk_id_map = s.merge.update_id_map(chunk_id_map, dup_id_map)
    cc_chunk = s.seg_utils.relabel_data_lookup_arr(cc_chunk, chunk_id_map)


    #Writing
    s.io.local.write_h5(cc_chunk, cc_fname_out)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("cc_fname_in")
    parser.add_argument("cc_fname_out")
    parser.add_argument("proc_dir_path")

    parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
    parser.add_argument("--chunk_end", nargs="+", type=int, required=True)


    args = parser.parse_args()
    main(**vars(args))
