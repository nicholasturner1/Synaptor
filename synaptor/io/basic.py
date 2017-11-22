#!/usr/bin/env python3

import pandas as pd

#just using csvs for now, but can experiment with parquet, feather, etc as needed
def write_edges(edges_dframe, fname):
    edges_dframe.to_csv(index=False)


def read_edges(fname):
    return pd.read_csv(fname)
