""" Cleft continuation IO for processing tasks """

import os
import re

import h5py
import pandas as pd
from sqlalchemy import select

from ... import io
from ..seg.continuation import Continuation, Face, ContinFile
from .. import colnames as cn
from . import filenames as fn


FACE_REGEXP = re.compile("f[0-2]_(hi|lo)")
CONTINUATION_FILE_COLUMNS = [cn.contin_filename, cn.facehash]
CONTIN_GRAPH_COLUMNS = [cn.graph_id1, cn.graph_id2]
TABLENAME = "continuations"


def fname_face_tag(face):
    hi_str = "hi" if face.hi_index else "lo"

    return f"f{face.axis}_{hi_str}"


def face_from_tag(tag):
    axis = int(tag[1])
    hi_index = tag[-2:] == "hi"

    return Face(axis, hi_index)


def face_from_filename(fname):
    match = FACE_REGEXP.search(fname)
    assert match is not None, f"face not found in fname: {fname}"

    return face_from_tag(match.group(0))


def face_filename(proc_url, chunk_bounds, face, local=False):
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    face_tag = fname_face_tag(face)
    basename = fn.contin_fmtstr.format(chunk_tag=chunk_tag, face_tag=face_tag)

    if local:
        return os.path.join(proc_url, basename)
    else:
        return os.path.join(proc_url, fn.contin_dirname, basename)


def _read_face_file(fname):

    continuations = list()

    with h5py.File(fname) as f:
        face_index = f["face_axis"][()]
        face_hi = f["hi_face"][()]

        face = Face(face_index, face_hi)
        continuation_ids = f["face_coords"].keys()

        for segid in continuation_ids:
            coords = f[f"face_coords/{segid}"][()]
            new_continuation = Continuation(int(segid), face, coords)
            continuations.append(new_continuation)

    return continuations


def _read_legacy_file(fname):

    continuations = dict()

    with h5py.File(fname) as f:
        for face in Face.all_faces():
            axis = face.axis
            hi_index = "high" if face.hi_index else "low"

            face_continuations = list()
            face_str = f"{axis}/{hi_index}"
            if face_str in f:
                for i in f[f"{axis}/{hi_index}"].keys():
                    coords = f[f"{axis}/{hi_index}/{i}"][()]
                    face_continuations.append(
                        Continuation(int(i), face, coords))

            continuations[face] = face_continuations

    return continuations


def _write_face_file(face_continuations, fname, face=None):
    """
    Given a concrete local path, writes an hdf5 file describing each
    continuation within a list. Each continuation within the list is assumed
    to originate from the same face of a given chunk.
    """

    if face is None:
        if len(face_continuations) == 0:
            raise(Exception("Need a face argument or continuations"
                            " to determine face info for file"))

        face = face_continuations[0].face

    if os.path.exists(fname):
        os.remove(fname)

    with h5py.File(fname) as f:
        f.create_dataset("face_axis", data=face.axis)
        f.create_dataset("hi_face", data=face.hi_index)
        coord_group = f.create_group("face_coords")

        for continuation in face_continuations:
            coord_group.create_dataset(f"{continuation.segid}",
                                       data=continuation.face_coords)


def read_face_continuations(proc_url, chunk_bounds, face):
    """ Reads the continuations for a single face """
    assert not io.is_db_url(proc_url), "Continuation IO not impl for dbs"
    local_fname = io.pull_file(face_filename(proc_url, chunk_bounds, face))

    return _read_face_file(local_fname)


def read_face_filenames(filenames):
    """
    Reads continuations for a set of face files by pulling the
    files from storage directly.
    """
    local_filenames = io.pull_files(filenames)
    return list(map(_read_face_file, local_filenames))


def write_face_continuations(continuations, proc_url, chunk_bounds, face):
    assert not io.is_db_url(proc_url), "Continuation IO not impl for dbs"
    local_fname = face_filename("", chunk_bounds, face, local=True)
    dst_fname = face_filename(proc_url, chunk_bounds, face, local=False)

    _write_face_file(continuations, local_fname, face)
    io.send_file(local_fname, dst_fname)


def read_chunk_continuations(proc_url, chunk_bounds):
    assert not io.is_db_url(proc_url), "Continuation IO not impl for dbs"
    cloud_fnames = list(face_filename(proc_url, chunk_bounds, face)
                        for face in Face.all_faces())

    local_fnames = io.pull_files(cloud_fnames)

    continuations = dict()
    for fname in local_fnames:
        face = face_from_filename(fname)
        continuations[face] = _read_face_file(fname)

    return continuations


def continuations_by_hash(proc_url, hashval):
    """ Reads the set of continuation files hashed to a particular value. """
    assert io.is_db_url(proc_url), "not impl for files"

    metadata = io.open_db_metadata(proc_url)
    continuations = metadata.tables["continuations"]
    columns = [continuations.c[name] for name in CONTINUATION_FILE_COLUMNS]

    statement = select(columns).where(continuations.c[cn.facehash] == hashval)

    dframe = io.read_db_dframe(proc_url, statement)

    filenames = list(dframe[cn.contin_filename])

    local_filenames = io.pull_files(filenames)
    bboxes = [io.bbox_from_fname(fname) for fname in filenames]
    faces = [face_from_filename(fname) for fname in filenames]

    return list(ContinFile(fname, bbox, face)
                for (fname, bbox, face) in zip(local_filenames, bboxes, faces))


def write_chunk_continuations(continuations, proc_url, chunk_bounds):
    assert not io.is_db_url(proc_url), "Continuation IO not impl for dbs"
    local_fnames = list(face_filename("./", chunk_bounds, face, local=True)
                        for face in Face.all_faces())

    for (face, fname) in zip(Face.all_faces(), local_fnames):
        _write_face_file(continuations[face], fname, face)

    io.send_files(local_fnames, os.path.join(proc_url, fn.contin_dirname))


def write_face_hashes(face_hashes, proc_url, chunk_bounds, proc_dir=None):
    proc_dir = proc_url if proc_dir is None else proc_dir

    df, tablename = prep_face_hashes(face_hashes, chunk_bounds, proc_dir)

    if io.is_db_url(proc_url):
        io.write_db_dframe(df, proc_url, tablename)

    else:
        raise(Exception("file IO for face hashes not implemented yet"))


def prep_face_hashes(face_hashes, chunk_bounds, proc_dir):
    """ Packaging face hashes to send as a dataframe"""
    items = list(face_hashes.items())
    faces, hashes = zip(*items)
    filenames = [face_filename(proc_dir, chunk_bounds, face) for face in faces]

    to_write = pd.DataFrame({cn.contin_filename: filenames,
                             cn.facehash: hashes})

    return to_write, TABLENAME


def read_all_continuations(proc_url):
    """
    Reads all of the continuation files from a processing directory
    NOT IMPLEMENTED
    """
    pass


def read_continuation_graph(proc_url):
    assert io.is_db_url(proc_url), "graph IO not implemented for files"

    metadata = io.open_db_metadata(proc_url)
    contin_graph = metadata.tables["contin_graph"]

    columns = list(contin_graph.c[name] for name in CONTIN_GRAPH_COLUMNS)
    statement = select(columns)

    dframe = io.read_db_dframe(proc_url, statement)

    return list(zip(dframe[cn.graph_id1], dframe[cn.graph_id2]))


def write_contin_graph_edges(graph_edges, proc_url):
    assert io.is_db_url(proc_url), "graph IO not implemented for files"

    if len(graph_edges) == 0:
        print("WARNING: no graph edges to write")
        return

    ids1, ids2 = zip(*graph_edges)
    dframe = pd.DataFrame({cn.graph_id1: ids1, cn.graph_id2: ids2})

    io.write_db_dframe(dframe, proc_url, "contin_graph")
