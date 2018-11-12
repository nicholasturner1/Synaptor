#!/usr/bin/env python3
__doc__ = """
Merge Edges Wrapper Script

-Maps together any edges that connect the same partners
 and are within some distance apart
-Maps any newly merged cleft segments to 0 if they're under the
 size threshold
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_dir_path")

# Processing Parameters
parser.add_argument("dist_thr", type=int)
parser.add_argument("size_thr", type=int)
parser.add_argument("--voxel_res", nargs="+", type=int)


args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.merge_edges_task(**vars(args))
