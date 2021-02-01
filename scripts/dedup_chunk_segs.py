"""
Removing any duplicate entries from chunk_segs

- Some cloud processing can allow for duplicate tasks to run, which
  can cause problems for our merging scheme. This removes duplicates from
  the database
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()


parser.add_argument("storagestr")


args = parser.parse_args()
args.storagestr = s.io.parse_storagestr(args.storagestr)
print(vars(args))


s.proc.io.dedup_chunk_segs(**vars(args))
