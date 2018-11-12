#!/usr/bin/env python3
__doc__ = """
Chunk Edges Wrapper Script

-Applies an id map to a chunk (if passed)
NOTE: Modifies the clefts array if id_map exists
-Applies an assignment network to each cleft in the chunk
-Computes the sizes of each cleft to assist later thresholding
-Returns all of the computed information in a DataFrame
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("img_cvname")
parser.add_argument("cleft_cvname")
parser.add_argument("seg_cvname")
parser.add_argument("proc_dir_path")
parser.add_argument("--wshed_cvname", default=None)

# Processing Parameters
parser.add_argument("num_samples_per_cleft", type=int)
parser.add_argument("dil_param", type=int)
parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
parser.add_argument("--chunk_end", nargs="+", type=int, required=True)
parser.add_argument("--patchsz", nargs="+", type=int, required=True)
parser.add_argument("--parallel", type=int, default=1)
parser.add_argument("--mip", nargs="+", type=int, default=(0,))
parser.add_argument("--img_mip", nargs="+", type=int, default=None)
parser.add_argument("--seg_mip", nargs="+", type=int, default=None)
parser.add_argument("--mip0_begin", nargs="+", type=int, default=None)
parser.add_argument("--mip0_end", nargs="+", type=int, default=None)


# MIP arguments can specify voxel resolutions or mip index
def mip_or_res(x): return x[0] if (x is not None and len(x) == 1) else x


args = parser.parse_args()
args.mip = mip_or_res(args.mip)
args.img_mip = mip_or_res(args.img_mip)
args.seg_mip = mip_or_res(args.seg_mip)
print(vars(args))


s.proc_tasks.tasks_w_io.chunk_edges_task(**vars(args))
