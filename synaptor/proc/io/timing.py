""" Task Time Duration IO """


import os

from sqlalchemy import select
from sqlalchemy.sql import and_

from ... import io
from .. import colnames as cn
from . import filenames as fn


TIMING_COLUMNS = [cn.task_name, cn.timing_tag, cn.task_time]


def _read_timing_file(filename):
    with open(filename) as f:
        return float(f.read().strip())


def _write_timing_file(time, filename):
    with open(filename, "w+") as f:
        f.write(f"{time}")


def timing_fname(proc_dir, task_name, timing_tag):
    basename = fn.timing_fmtstr.format(timing_tag)

    return os.path.join(proc_dir, fn.timing_dirname, basename)


def read_task_timing(proc_url, task_name, tag):
    """ Reads timing info for a given timing tag """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        timing_log = metadata.tables["timing_log"]
        columns = list(timing_log.c[name] for name in TIMING_COLUMNS)
        statement = select(columns).where(and_(
                        timing_log.c[cn.timing_tag] == tag,
                        timing_log.c[cn.task_name] == task_name))

        return io.read_db_dframe(proc_url, statement)

    else:
        local_fname = io.pull_file(timing_fname(proc_url, task_name, tag))

        _read_timing_file(local_fname)


def write_task_timing(time, task_name, tag, proc_url):
    """ Writes timing info for a given timing tag """
    if io.is_db_url(proc_url):
        metadata = io.open_db_metadata(proc_url)

        timing_log = metadata.tables["timing_log"]
        statement = timing_log.insert().values({cn.timing_tag: tag,
                                                cn.task_name: task_name,
                                                cn.task_time: time})

        io.execute_db_statement(proc_url, statement)

    else:
        dest_filename = timing_fname(proc_url, task_name, tag)
        local_filename = "./timing"

        _write_timing_file(local_filename)
        io.send_file(local_filename, dest_filename)


def read_all_task_timing(proc_url, task_name):
    assert io.is_db_url(proc_url), "not implemented for files"

    metadata = io.open_db_metadata(proc_url)

    timing_log = metadata.tables["timing_log"]
    columns = list(timing_log.c[name] for name in TIMING_COLUMNS)
    statement = select(columns).where(
                    timing_log.c[cn.task_name] == task_name)

    return io.read_db_dframe(proc_url, statement)
