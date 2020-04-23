import argparse

from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    enforce_szthresh = config["workflowtype"] == "Segmentation"
    szthresh = config["szthresh"] if enforce_szthresh else None

    iterator = tc.create_merge_seginfo_tasks(
                   config["storagestrs"][0], config["nummergetasks"],
                   aux_storagestr=config["storagestrs"][1],
                   szthresh=szthresh)

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(iterator)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
