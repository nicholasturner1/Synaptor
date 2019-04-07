"""
Initializes a database with the proper tables, etc.
"""
import synaptor as s


import argparse
parser = argparse.ArgumentParser()


parser.add_argument("proc_url")


args = parser.parse_args()
args.proc_url = s.io.parse_proc_url(args.proc_url)
print(vars(args))


s.proc.io.initdb.drop_db(**vars(args))
s.proc.io.initdb.init_db(**vars(args))
