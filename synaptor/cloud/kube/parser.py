import configparser


SUPPORTED_WORKFLOWS = ["Segmentation", "Segmentation+Assignment"]
SUPPORTED_WORKSPACES = ["Database", "File"]


def parse(filename):
    """Parses a configuration file."""

    parser = configparser.ConfigParser()
    parser.read(filename)

    assert parser.get("Workflow", "workflowtype") in SUPPORTED_WORKFLOWS
    assert parser.get("Workflow", "workspacetype") in SUPPORTED_WORKSPACES

    conf = dict()

    conf["descriptor"] = parser.get("Volumes", "descriptor")
    conf["output"] = parser.get("Volumes", "output")
    conf["tempoutput"] = parser.get("Volumes", "tempoutput",
                                    fallback=conf["output"])
    conf["baseseg"] = parser.get("Volumes", "baseseg", fallback=None)
    conf["image"] = parser.get("Volumes", "image", fallback=None)

    conf["voxelres"] = parse_tuple(parser.get("Dimensions", "voxelres"))
    conf["startcoord"] = parse_tuple(parser.get("Dimensions", "startcoord"))
    conf["volshape"] = parse_tuple(parser.get("Dimensions", "volshape"))
    conf["chunkshape"] = parse_tuple(parser.get("Dimensions", "chunkshape"))
    conf["blockshape"] = parse_tuple(parser.get("Dimensions", "blockshape",
                                                fallback="1, 1, 1"))
    conf["patchshape"] = parse_tuple(parser.get("Dimensions", "patchshape",
                                                fallback="1, 1, 1"))

    # Additional field inferred from chunk_shape
    conf["maxfaceshape"] = infer_max_face_shape(conf["chunkshape"])
    check_shapes(conf["volshape"], conf["chunkshape"], conf["blockshape"])

    conf["ccthresh"] = parser.getfloat("Parameters", "ccthresh")
    conf["szthresh"] = parser.getint(
                           "Parameters", "szthresh", fallback=0)
    conf["dustthresh"] = parser.getint(
                             "Parameters", "dustthresh", fallback=0)
    conf["mergethresh"] = parser.getint(
                              "Parameters", "mergethresh", fallback=0)
    conf["nummergetasks"] = parser.getint(
                                "Parameters", "nummergetasks", fallback=1)

    conf["workflowtype"] = parser.get(
                               "Workflow", "workflowtype", fallback="Segmentation")
    conf["workspacetype"] = parser.get(
                                "Workflow", "workspacetype", fallback="File")
    conf["queueurl"] = parser.get("Workflow", "queueurl", fallback=None)
    conf["connectionstr"] = parser.get(
                                "Workflow", "connectionstr",
                                fallback="STORAGE_FROM_FILE")
    conf["storagedir"] = parser.get("Workflow", "storagedir")
    conf["normcloudpath"] = parser.get(
                                "Workflow", "normcloudpath", fallback=None)
    conf["storagestrs"] = get_storagestrs(parser)

    return conf


def parse_tuple(field):
    return tuple(map(int, field.split(",")))


def infer_max_face_shape(chunk_shape):
    return tuple(sorted(chunk_shape)[1:])


def get_storagestrs(parser):
    """ Extracts the storage strings depending upon the workspace type. """
    workspacetype = parser.get("Workflow", "workspacetype")

    if workspacetype == "Database":
        storagestr = parser.get(
                         "Workflow", "connectionstr",
                         fallback="STORAGE_FROM_FILE")

    elif workspacetype == "File":
        storagestr = parser.get("Workflow", "storagedir")

    aux_storagestr = parser.get("Workflow", "storagedir")

    return storagestr, aux_storagestr


def check_shapes(volshape, chunkshape, blockshape):
    if not all(v % b == 0 for (v, b) in zip(volshape, blockshape)):
        raise Exception("volshape not evenly divided by blockshape")
    if not all(c % b == 0 for (c, b) in zip(chunkshape, blockshape)):
        raise Exception("chunkshape not evenly divided by blockshape")
