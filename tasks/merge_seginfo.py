"""
Segment Info Merging Wrapper Script

-Takes an id mapping across segments as input
-Merges the segment info dataframes into one for the entire dataset
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_url")
parser.add_argument("hashval", type=int)


args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.merge_seginfo_task(**vars(args))
