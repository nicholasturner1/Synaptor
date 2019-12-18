#!/usr/bin/env python3
__doc__ = """
Merge Edges Wrapper Script

Takes assignments from multiple chunks, and selects the one from the
chunk containing the largest number of that cleft's voxels.
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")

parser.add_argument("--timing_tag", default=None)

args = parser.parse_args()
print(vars(args))

if s.io.is_db_url(args.storagestr):
    s.proc.tasks_w_io.consolidate_edges_db_task(**vars(args))
else:
    s.proc.tasks_w_io.consolidate_edges_task(**vars(args))
