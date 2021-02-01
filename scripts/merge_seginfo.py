"""
Segment Info Merging Wrapper Script

- Takes an id mapping across segments as input
- Merges the segment info dataframes into one for the entire dataset
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")
parser.add_argument("hashval", type=int)

parser.add_argument("--aux_storagestr", default=None)
parser.add_argument("--timing_tag", default=None)
parser.add_argument("--szthresh", type=int, default=None)


args = parser.parse_args()
args.storagestr = s.io.parse_storagestr(args.storagestr)
args.aux_storagestr = s.io.parse_storagestr(args.aux_storagestr)
print(vars(args))


s.proc.tasks_w_io.merge_seginfo_task(**vars(args))
