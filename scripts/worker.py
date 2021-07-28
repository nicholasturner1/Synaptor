import argparse
from taskqueue import TaskQueue

import synaptor.cloud.kube.synaptortask  # triggers registration of SynaptorTask

parser = argparse.ArgumentParser()

parser.add_argument("qurl", type=str)
parser.add_argument("lease_seconds", type=int, default=300)

args = parser.parse_args()
with TaskQueue(qurl=args.qurl, n_threads=0) as tq:
    tq.poll(lease_seconds=args.lease_seconds)
