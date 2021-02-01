"""
Create an index on a single database column
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()

# Inputs & Outputs
parser.add_argument("storagestr")
parser.add_argument("tablename")
parser.add_argument("colname")


args = parser.parse_args()
args.storagestr = s.io.parse_storagestr(args.storagestr)
print(vars(args))


s.io.create_index(args.storagestr, args.tablename, args.colname)
