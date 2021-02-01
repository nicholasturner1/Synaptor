"""
Pick Largest Edge Wrapper Script

- Takes edge assignments from multiple chunks, and selects the one from the
  chunk containing the largest number of each cleft's voxels.
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")
parser.add_argument("clefthash", type=int)

parser.add_argument("--timing_tag", default=None)


args = parser.parse_args()
args.storagestr = s.io.parse_storagestr(args.storagestr)
print(vars(args))


s.proc.tasks_w_io.pick_largest_edges_task(**vars(args))
