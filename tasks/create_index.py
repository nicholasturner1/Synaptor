"""
Create an index on a single database column

- Takes a graph of continuation edges as input
- Makes an id mapping that merges the connected continuations using global ids
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_url")
parser.add_argument("tablename")
parser.add_argument("colname")


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.io.create_index(args.proc_url, args.tablename, args.colname)
