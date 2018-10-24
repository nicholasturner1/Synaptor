#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import map
from builtins import zip
from builtins import range
from future import standard_library
standard_library.install_aliases()

__doc__ = """

3D-Coordinate Bounding Box

Tweaked version of https://github.com/torms3/DataProvider/blob/refactoring/python/dataprovider/box.py

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


from builtins import object
import operator

from .vector import Vec3d, minimum, maximum


class BBox3d(object):
    """
    3D-Coordinate Bounding Box

    index()      -- return an np array index
    min()        -- return the minimum coordinate
    max()        -- return the (exclusive) upper coordinate
    transpose()  -- return a new bbox with coordinates reversed
    translate()  -- return a new bbox with shifted coordinates
    merge()      -- return a new bbox containing this and another box
    astuple()    -- return a simplified representation
    """

    __slots__ = ("_min","_max")

    def __init__(self, v1_or_bbox, v2=None, v3=None):
        """
        Initialize a box from a (1) box, (2) pair of vectors, or
        (3) triplet of slices
        """

        if v3 is not None: #slices- coord-wise
            self.set_slices(v1_or_bbox, v2, v3)

        elif v2 is not None: #vectors- begin<->end
            self.set_bounds(v1_or_bbox, v2)

        else: #iterable

            if len(v1_or_bbox) == 2:
                self.set_bounds(*v1_or_bbox)
            elif len(v1_or_bbox) == 3:
                self.set_slices(*v1_or_bbox)
            else:
                raise(ValueError("unexpected argument specified"))

    def set_bounds(self, b,e):
        self._min = Vec3d(b)
        self._max = Vec3d(e)

    def set_slices(self, x,y,z):
        self._min = Vec3d(x.start, y.start, z.start)
        self._max = Vec3d(x.stop, y.stop, z.stop)

    def index(self):
        """ Convert to an index for np cut-outs """
        return (slice(self._min[0], self._max[0]),
                slice(self._min[1], self._max[1]),
                slice(self._min[2], self._max[2]))

    def min(self):
        """Return the minimum coordinate"""
        return Vec3d(self._min)

    def max(self):
        """Return the maximum coordinate"""
        return Vec3d(self._max)

    def shape(self):
        """Return the box shape (max - min)"""
        return self.max() - self.min()

    def transpose(self):
        """Return the same box with reversed coordinates"""
        return BBox3d(Vec3d(self._min.z, self._min.y, self._min.x),
                      Vec3d(self._max.z, self._max.y, self._max.x))

    def astuple(self):
        """Return in a simplified representation"""
        return (self._min.x, self._min.y, self._min.z,
                self._max.x, self._max.y, self._max.z)

    def translate(self, v):
        """Shift by a coordinate v, return a copy"""
        return BBox3d(self._min+v, self._max+v)

    def merge(self, other):
        """
        Consolidate two bounding boxes together, forming a
        new box which contains both original boxes
        """
        return BBox3d(minimum(self._min, other._min),
                      maximum(self._max, other._max))

    def intersect(self, other):
        """
        Find the intersection between two bounding boxes

        The boxes are assumed to overlap, and will produce
        an invalid box if this is violated
        """
        return BBox3d(maximum(self._min, other._min),
                      minimum(self._max, other._max))


    def scale(self, factor):
        """Scales the coordinates by a given factor, return a copy"""
        return BBox3d(self._min*factor, self._max*factor)

    def scale2d(self, factor):
        return BBox3d(self._min*[factor,factor,1],
                      self._max*[factor,factor,1])

    def div(self, factor):
        return BBox3d(self._min//factor, self._max//factor)

    def div2d(self, factor):
        return BBox3d(self._min//[factor,factor,1],
                      self._max//[factor,factor,1])

    def __eq__(self, other):
        return self.min() == other.min() and self.max() == other.max()

    def __ne__(self, other):
        return not(self == other)

    def __repr__(self):
        s, e = self.min(), self.max()
        return "<BBox3d {}-{}>".format(s,e)

    def __str__(self):
        return "{}({}<->{})".format(self.__class__.__name__,
                                    tuple(self._min),
                                    tuple(self._max))

    def __hash__(self):
        return hash(self.astuple())

    def contains(self, x):
        return self._min.all_le(x) and self._max.all_gt(x)

    def shrink_by(self, v):
        v = Vec3d(v)
        return BBox3d(self._min + v, self._max - v)

    def grow_by(self, v):
        v = Vec3d(v)
        return BBox3d(self._min - v, self._max + v)

#=========================================================================
# Utility Functions
#=========================================================================

def containing_box(loc, box_shape, vol_shape):
    """
    Find a bounding box of a given shape that contains loc.
    The resulting box is constrained to stay within (0,0,0)<->vol_shape
    """
    #these coordinates might be out of bounds
    box = centered_box(loc, box_shape)
    return shift_to_bounds(box, vol_shape)


def shift_to_bounds(box, vol_shape):

    shift_up = (box.min() - abs(box.min())) // -2
    over = box.max() - vol_shape
    shift_down = (over + abs(over)) // -2

    total_shift = shift_up + shift_down
    return box.translate(total_shift)


def centered_box(loc, box_shape):
    """
    Yields a BBox3d centered on the given coordinate of a given shape
    Not guaranteed to remain within any bounds
    """
    margin = Vec3d(box_shape) // 2
    begin  = loc - margin
    end    = begin + box_shape

    return BBox3d(begin, end)


def expand_box_within_bounds(box, box_shape, vol_shape):

    if box.shape().all_ge(box_shape):
        return shift_to_bounds(box, vol_shape)

    over = box_shape - box.shape()
    shape_incr = (over + abs(over)) // 4

    return shift_to_bounds(box.grow_by(shape_incr), vol_shape)


if __name__ == "__main__":

    import unittest

    class BBox3dTests(unittest.TestCase):

        def setUp(self):
            self.b1 = BBox3d(slice(0,1,None),slice(2,3,None),slice(4,5,None))
            self.b2 = BBox3d((0,2,4),(1,3,5))
            self.b3 = BBox3d((slice(0,1,None),slice(2,3,None),slice(4,5,None)))
            self.b4 = BBox3d(((1,3,5),(2,4,6)))

        def test_index(self):
            self.assertEqual(self.b1.index(),
                             (slice(0,1,None),slice(2,3,None),slice(4,5,None)))
            self.assertEqual(self.b2.index(),
                             (slice(0,1,None),slice(2,3,None),slice(4,5,None)))
            self.assertEqual(self.b3.index(),
                             (slice(0,1,None),slice(2,3,None),slice(4,5,None)))
            self.assertEqual(self.b4.index(),
                             (slice(1,2,None),slice(3,4,None),slice(5,6,None)))

        def test_min(self):
            self.assertEqual(self.b1.min(), (0,2,4))
            self.assertEqual(self.b2.min(), (0,2,4))
            self.assertEqual(self.b3.min(), (0,2,4))
            self.assertEqual(self.b4.min(), (1,3,5))

        def test_max(self):
            self.assertEqual(self.b1.max(), (1,3,5))
            self.assertEqual(self.b2.max(), (1,3,5))
            self.assertEqual(self.b3.max(), (1,3,5))
            self.assertEqual(self.b4.max(), (2,4,6))

        def test_eq(self):
            self.assertTrue(self.b1 == self.b2)
            self.assertTrue(self.b1 == self.b3)
            self.assertTrue(self.b2 == self.b3)
            self.assertFalse(self.b1 == self.b4)

        def test_ne(self):
            self.assertTrue(self.b1 != self.b4)
            self.assertTrue(self.b2 != self.b4)
            self.assertTrue(self.b3 != self.b4)
            self.assertFalse(self.b4 != self.b4)

        def test_translate(self):
            bp1 = self.b1.translate((1,1,1))
            bm1 = self.b1.translate((-1,-1,-1))

            self.assertEqual(bp1.min(), (1,3,5))
            self.assertEqual(bp1.max(), (2,4,6))

            self.assertEqual(bm1.min(), (-1,1,3))
            self.assertEqual(bm1.max(), (0,2,4))

            self.assertTrue(bp1 == self.b4)

    unittest.main()
