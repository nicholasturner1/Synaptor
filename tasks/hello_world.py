import argparse
from time import sleep

parser = argparse.ArgumentParser()

parser.add_argument("proc_url")
parser.add_argument("message")
parser.add_argument("sleep", type=float, default=0.0)

args = parser.parse_args()
print("Sleeping for {} s".format(args.sleep), flush=True)
sleep(args.sleep)
print("Hello world: {}".format(args.message), flush=True)
