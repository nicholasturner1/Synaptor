#!/usr/bin/env python3
__doc__ = """
Cleft ID mapping IO for processing tasks
"""

from ... import io


ID_MAP_DIRNAME = "id_maps"
ID_MAP_FMTSTR = "id_map_{tag}.df"


def read_chunk_id_map(proc_dir_path, chunk_bounds):
    """Reads an id mapping for a chunk from a processing directory"""
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    basename = ID_MAP_FMTSTR.format(tag=chunk_tag)
    fname = io.pull_file(os.path.join(proc_dir_path, ID_MAP_DIRNAME, basename))

    df = io.read_dframe(fname)

    return dict(zip(df.index, df.new_id))


#NOTE: why does this take a fname directly?
def write_chunk_id_map(id_map, fname):
    """Writes an id mapping for a chunk to a processing directory"""
    df = pd.DataFrame(pd.Series(id_map), columns=["new_id"])
    io.write_dframe(df, fname)


def write_chunk_id_maps(chunk_id_maps, chunk_bounds, proc_dir_path):
    """
    Writes all of the id mappings for each chunk to a subdirectory
    of a processing directory
    """
    if not os.path.exists(ID_MAP_DIRNAME):
        os.makedirs(ID_MAP_DIRNAME)

    for (id_map, bounds) in zip(chunk_id_maps.flat, chunk_bounds):

        chunk_tag = io.fname_chunk_tag(bounds)
        fname = os.path.join(ID_MAP_DIRNAME,
                             ID_MAP_FMTSTR.format(tag=chunk_tag))
        write_chunk_id_map(id_map, fname)

    io.send_directory(ID_MAP_DIRNAME, proc_dir_path)


def read_dup_id_map(proc_dir_path):
    df = io.read_dframe(proc_dir_path, "dup_id_map.df")
    return dict(zip(df.index, df.new_id))


def write_dup_id_map(id_map, proc_dir_path):

    df = pd.DataFrame(pd.Series(id_map), columns=["new_id"])
    io.write_dframe(df, proc_dir_path, "dup_id_map.df")
