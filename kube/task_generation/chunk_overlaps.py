import argparse

from cloudvolume.lib import Bbox, Vec
from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    startcoord = Vec(*config["startcoord"])
    volshape = Vec(*config["volshape"])

    bounds = Bbox(startcoord, startcoord + volshape)

    iterator = tc.create_overlap_tasks(
                   config["output"], config["baseseg"],
                   config["storagestrs"][0],
                   bounds=bounds, shape=config["chunkshape"],
                   mip=config["voxelres"])

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
