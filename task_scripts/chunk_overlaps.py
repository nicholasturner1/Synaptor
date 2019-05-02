#!/usr/bin/env python3
__doc__ = """
Chunk Overlaps Wrapper Script

Determines which segments of interest overlap with
base segs

Returns the overlap matrix
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("seg_cvname")
parser.add_argument("base_seg_cvname")
parser.add_argument("proc_dir_path")

# Processing Parameters
parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
parser.add_argument("--chunk_end", nargs="+", type=int, required=True)
parser.add_argument("--parallel", type=int, default=1)
parser.add_argument("--mip", nargs="+", type=int, default=(0,))
parser.add_argument("--seg_mip", nargs="+", type=int, default=None)
parser.add_argument("--timing_tag", default=None)


# MIP arguments can specify voxel resolutions or mip index
def mip_or_res(x): return x[0] if (x is not None and len(x) == 1) else x


args = parser.parse_args()
args.mip = mip_or_res(args.mip)
args.seg_mip = mip_or_res(args.seg_mip)
print(vars(args))


s.proc_tasks.tasks_w_io.chunk_overlaps_task(**vars(args))
