#!/usr/bin/env python3


import numpy as np


def make_info_arr(start_lookup):

    ordering = sorted(start_lookup.keys())
    dims     = infer_dims(ordering)

    ordered = [start_lookup[k] for k in ordering]

    arr = np.array([None for _ in range(len(ordered))]) #object arr
    for i in range(len(ordered)):
        arr[i] = ordered[i]

    return arr.reshape(dims)


def infer_dims(ordered_tups):

    #assuming the grid is full and complete, then
    # each dim's first index is repeated a number of times
    # equal to the product of the other dimension lengths.
    # => we can find the length in that dimension by dividing
    # the total # elems by this product

    num_tups = len(ordered_tups)
    first_x, first_y, first_z = ordered_tups[0]

    y_times_z = len(list(filter(lambda v: v[0] == first_x, ordered_tups)))
    x_times_z = len(list(filter(lambda v: v[1] == first_y, ordered_tups)))
    x_times_y = len(list(filter(lambda v: v[2] == first_z, ordered_tups)))

    assert num_tups % y_times_z == 0, "grid incomplete or redundant"
    assert num_tups % x_times_z == 0, "grid incomplete or redundant"
    assert num_tups % x_times_y == 0, "grid incomplete or redundant"

    x = num_tups  // y_times_z
    y = x_times_y // x
    z = x_times_z // x

    return (x,y,z)
