#!/usr/bin/env python3
__doc__ = """
Chunk Anchors Wrapper Script
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("cleft_cvname")
parser.add_argument("seg_cvname")
parser.add_argument("proc_dir_path")

# Processing Parameters
parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
parser.add_argument("--chunk_end", nargs="+", type=int, required=True)
parser.add_argument("--parallel", type=int, default=1)
parser.add_argument("--mip", nargs="+", type=int, default=(0,))
parser.add_argument("--seg_mip", nargs="+", type=int, default=None)
parser.add_argument("--wshed_cvname", default=None)
parser.add_argument("--min_box_width", nargs="+",
                    type=int, default=(100, 100, 5))
parser.add_argument("--voxel_res", nargs="+", type=int, default=(4, 4, 40))


# MIP arguments can specify voxel resolutions or mip index
def mip_or_res(x): return x[0] if (x is not None and len(x) == 1) else x


args = parser.parse_args()
args.mip = mip_or_res(args.mip)
args.seg_mip = mip_or_res(args.seg_mip)
print(vars(args))


s.proc_tasks.tasks_w_io.anchor_task(**vars(args))
