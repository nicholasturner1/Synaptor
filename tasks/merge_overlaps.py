#!/usr/bin/env python3
__doc__ = """
Merge Edges Wrapper Script

Merges overlap matrices together

Writes the segments of max overlap
"""
import synaptor as s

import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_dir_path")

# Processing Parameters
args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.merge_overlaps_task(**vars(args))
