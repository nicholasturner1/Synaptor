"""
Remap IDs Wrapper Script

- Read connected components for a chunk
- Read id mapping for the same chunk (including duplicate id map if it exists)
- Apply the id mapping
- Write the new chunk
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("seg_in_cvname")
parser.add_argument("seg_out_cvname")
parser.add_argument("storagestr")

# Processing Parameters
parser.add_argument("--chunk_begin", nargs=3, type=int, required=True)
parser.add_argument("--chunk_end", nargs=3, type=int, required=True)
parser.add_argument("--parallel", type=int, default=1)
parser.add_argument("--mip", nargs="+", type=int, default=(0,))
parser.add_argument("--timing_tag", default=None)
parser.add_argument("--dup_map_storagestr", default=None)


# MIP arguments can specify voxel resolutions or mip index
def mip_or_res(x): return x[0] if (x is not None and len(x) == 1) else x


args = parser.parse_args()
args.mip = mip_or_res(args.mip)
args.storagestr = s.io.parse_storagestr(args.storagestr)
if args.dup_map_storagestr is not None:
    args.dup_map_storagestr = s.io.parse_storagestr(args.dup_map_storagestr)
print(vars(args))


s.proc.tasks_w_io.remap_ids_task(**vars(args))
