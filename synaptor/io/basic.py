#!/usr/bin/env python3


def chunk_tag(chunk_bounds):
    return "{0}_{1}_{2}-{3}_{4}_{5}".format(*chunk_bounds.min(),
                                            *chunk_bounds.max())
