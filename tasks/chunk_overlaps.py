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
parser.add_argument("--mip", type=int, default=0)

args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.chunk_overlaps_task(**vars(args))
