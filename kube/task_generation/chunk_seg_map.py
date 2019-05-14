import argparse

from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    task = tc.create_chunk_seg_map_task(config["storagestrs"][0])

    print(task)
    print(config["storagestrs"][0])
    tq = TaskQueue(config["queueurl"])
    tq.insert_all([task])


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
