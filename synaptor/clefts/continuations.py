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

        res = {}
        with h5py.File(fname) as f:

            for face in Face.all_faces():
                face_dir = face.to_dir()
                all_conts = [ Continuation.read_from_fobj(f,face,segid)
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


    def to_dir(self):
        hi = "high" if self.hi_index else "low"
        return "{axis}/{hi}".format(axis=self.axis, hi=hi)

    
    def all_faces():
        """ Returns a generator over all possible 3d faces """
        return (Face(axis,hi) for axis in range(3) for hi in (True,False))


    def __repr__(self):
        hi = "high" if self.hi_index else "low"
        return "<Face {axis},{hi}>".format(axis=self.axis, hi=hi)
    

    def __str__(self):
        hi = "high" if self.hi_index else "low"
        return "<Face {axis},{hi}>".format(axis=self.axis, hi=hi)

