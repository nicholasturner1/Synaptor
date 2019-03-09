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
print(vars(args))


s.proc_tasks.tasks_w_io.seg_graph_cc_task(**vars(args))
