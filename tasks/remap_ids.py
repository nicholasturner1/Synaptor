#!/usr/bin/env python3
__doc__ = """
Remap IDs

-Read connected components for a chunk
-Read id mapping for the same chunk
-Apply the id mapping
-Write the new chunk
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("cleft_in_cvname")
parser.add_argument("cleft_out_cvname")
parser.add_argument("proc_dir_path")

# Processing Parameters
parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
parser.add_argument("--chunk_end", nargs="+", type=int, required=True)

args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.remap_ids_task(**vars(args))
