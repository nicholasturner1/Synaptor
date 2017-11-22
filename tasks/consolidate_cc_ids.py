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


def main(cc_cvname, proc_dir_path):

    #Reading
    continuation_info_arr = S.IO.read_continuations(proc_dir_path)
    seg_info_arr = S.IO.read_seg_infos(proc_dir_path)


    #Processing
    full_seg_info, chunk_id_maps = S.consolidate_info_arr(seg_info_arr)
    continuation_info_arr = S.apply_chunk_id_maps(continuation_info_arr)
    cont_id_maps = S.find_connected_continuations(continuation_info_arr)

    chunk_id_maps = S.update_chunk_id_maps(chunk_id_maps, cont_id_maps)
    full_seg_info = S.merge_cont_info(full_seg_info, cont_id_maps)


    #Writing
    S.IO.write_full_seg_info(full_seg_info, proc_dir_path)
    S.IO.write_chunk_id_maps(chunk_id_maps, proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()


    parser.add_argument("cc_cvname")
    parser.add_argument("proc_dir_path")


    args = parser.parse_args()
    main(**vars(args))
