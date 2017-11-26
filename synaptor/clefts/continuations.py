#!/usr/bin/env python3


import numpy as np
import h5py


def extract_all_continuations(segs):

    continuations = []
    for axis in (0,1,2):
        for hi_index in (True,False):

            face = Face(axis, hi_index)
            extracted = face.extract(segs)

            segid_lookup = make_id_lookup(extracted)
            for (segid,coords) in segid_lookup.items():
                continuations.append(Continuation(segid, face, np.array(coords)))

    return continuations


def make_id_lookup(face_arr):

    x,y = np.nonzero(face_arr)
    segids = face_arr[(x,y)]

    lookup = {}
    for (segid,i,j) in zip(segids, x,y):
        if segid not in lookup:
            lookup[segid] = [(i,j)]
        else:
            lookup[segid].append((i,j))

    return lookup


class Continuation:


    def __init__(self, segid, face, face_coords=[]):

        self.segid = segid
        self.face  = face
        self.face_coords = face_coords


    def set_face_coords(self, coords):
        self.face_coords = coords


    def opposite_face(self):
        return opposite_face(self.face)


    def write_to_fname(self, fname):
        with h5py.File(fname) as f:
            return self.write_to_fobj(fname)


    def read_all_from_fname(fname):
        with h5py.File(fname) as f:
            return [self.read_from_fobj(f, segid) for segid in f.keys()]


    def read_from_fname(fname, segid):
        with h5py.File(fname) as f:
            return read_from_fobj(f, segid)


    def read_from_fobj(f, segid):
        
        face = Face.read_from_fobj(f, segid)
        face_coords = f["/{segid}/coords"].value

        return Continuation(segid, face, face_coords)


    def write_to_fobj(f):

        self.face.write_to_fobj(f, self.segid)
        f.create_dataset("/{segid}/coords".format(segid=self.segid),
                         dtype=np.uint16, data=self.face_coords)


    def __repr__(self):
        return "<Continuation {segid}-{face}>".format(segid=self.segid,
                                                      face=repr(self.face))


    def __str__(self):
        return "<Continuation {segid}-{face}>".format(segid=self.segid,
                                                      face=str(self.face))


class Face:


    def __init__(self, axis, hi_index):

        self.axis = axis
        self.hi_index = hi_index


    def extract(self, data):
        index = -1 if self.hi_index else 0
        return np.take(data, index, axis=self.axis)


    def read_from_fobj(f, segid=0):
        axis = f["/{segid}/face_axis"].value
        hi_index = f["/{segid}/face_hi_index"].value
        return Face(axis, hi_index)


    def write_to_fobj(self, segid=0):

        f.create_dataset("/{segid}/face_axis".format(segid=segid),
                         dtype=np.uint8, data=self.axis)
        f.create_dataset("/{segid}/face_hi_index".format(segid=segid),
                         dtype=np.bool,  data=self.hi_index)

    def __repr__(self):
        hi = "high" if self.hi_index else "low"
        return "<Face {axis},{hi}>".format(axis=self.axis, hi=hi)
    

    def __str__(self):
        hi = "high" if self.hi_index else "low"
        return "<Face {axis},{hi}>".format(axis=self.axis, hi=hi)

