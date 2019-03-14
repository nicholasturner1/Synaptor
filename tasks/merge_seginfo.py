"""
Segment Info Merging Wrapper Script

- Takes an id mapping across segments as input
- Merges the segment info dataframes into one for the entire dataset
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_url")
parser.add_argument("hashval", type=int)

parser.add_argument("--timing_tag", default=None)


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.proc.tasks_w_io.merge_seginfo_task(**vars(args))
