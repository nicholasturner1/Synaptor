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

    iterator = tc.create_connected_component_tasks(
                   config["descriptor"], config["tempoutput"],
                   storagestr=config["storagestrs"][0],
                   storagedir=config["storagestrs"][1],
                   cc_thresh=config["ccthresh"], sz_thresh=config["dustthresh"],
                   bounds=bounds, shape=config["chunkshape"],
                   mip=config["voxelres"], hashmax=config["nummergetasks"])

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
