#!/usr/bin/env python3
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import zip
from builtins import range
from builtins import str
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import object

__doc__ = """
Segment Continuation

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""


import numpy as np
import h5py


class Continuation(object):
    """
    Continuation - a representation of a segment that contacts
     a surface of a chunk, and may continue to the next chunk
    """

    __slots__ = ("segid","face","face_coords")

    def __init__(self, segid, face, face_coords=[]):

        self.segid = segid
        self.face  = face
        self.face_coords = face_coords


    def set_face_coords(self, coords):
        self.face_coords = coords


    def opposite_face(self):
        return Face.opposite(self.face)


    def write_to_fname(self, fname):
        with h5py.File(fname) as f:
            return self.write_to_fobj(fname)


    def read_all_from_fname(fname):

        res = {}
        with h5py.File(fname) as f:

            for face in Face.all_faces():
                face_dir = face.to_dir()

                if not Face.represented_in_h5(f,face):
                     res[face] = []
                     continue

                all_conts = [ Continuation.read_from_fobj(f,face,int(segid))
                              for segid in f["/"+face_dir].keys() ]
                res[face] = all_conts

        return res


    def read_from_fname(fname, segid):
        with h5py.File(fname) as f:
            return read_from_fobj(f, segid)


    def read_from_fobj(f, face, segid):

        face_dir = face.to_dir()
        coords_path = "/{face_dir}/{segid}".format(face_dir=face_dir,
                                                   segid=segid)
        face_coords = f[coords_path].value

        return Continuation(segid, face, face_coords)


    def write_to_fobj(self, f):

        face_dir = self.face.to_dir()
        f.create_dataset("/{face_dir}/{segid}".format(
                         face_dir=face_dir, segid=self.segid),
                         dtype=np.uint16, data=self.face_coords)


    def __repr__(self):
        return "<Continuation {segid}-{face}>".format(segid=self.segid,
                                                      face=repr(self.face))


    def __str__(self):
        return "<Continuation {segid}-{face}>".format(segid=self.segid,
                                                      face=str(self.face))


class Face(object):
    """
    Face - a representation for a face of a chunk of data
    """

    __slots__ = ("axis","hi_index")

    def __init__(self, axis, hi_index):

        self.axis = axis
        self.hi_index = hi_index


    def opposite(self):
        return Face(self.axis, not(self.hi_index))


    def extract(self, data):
        """ Extracts the 2D data at a Face of a 3d chunk """
        index = -1 if self.hi_index else 0
        return np.take(data, index, axis=self.axis)


    def to_dir(self):
        hi = "high" if self.hi_index else "low"
        return "{axis}/{hi}".format(axis=self.axis, hi=hi)


    def represented_in_h5(fobj, face):
        hi = "high" if face.hi_index else "low"
        axis_str = str(face.axis)
        return (axis_str in fobj.keys() and
                hi in fobj[axis_str].keys())


    def all_faces():
        """ Returns a generator over all possible 3d faces """
        return (Face(axis,hi) for axis in range(3) for hi in (True,False))


    def __eq__(self, other):
        return self.axis == other.axis and self.hi_index == other.hi_index


    def __ne__(self, other):
        return not(self == other)


    def __hash__(self):
        return hash((self.axis,self.hi_index))


    def __repr__(self):
        hi = "high" if self.hi_index else "low"
        return "<Face {axis},{hi}>".format(axis=self.axis, hi=hi)


    def __str__(self):
        hi = "high" if self.hi_index else "low"
        return "<Face {axis},{hi}>".format(axis=self.axis, hi=hi)


#=========================================================================
# Utility functions
#=========================================================================

def extract_all_continuations(seg):
    """
    Takes chunk of segmented data and finds the continuations
    within that chunk
    """

    continuations = []
    for face in Face.all_faces():

        #Pulls the 2D face arr
        extracted = face.extract(seg)

        #Finds which segids are in the face, and extracts the coords
        # at which that segid exists
        segid_lookup = make_id_lookup(extracted)
        for (segid,coords) in segid_lookup.items():
            continuations.append(Continuation(segid, face, np.array(coords)))

    return continuations


def make_id_lookup(face_arr):
    """
    Takes a 2D numpy array, and finds where the values are nonzero.
    Returns a lookup from segid to the coords at which it exists
    """

    x,y = np.nonzero(face_arr)
    segids = face_arr[(x,y)]

    lookup = {}
    for (segid,i,j) in zip(segids, x,y):
        if segid not in lookup:
            lookup[segid] = [(i,j)]
        else:
            lookup[segid].append((i,j))

    return lookup
