"""
Segmentation Continuation Graph Components Wrapper Script

- Takes a graph of continuation edges as input
- Makes an id mapping that merges the matching continuations for each chunk
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_url")
parser.add_argument("hashmax", type=int)


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.proc.tasks_w_io.seg_graph_cc_task(**vars(args))
