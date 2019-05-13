import configparser


def parse(filename):
    """ Parses a configuration file. """

    parser = configparser.ConfigParser()
    parser.read(filename)

    assert parser.get("Workspaces", "workspacetype") in ["Database", "File"]

    conf = dict()

    conf["descriptor"] = parser.get("Volumes", "descriptor")
    conf["temp_output"] = parser.get("Volumes", "temp_output")
    conf["output"] = parser.get("Volumes", "output")

    conf["voxelres"] = parse_tuple(parser.get("Dimensions", "voxelres"))
    conf["startcoord"] = parse_tuple(parser.get("Dimensions", "startcoord"))
    conf["vol_shape"] = parse_tuple(parser.get("Dimensions", "vol_shape"))
    conf["chunk_shape"] = parse_tuple(parser.get("Dimensions", "chunk_shape"))
    # Additional field inferred from chunk_shape
    conf["max_face_shape"] = infer_max_face_shape(conf["chunk_shape"])

    conf["ccthresh"] = parser.getfloat("Parameters", "ccthresh")
    conf["szthresh"] = parser.getint("Parameters", "szthresh")
    conf["dustthresh"] = parser.getint("Parameters", "dustthresh")
    conf["num_merge_tasks"] = parser.getint("Parameters", "num_merge_tasks")

    conf["workspacetype"] = parser.get("Workspaces", "workspacetype")
    conf["queueurl"] = parser.get("Workspaces", "queueurl")
    conf["connectionstr"] = parser.get("Workspaces", "connectionstr")
    conf["storagedir"] = parser.get("Workspaces", "storagedir")
    conf["storagestrs"] = get_storagestrs(parser)

    return conf


def parse_tuple(field):
    return tuple(map(int, field.split(",")))


def infer_max_face_shape(chunk_shape):
    return tuple(sorted(chunk_shape)[:2])


def get_storagestrs(parser):
    """ Extracts the storage strings depending upon the workspace type. """
    workspacetype = parser.get("Workspaces", "workspacetype")

    if workspacetype == "Database":
        storagestr = parser.get("Workspaces", "connectionstr")

    elif workspacetype == "File":
        storagestr = parser.get("Workspaces", "storagedir")

    aux_storagestr = parser.get("Workspaces", "storagedir")

    return storagestr, aux_storagestr
