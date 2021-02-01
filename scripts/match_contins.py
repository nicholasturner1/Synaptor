"""
Match Continuations Wrapper Script

- Finds which continuations match across chunks
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")
parser.add_argument("storagedir")
parser.add_argument("facehash", type=int)

# Processing Parameters
parser.add_argument("--max_face_shape", type=int,
                    nargs=2, default=(1024, 1024))
parser.add_argument("--timing_tag", default=None)

args = parser.parse_args()
args.storagestr = s.io.parse_storagestr(args.storagestr)
print(vars(args))


s.proc.tasks_w_io.match_continuations_task(**vars(args))
