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
    conf["tempoutput"] = parser.get("Volumes", "tempoutput")
    conf["output"] = parser.get("Volumes", "output")
    conf["baseseg"] = parser.get("Volumes", "baseseg")
    conf["image"] = parser.get("Volumes", "image")

    conf["voxelres"] = parse_tuple(parser.get("Dimensions", "voxelres"))
    conf["startcoord"] = parse_tuple(parser.get("Dimensions", "startcoord"))
    conf["volshape"] = parse_tuple(parser.get("Dimensions", "volshape"))
    conf["chunkshape"] = parse_tuple(parser.get("Dimensions", "chunkshape"))
    conf["blockshape"] = parse_tuple(parser.get("Dimensions", "blockshape"))
    conf["patchshape"] = parse_tuple(parser.get("Dimensions", "patchshape"))
    # Additional field inferred from chunk_shape
    conf["maxfaceshape"] = infer_max_face_shape(conf["chunkshape"])

    conf["ccthresh"] = parser.getfloat("Parameters", "ccthresh")
    conf["szthresh"] = parser.getint("Parameters", "szthresh")
    conf["dustthresh"] = parser.getint("Parameters", "dustthresh")
    conf["mergethresh"] = parser.getint("Parameters", "mergethresh")
    conf["nummergetasks"] = parser.getint("Parameters", "nummergetasks")

    conf["workflowtype"] = parser.get("Workflow", "workflowtype")
    conf["workspacetype"] = parser.get("Workflow", "workspacetype")
    conf["queueurl"] = parser.get("Workflow", "queueurl")
    conf["connectionstr"] = parser.get("Workflow", "connectionstr")
    conf["storagedir"] = parser.get("Workflow", "storagedir")
    conf["normcloudpath"] = parser.get("Workflow", "normcloudpath")
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
        storagestr = parser.get("Workflow", "connectionstr")

    elif workspacetype == "File":
        storagestr = parser.get("Workflow", "storagedir")

    aux_storagestr = parser.get("Workflow", "storagedir")

    return storagestr, aux_storagestr
