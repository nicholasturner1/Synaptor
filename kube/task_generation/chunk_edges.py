import argparse

from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc
from synaptor import io


def main(configfilename, tagfilename=None):

    config = parser.parse(configfilename)

    if tagfilename is not None:
        bboxes = io.utils.read_bbox_tag_filename(tagfilename)
    else:
        bboxes = None

    iterator = tc.create_chunk_edges_tasks(
                   config["image"], config["tempoutput"], config["baseseg"],
                   storagestr=config["storagestrs"][0],
                   hashmax=config["nummergetasks"],
                   storagedir=config["storagestrs"][1],
                   volshape=config["volshape"],
                   chunkshape=config["chunkshape"],
                   startcoord=config["startcoord"],
                   patchsz=config["patchshape"],
                   normcloudpath=config["normcloudpath"],
                   resolution=config["voxelres"],
                   bboxes=bboxes)

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")
    argparser.add_argument("--tagfilename", default=None)

    args = argparser.parse_args()

    main(**vars(args))
