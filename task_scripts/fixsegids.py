"""
Fix Segment IDs wrapper script
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")

# Processing Parameters
parser.add_argument("--chunk_begin", nargs=3, type=int, required=True)
parser.add_argument("--chunk_end", nargs=3, type=int, required=True)

parser.add_argument("--aggscratchpath", default=None)
parser.add_argument("--aggchunksize", nargs=3, type=int, default=None)
parser.add_argument("--aggstartcoord", nargs=3, type=int, default=None)
parser.add_argument("--aggmaxmip", type=int, default=None)

args = parser.parse_args()
args.storagestr = s.io.parse_storagestr(args.storagestr)
print(vars(args))


s.proc.tasks_w_io.fixsegids_task(**vars(args))
