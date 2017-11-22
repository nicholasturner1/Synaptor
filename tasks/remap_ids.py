#!/usr/bin/env python3
__doc__ = """
Remap IDs

-Read connected components for a chunk
-Read id mapping for the same chunk
-Apply the id mapping
-Write the new chunk to the same location
"""
import Synaptor as S


def main(cc_cvname, chunk_bounds, proc_dir_path):

    chunk_bounds = S.IO.parse_chunk_bounds(chunk_bounds)

    #Reading
    chunk_id_map = S.IO.read_chunk_id_map(proc_dir_path, chunk_bounds)
    cc_chunk = S.IO.read_cloud_volume_chunk(cc_cvname, chunk_bounds)


    #Processing
    cc_chunk = S.relabel_data_lookup_arr(cc_chunk, chunk_id_map)


    #Writing
    S.IO.write_cloud_volume_chunk(cc_chunk, cc_cvname, chunk_bounds)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("cc_cvname")
    parser.add_argument("chunk_bounds", nargs="+", type=int)
    parser.add_argument("proc_dir_path")


    args = parser.parse_args()
    main(**vars(args))
