"""
Pick Largest Edge Wrapper Script

- Takes edge assignments from multiple chunks, and selects the one from the
  chunk containing the largest number of each cleft's voxels.
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_url")
parser.add_argument("clefthash", type=int)


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.proc.tasks_w_io.pick_largest_edges_task(**vars(args))
