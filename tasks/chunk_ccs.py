#!/usr/bin/env python3
__doc__ = """
Chunkwise Connected Components Wrapper Script

- Performs connected components over a chunk of data
- Extracts clefts that possibly continue to the next chunk (continuations)
- Filters out any complete segments under the size threshold
- Records the centroid, size, and bounding box for the surviving
  clefts in a DataFrame
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Input & Outputs
parser.add_argument("output_cvname")
parser.add_argument("cleft_cvname")
parser.add_argument("proc_dir_path")

# Processing Parameters
parser.add_argument("--chunk_begin", nargs="+", type=int, required=True)
parser.add_argument("--chunk_end", nargs="+", type=int, required=True)
parser.add_argument("cc_thresh", type=float)
parser.add_argument("sz_thresh", type=int)

args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.chunk_ccs_task(**vars(args))
