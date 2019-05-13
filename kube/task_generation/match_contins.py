import argparse

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    iterator = tc.create_match_contins_tasks(
                   config["storagestrs"][0], config["num_merge_jobs"],
                   max_faceshape=config["max_face_shape"])

    tq = TaskQueue(config["queueurl"])
    tq.insert_all(tasks)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
