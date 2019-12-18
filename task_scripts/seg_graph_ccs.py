"""
Segmentation Continuation Graph Components Wrapper Script

- Takes a graph of continuation edges as input
- Makes an id mapping that merges the connected continuations using global ids
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("stroagestr")
parser.add_argument("hashmax", type=int)

parser.add_argument("--timing_tag", default=None)


args = parser.parse_args()
args.stroagestr = s.io.parse_stroagestr(args.stroagestr)
print(vars(args))


s.proc.tasks_w_io.seg_graph_cc_task(**vars(args))
