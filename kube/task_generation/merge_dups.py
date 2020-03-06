import argparse

from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    iterator = tc.create_merge_dup_tasks(
                   config["storagestrs"][0], config["num_merge_tasks"],
                   config["mergethresh"], config["szthresh"],
                   config["voxelres"], config["storagestrs"][1]
                   )

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
