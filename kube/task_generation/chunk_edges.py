import argparse

from cloudvolume.lib import Bbox, Vec
from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    startcoord = Vec(*config["startcoord"])
    volshape = Vec(*config["vol_shape"])

    bounds = Bbox(startcoord, startcoord + volshape)

    iterator = tc.create_chunk_edges_tasks(
                   config["image"], config["temp_output"],
                   config["base_seg"], storagestr=config["storagestrs"][0],
                   hashmax=config["num_merge_tasks"],
                   storagedir=config["storagestrs"][1],
                   bounds=bounds, chunkshape=config["chunk_shape"],
                   patchsz=config["patch_shape"],
                   resolution=config["voxelres"])

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
