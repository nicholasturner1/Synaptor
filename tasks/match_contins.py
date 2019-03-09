"""
Match Continuations Wrapper Script

- Finds which continuations match across chunks
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("proc_url")
parser.add_argument("facehash", type=int)

# Processing Parameters
parser.add_argument("--max_face_shape", type=int,
                    nargs=2, default=(1024, 1024))

args = parser.parse_args()
print(vars(args))


s.proc.tasks_w_io.match_continuations_task(**vars(args))
