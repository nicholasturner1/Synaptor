#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import map
from future import standard_library
standard_library.install_aliases()

__doc__ = """

Coordinate Chunking Functions

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


import itertools

from . import bbox
from .vector import Vec3d


def chunk_bboxes(vol_size, chunk_size, offset=None, mip=0):
    """
    Break up a volume of a given size into chunks. The desired coordinates
    of the chunks should start at the offset value
    """

    if mip > 0:
        mip_factor = 2 ** mip
        vol_size = (vol_size[0]//mip_factor,
                    vol_size[1]//mip_factor,
                    vol_size[2])

        chunk_size = (chunk_size[0]//mip_factor,
                      chunk_size[1]//mip_factor,
                      chunk_size[2])

        if offset is not None:
            offset = (offset[0]//mip_factor,
                      offset[1]//mip_factor,
                      offset[2])

    x_bnds = bounds1D(vol_size[0], chunk_size[0])
    y_bnds = bounds1D(vol_size[1], chunk_size[1])
    z_bnds = bounds1D(vol_size[2], chunk_size[2])

    bboxes = [ bbox.BBox3d(x,y,z)
               for (x,y,z) in itertools.product(x_bnds, y_bnds, z_bnds) ]

    if offset is not None:
        bboxes = [ bb.translate(offset) for bb in bboxes ]

    return bboxes


def bounds1D(full_width, step_size):
    """
    Return the bbox coordinates for a single dimension given
    the size of the chunked dimension and the size of each box
    """
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
    """Return the bounding box corner closest to the given point"""

    diff = Vec3d(pt) - offset
    index = diff / chunk_size
    closest = round(index)

    return closest * chunk_size + offset
