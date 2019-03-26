"""
Create an index on a single database column

- Takes a graph of continuation edges as input
- Makes an id mapping that merges the connected continuations using global ids
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("url")
parser.add_argument("tablename", type=int)
parser.add_argument("colname", type=int)


args = parser.parse_args()
args.url = s.io.parse_proc_url(args.url)
print(vars(args))


s.io.create_index(**vars(args))
