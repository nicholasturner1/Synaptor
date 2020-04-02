import argparse

from taskqueue import TaskQueue

import synaptor.cloud.kube.parser as parser
import synaptor.cloud.kube.task_creation as tc


def main(configfilename):

    config = parser.parse(configfilename)

    task = tc.create_cloudvols(
               config["output"], config["tempoutput"],
               config["voxelres"], config["volshape"],
               config["startcoord"], config["blockshape"])


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()

    argparser.add_argument("configfilename")

    args = argparser.parse_args()

    main(args.configfilename)
