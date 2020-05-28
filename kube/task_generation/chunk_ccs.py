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

    iterator = tc.create_connected_component_tasks(
                   config["descriptor"], config["tempoutput"],
                   storagestr=config["storagestrs"][0],
                   storagedir=config["storagestrs"][1],
                   ccthresh=config["ccthresh"],
                   szthresh=config["dustthresh"],
                   volshape=config["volshape"],
                   chunkshape=config["chunkshape"],
                   startcoord=config["startcoord"],
                   resolution=config["voxelres"],
                   hashmax=config["nummergetasks"],
                   bboxes=bboxes)

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")
    argparser.add_argument("--tagfilename", default=None)

    args = argparser.parse_args()

    main(args.configfilename, args.tagfilename)
