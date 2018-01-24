#!/usr/bin/env python3

#Pasteurize
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import map
from future import standard_library
standard_library.install_aliases()


import itertools, operator

from . import bbox

def chunk_bboxes(vol_size, chunk_size, offset=None):

    x_bnds = bounds1D(vol_size[0], chunk_size[0])
    y_bnds = bounds1D(vol_size[1], chunk_size[1])
    z_bnds = bounds1D(vol_size[2], chunk_size[2])

    bboxes = [ bbox.BBox3d(x,y,z) 
               for (x,y,z) in itertools.product(x_bnds, y_bnds, z_bnds) ]

    if offset is not None:
        bboxes = [ bb.translate(offset) for bb in bboxes ]

    return bboxes


def bounds1D(full_width, step_size):

    assert step_size > 0, "invalid step_size: {}".format(step_size)
    assert full_width > 0, "invalid volume_width: {}".format(full_width)

    start = 0
    end = step_size

    bounds = []
    while end < full_width:
        bounds.append(slice(start, end))

        start += step_size
        end   += step_size

    #last window
    bounds.append(slice(start, end))

    return bounds


def find_closest_chunk_boundary(pt, offset, chunk_size):

    diff = tuple(map(operator.sub, pt,offset))
    index = tuple(map(operator.truediv, diff,chunk_size))
    closest = tuple(map(round, index))
    
    shift = tuple(map(operator.mul, closest,chunk_size))
    return tuple(map(operator.add, shift,offset))
