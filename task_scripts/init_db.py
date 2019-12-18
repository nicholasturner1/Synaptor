"""
Initializes a database with the proper tables, etc.
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()


parser.add_argument("storagestr")


args = parser.parse_args()
args.storagestr = s.io.parse_storagestr(args.storagestr)
print(vars(args))


s.proc.io.initdb.drop_db(args.storagestr)
s.proc.io.initdb.init_db(args.storagestr)
