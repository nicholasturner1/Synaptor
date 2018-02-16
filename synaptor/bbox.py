#!/usr/bin/env python3

"""
Tweaked version of https://github.com/torms3/DataProvider/blob/refactoring/python/dataprovider/box.py
"""
#Pasteurize
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import map
from builtins import zip
from builtins import range
from future import standard_library
standard_library.install_aliases()


from builtins import object
import operator
#from . import tup_ops


class BBox3d(object):


    def __init__(self, v1_or_bbox, v2=None, v3=None):

        if   v3 is not None: #coord-wise
            self.set_slices(v1_or_bbox, v2, v3)

        elif v2 is not None: #begin<->end
            self.set_bounds(v1_or_bbox, v2)

        else: #iterable

            if len(v1_or_bbox) == 2:
                self.set_bounds(*v1_or_bbox)
            elif len(v1_or_bbox) == 3:
                self.set_slices(*v1_or_bbox)
            else:
                raise("something")


    def set_bounds(self, b,e):

        x = slice(b[0], e[0], None)
        y = slice(b[1], e[1], None)
        z = slice(b[2], e[2], None)

        self.set_slices(x,y,z)


    def set_slices(self, x,y,z):

        self._x = x
        self._y = y
        self._z = z


    def index(self):
        """ Convert to an index for np cut-outs """
        return (self._x, self._y, self._z)


    def min(self):
        return (self._x.start, self._y.start, self._z.start)


    def max(self):
        return (self._x.stop, self._y.stop, self._z.stop)


    def transposed(self):
        return BBox3d(self._z, self._y, self._x)


    def astuple(self):
        return (self._x.start, self._y.start, self._z.start,
                self._x.stop,  self._y.stop,  self._z.stop)


    def translate(self, v):

        x = slice(self._x.start + v[0], self._x.stop + v[0], None)
        y = slice(self._y.start + v[1], self._y.stop + v[1], None)
        z = slice(self._z.start + v[2], self._z.stop + v[2], None)

        return BBox3d(x,y,z)


    def merge(self, other):

        xb = min(self._x.start, other._x.start)
        yb = min(self._y.start, other._y.start)
        zb = min(self._z.start, other._z.start)

        xe = max(self._x.start, other._x.start)
        ye = max(self._y.start, other._y.start)
        ze = max(self._z.start, other._z.start)

        x = slice(xb, xe, None)
        y = slice(yb, ye, None)
        z = slice(zb, ze, None)

        return BBox3d(x,y,z)


    def containing_box(loc, box_shape, vol_shape):

        box = BBox3d.centered_box(loc, box_shape)

        shift_up   = tuple( -i  if i < 0 else 0 for i in box.min() )
        shift_down = tuple( j-i if i > j else 0 for (i,j) in zip(box.max(),
                                                                vol_shape))

        total_shift = tuple(map(operator.add, shift_up, shift_down))
        return box.translate(total_shift)


    def centered_box(loc, box_shape):
        """
        Yields a BBox3d centered on the given coordinate of a given shape
        Not guaranteed to remain within any bounds
        """
        margin = tuple(map(operator.floordiv, box_shape, (2 for _ in range(3))))
        begin  = tuple(map(operator.sub, loc, margin))
        end    = tuple(map(operator.add, begin, box_shape))

        return BBox3d(begin, end)


    def __eq__(self, other):
        return self.min() == other.min() and self.max() == other.max()


    def __ne__(self, other):
        return not(self == other)


    def __repr__(self):
        s, e = self.min(), self.max()
        return "<BBox3d {}-{}>".format(s,e)


    def __str__(self):
        return "{}({},{},{})".format(self.__class__.__name__, self._x, self._y, self._z)


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
