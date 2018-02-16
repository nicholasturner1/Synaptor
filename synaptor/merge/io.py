#!/usr/bin/env python3

#Pasteurize
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import dict
from builtins import zip
from future import standard_library
standard_library.install_aliases()


import os
import pandas as pd

from .. import io


def write_dup_id_map(id_map, proc_dir_path):

    df = pd.DataFrame(pd.Series(id_map), columns=["new_id"])
    io.utils.write_single_df(df, proc_dir_path, "dup_id_map.df")


def read_dup_id_map(proc_dir_path):
    df = io.utils.read_single_df(proc_dir_path, "dup_id_map.df")
    return dict(zip(df.index, df.new_id))


def write_final_df(df, proc_dir_path):
    io.utils.write_single_df(df, proc_dir_path, "final.df")


def read_final_df(proc_dir_path):
    return io.utils.read_single_df(proc_dir_path, "final.df")


def write_cons_edge_list(df, proc_dir_path):
    io.utils.write_single_df(df, proc_dir_path, "cons_edges.df")


def read_cons_edge_list(df, proc_dir_path):
    return io.utils.read_single_df(proc_dir_path, "cons_edges.df")
