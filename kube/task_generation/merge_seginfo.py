import argparse

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    iterator = tc.create_merge_seginfo_tasks(
                   config["storagestrs"][0], config["num_merge_jobs"],
                   aux_storagestr=config["storagestrs"][1])

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(tasks)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
