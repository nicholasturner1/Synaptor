"""
Removing any duplicate entries from chunk_segs

- Some cloud processing can allow for duplicate tasks to run, which
  can cause problems for our merging scheme. This removes duplicates from
  the database
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()


parser.add_argument("proc_url")


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.proc.io.dedup_chunk_segs(**vars(args))
