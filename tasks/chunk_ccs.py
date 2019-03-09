"""
Chunkwise Connected Components Wrapper Script

- Performs connected components over a chunk of data
- Extracts clefts that possibly continue to the next chunk (continuations)
- Filters out any complete segments under the size threshold
- Records the centroid, size, and bounding box for the surviving
  segments in the database (depending on proc_url)
- Records the continuation information in files under proc_dir
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Input & Outputs
parser.add_argument("desc_cvname")
parser.add_argument("seg_cvname")
parser.add_argument("proc_url")
parser.add_argument("--proc_dir", default=None, help="file storage dir")

# Processing Parameters
parser.add_argument("cc_thresh", type=float)
parser.add_argument("sz_thresh", type=int)
parser.add_argument("--chunk_begin", nargs=3, type=int, required=True)
parser.add_argument("--chunk_end", nargs=3, type=int, required=True)
parser.add_argument("--parallel", type=int, default=1)
parser.add_argument("--mip", nargs="+", type=int, default=(0,))
parser.add_argument("--hashmax", type=int, default=1)


# MIP arguments can specify voxel resolutions or mip index
def mip_or_res(x): return x[0] if (x is not None and len(x) == 1) else x


args = parser.parse_args()
args.mip = mip_or_res(args.mip)
print(vars(args))


s.proc_tasks.tasks_w_io.cc_task(**vars(args))
