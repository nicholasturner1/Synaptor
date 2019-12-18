"""
Connected Component Consolidation Wrapper Script

-Assigns a global set of cleft segment ids
-Finds which continuations match across chunks
-Makes an id mapping that merges the matching continuations for each chunk
-Merges the cleft info dataframes into one for the entire dataset
-Maps any newly merged cleft segments to 0 if they're under the
 size threshold
"""
import synaptor as s

import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")

# Processing Parameters
parser.add_argument("size_thr", type=int)
parser.add_argument("--max_face_shape", type=int,
                    nargs="+", default=(1024, 1024))
parser.add_argument("--timing_tag", default=None)

args = parser.parse_args()
print(vars(args))


s.proc_tasks.tasks_w_io.merge_ccs_task(**vars(args))
