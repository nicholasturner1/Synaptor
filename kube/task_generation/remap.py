import argparse

from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    iterator = tc.create_remap_tasks(
                   config["tempoutput"], config["output"],
                   storagestr=config["storagestrs"][0],
                   volshape=config["volshape"],
                   chunkshape=config["chunkshape"],
                   startcoord=config["startcoord"],
                   dupstoragestr=config["storagestrs"][1],
                   resolution=config["voxelres"])

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
