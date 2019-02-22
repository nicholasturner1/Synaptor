"""
Some utilities for hashing groups of values for distributed processing.
"""

import random
import struct
import hashlib
import collections

import pandas as pd


HASHED_INDEX_NAME = "hashed_index"
PRIME = 4839472903831


def basehash(v, seed=54321, verbose=False):
    """ Hash an object, return a hash object. """
    random.seed(seed)
    a = random.randint(1, PRIME-1)
    b = random.randint(0, PRIME-1)
    ret = (a*v + b) % PRIME

    if verbose:
        print((v, a, b, ret))

    return ret


def pack_many(v, verbose=False):
    if isinstance(v, collections.Iterable):
        if verbose:
            print(",".join(map(str, v)))
        return int.from_bytes(",".join(map(str, v)).encode(),
                              byteorder="little")

    else:
        return int.from_bytes(str(v).encode(), byteorder="little")


def get_format(v):
    return 'i' if isinstance(v, int) else "d"


def hashval(v, maxval):
    """ Hash a value to an index below maxval. """
    return basehash(pack_many(v)) % maxval


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


def add_hashed_index(dframe, columns, maxval,
                     indexname=HASHED_INDEX_NAME, null_fillval=None):
    dframe[indexname] = hashcolumns(dframe, columns, maxval)
    if null_fillval is not None:
        dframe = fill_nulls(dframe, columns, null_fillval,
                            indexname=indexname)

    return dframe


def fill_nulls(dframe, columns, fillval, indexname=HASHED_INDEX_NAME):
    for col in columns:
        dframe.loc[pd.isnull(dframe[col]), indexname] = fillval

    return dframe
