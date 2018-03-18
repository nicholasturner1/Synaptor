#!/usr/bin/env python3
__doc__ = """
Connected Component Consolidation Wrapper Script

-Assigns a global set of cleft segment ids
-Finds which continuations match across chunks
-Makes an id mapping that merges the matching continuations for each chunk
-Merges the cleft info dataframes into one for the entire dataset
-Maps any newly merged cleft segments to 0 if they're under the
 size threshold
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_dir_path")

# Processing Parameters
parser.add_argument("size_thr", type=int)

args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.merge_ccs_task(**vars(args))
