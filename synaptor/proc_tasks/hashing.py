__doc__ = """
Some utilities for hashing groups of values for distributed processing.
"""
import struct
import hashlib
import collections

import pandas as pd

HASHED_INDEX_NAME = "hashed_index"


def basehash(v):
    """ Hash an object, return a hash object. """
    return hashlib.sha224(v)


def pack_many(v):
    if isinstance(v, collections.Iterable):
        fmt = "".join(get_format(elem) for elem in v)
        return struct.pack(fmt, *v)

    else:
        return struct.pack(get_format(v), v)
    

def get_format(v):
    return 'i' if isinstance(v, int) else "d"


def hashval(v, maxval):
    """ Hash a value to an index below maxval. """
    return int(basehash(pack_many(v)).hexdigest(), 16) % maxval


def hashtuple(t, maxval):
    """
    Hash a tuple of values to an index below maxval using
    a combination of the element hash values.
    """
    elem_hashes = tuple(map(basehash, t))
    full_digest = "".join(map(h.hexdigest() for h in elem_hashes))
    return hashval(full_digest, maxval)


def hashcolumns(dframe, columns, maxval):
    """ Hash each value of multiple dataframe columns. """
    columnvals = list(zip(*(dframe[col] for col in columns)))
    return list(hashval(v, maxval) for v in columnvals)


def hashcolumns2(dframe, columns, maxval):
    """
    Hash each value of multiple dataframe columns. (alternate implementation)
    """
    columnvals = list(zip(*(dframe[col] for col in columns)))
    return list(hashtuple(t, maxval) for t in columnvals)


def add_hashed_index(dframe, columns, maxval, null_fillval=None):
    dframe[HASHED_INDEX_NAME] = hashcolumns(dframe, columns, maxval)
    if null_fillval is not None:    
        dframe = fill_nulls(dframe, columns, null_fillval)
    return dframe


def fill_nulls(dframe, columns, fillval):
    for col in columns:
        dframe.loc[pd.isnull(dframe[col]), HASHED_INDEX_NAME] = fillval
    return dframe
