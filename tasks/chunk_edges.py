"""
Chunk Edges Wrapper Script

- Applies an id map to a chunk (if passed)
NOTE: Modifies the clefts array if id_map exists
- Applies an assignment network to each cleft in the chunk
- Computes the size of each cleft to assist later thresholding
- Stores all of the computed information in the Database
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("img_cvname")
parser.add_argument("cleft_cvname")
parser.add_argument("seg_cvname")
parser.add_argument("proc_dir_path")
parser.add_argument("hashmax", type=int, default=1)
parser.add_argument("--proc_dir", default=None)
parser.add_argument("--root_seg_cvname", default=None)

# Processing Parameters
parser.add_argument("num_samples_per_cleft", type=int)
parser.add_argument("dil_param", type=int)
parser.add_argument("--chunk_begin", nargs=3, type=int, required=True)
parser.add_argument("--chunk_end", nargs=3, type=int, required=True)
parser.add_argument("--patchsz", nargs=3, type=int, required=True)
parser.add_argument("--resolution", nargs=3, type=int, default=(4, 4, 40))
parser.add_argument("--num_downsamples", type=int, default=0)
parser.add_argument("--base_res_begin", nargs=3, type=int, default=None)
parser.add_argument("--base_res_end", nargs=3, type=int, default=None)
parser.add_argument("--parallel", type=int, default=1)


args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.edge_task(**vars(args))
