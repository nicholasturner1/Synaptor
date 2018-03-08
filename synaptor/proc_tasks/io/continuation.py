#!/usr/bin/env python3
__doc__ = """
Cleft continuation IO for processing tasks
"""

import os

from ... import io
from ...types import continuation


CONTN_DIRNAME = "continuations"
CONTN_FMTSTR = "conts_{tag}.h5"


def read_chunk_continuations(fname):
    """Reads the continuations for a chunk"""
    return continuation.Continuation.read_all_from_fname(fname)


def write_chunk_continuations(conts, chunk_bounds, proc_dir_path):
    """Writes the continuations for a chunk to a processing directory"""
    chunk_tag = io.fname_chunk_tag(chunk_bounds)
    fname = os.path.join(proc_dir_path, CONTN_DIRNAME,
                         CONTN_FMTSTR.format(tag=chunk_tag))

    fobj = io.open_h5(fname)
    local_fname = fobj.filename
    for c in conts:
        c.write_to_fobj(fobj)
    fobj.close()

    if io.is_remote_path(fname):
        io.send_local_file(local_fname, fname)


def read_all_continuations(proc_dir_path):
    """
    Reads all of the continuation files from a processing directory
    Currently assumes that NOTHING else is in the same subdirectory
    """
    continuation_dir = os.path.join(proc_dir_path, CONTN_DIRNAME)
    fnames = io.pull_all_files(continuation_dir)

    starts = [io.bbox_from_fname(f).min() for f in fnames ]
    cont_dicts = [ read_chunk_continuations(f) for f in fnames ]

    info_arr = io.utils.make_info_arr({s : cd
                                       for (s,cd) in zip(starts, cont_dicts)})
    return info_arr, os.path.dirname(fnames[0])
