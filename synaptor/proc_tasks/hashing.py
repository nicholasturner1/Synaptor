__doc__ = """
Some utilities for hashing groups of values for distributed processing.
"""
import hashlib


def basehash(v):
    """ Hash an object, return a hash object. """
    return hashlib.sha224(bytes(v))


def hashval(v, maxval):
    """ Hash a value to an index below maxval. """
    return int(basehash(v).hexdigest(), 16) % maxval


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
