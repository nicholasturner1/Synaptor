import argparse

from cloudvolume.lib import Bbox, Vec

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    startcoord = Vec(config["startcoord"])
    volshape = Vec(config["vol_shape"])

    bounds = Bbox(startcoord, startcoord + volshape)

    iterator = tc.create_remap_tasks(
                   config["temp_output"], config["output"],
                   storagestr=config["storagestrs"][0],
                   bounds=bounds, shape=config["chunk_shape"],
                   resolution=config["voxelres"])

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(tasks)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
