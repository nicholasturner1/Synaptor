"""
Merge Edges Wrapper Script

Merges overlap matrices together

Writes the segments of max overlap
"""
import synaptor as s

import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")

parser.add_argument("--timing_tag", default=None)


args = parser.parse_args()
print(vars(args))


s.proc.tasks_w_io.merge_overlaps_task(**vars(args))
