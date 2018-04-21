#!/usr/bin/env python3

import os
import shutil

import synaptor as s


def main(img_cvname, out_cvname, cleft_cvname, seg_cvname,
         cc_thresh, sz_thresh1, sz_thresh2,
         asynet_patchsz, samples_per_cleft, dil_param,
         voxel_res, merge_dist_thr,
         vol_shape, chunk_shape, proc_dir_path, 
         cleft_chunk_shape, description,
         asynet_fname, asynet_chkpt_fname):

    init_proc_dir(proc_dir_path, asynet_fname, asynet_chkpt_fname)

    init_cleft_vol(cleft_cvname, voxel_res, description, vol_shape,
                   cleft_chunk_shape)

    chunk_bboxes = s.types.bbox.chunk_bboxes(vol_shape, chunk_shape)

    run_chunk_ccs(chunk_bboxes, out_cvname, cleft_cvname, 
                  proc_dir_path, cc_thresh, sz_thresh1)

    run_merge_ccs(proc_dir_path, sz_thresh1)

    run_chunk_edges(chunk_bboxes, img_cvname, cleft_cvname, seg_cvname,
                    asynet_patchsz, samples_per_cleft, dil_param, proc_dir_path)

    run_merge_edges(voxel_res, merge_dist_thr, sz_thresh2, proc_dir_path)

    run_remap_ids(chunk_bboxes, cleft_cvname, cleft_cvname, proc_dir_path)


def init_proc_dir(proc_dir_path, asynet_fname, asynet_chkpt_fname):

    mkdir(proc_dir_path)

    mkdir(os.path.join(proc_dir_path,"cleft_infos"))
    mkdir(os.path.join(proc_dir_path,"continuations"))
    mkdir(os.path.join(proc_dir_path,"chunk_edges"))
    mkdir(os.path.join(proc_dir_path,"network"))

    net_fname = os.path.join(proc_dir_path, "network","net.py")
    net_chkpt = os.path.join(proc_dir_path, "network","net.chkpt")

    shutil.copyfile(asynet_fname, net_fname)   
    shutil.copyfile(asynet_chkpt_fname, net_chkpt)   


def mkdir(dir_path):
    if not os.path.isdir(dir_path):
         os.makedirs(dir_path)

    
def init_cleft_vol(cleft_cvname, voxel_res, description, vol_shape,
                   chunk_size):
    s.io.init_seg_volume(cleft_cvname, voxel_res, vol_shape, description, "Nick",
                         chunk_size=chunk_size)


def run_chunk_ccs(chunk_bboxes, out_cvname, cleft_cvname, 
                  proc_dir_path, cc_thresh, sz_thresh):
    """chunk_ccs"""
    for cb in chunk_bboxes:
        chunk_begin, chunk_end = cb.min(), cb.max()
        s.proc_tasks.tasks_w_io.chunk_ccs_task(out_cvname, cleft_cvname,
                                               proc_dir_path, chunk_begin,
                                               chunk_end, cc_thresh, sz_thresh)


def run_merge_ccs(proc_dir_path, sz_thresh):
    """merge_ccs"""
    s.proc_tasks.tasks_w_io.merge_ccs_task(proc_dir_path, sz_thresh)


def run_chunk_edges(chunk_bboxes, img_cvname, cleft_cvname, seg_cvname,
                    patchsz, samples_per_cleft, dil_param, proc_dir_path):
    """chunk_edges"""
    for cb in chunk_bboxes:
        chunk_begin, chunk_end = cb.min(), cb.max()
        s.proc_tasks.tasks_w_io.chunk_edges_task(img_cvname, cleft_cvname,
                                                seg_cvname, chunk_begin,
                                                chunk_end, patchsz,
                                                samples_per_cleft, dil_param,
                                                proc_dir_path)


def run_remap_ids(chunk_bboxes, input_cvname, output_cvname, proc_dir_path):
    """remap_ids"""
    for cb in chunk_bboxes:
        chunk_begin, chunk_end = cb.min(), cb.max()
        s.proc_tasks.tasks_w_io.remap_ids_task(input_cvname, output_cvname,
                                               chunk_begin, chunk_end,
                                               proc_dir_path)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)

    #Always Required
    parser.add_argument("img_cvname")
    parser.add_argument("out_cvname")
    parser.add_argument("cleft_cvname")
    parser.add_argument("seg_cvname")
    parser.add_argument("cc_thresh")
    parser.add_argument("sz_thresh1")
    parser.add_argument("sz_thresh2")
    parser.add_argument("proc_dir_path")

    parser.add_argument("--vol_shape", nargs="+", type=int, required=True)
    parser.add_argument("--chunk_shape", nargs="+", type=int, required=True)
    parser.add_argument("--asynet_patchsz", nargs="+", type=int, required=True)
    parser.add_argument("--description", required=True)

    #Optional
    parser.add_argument("--voxel_res", nargs="+", type=int, default=(4,4,40))
    parser.add_argument("--cleft_chunk_shape", nargs="+", type=int, default=(64,64,64))
    parser.add_argument("--samples_per_cleft", type=int, default=2)
    parser.add_argument("--dil_param", type=int, default=5)
    parser.add_argument("--merge_dist_thr", type=int, default=1000)
   
    args = parser.parse_args()

    main(**vars(args))
