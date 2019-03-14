"""
Merge Duplicates Wrapper Script

- Merges assigned clefts together which connect the same partners within
  some distance threshold. Also filters all resulting entries by a high-pass
  size threshold.
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_url")
parser.add_argument("hash_index", type=int)

# Processing Parameters
parser.add_argument("dist_thr", type=int)
parser.add_argument("size_thr", type=int)
parser.add_argument("--voxel_res", nargs="+", type=int)
parser.add_argument("--timing_tag", default=None)


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.proc.tasks_w_io.merge_duplicates_task(**vars(args))
