"""
Chunk Segmentation Merging Map Wrapper Script

- Takes the resulting id map from seg_graph_ccs as input
- Makes an id mapping that merges the matching continuations within each chunk
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()


parser.add_argument("proc_url")

parser.add_argument("--timing_tag", default=None)


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.proc.tasks_w_io.chunk_seg_merge_map(**vars(args))
