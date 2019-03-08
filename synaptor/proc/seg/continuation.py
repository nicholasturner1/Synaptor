"""
Segment Continuation

A class representing a surface contact of a segment, suggesting that
it might continue on to the chunk on the other side.
"""

from collections import namedtuple

import numpy as np

from .. import hashing


class Continuation(object):
    """
    Continuation - a representation of a segment that contacts
    a surface of a chunk, and may continue to the next chunk
    """

    __slots__ = ("segid", "face", "face_coords")

    def __init__(self, segid, face, face_coords):
        self.segid = segid
        self.face = face
        self.face_coords = face_coords

    def opposite_face(self):
        return Face.opposite(self.face)

    def __repr__(self):
        return f"<Continuation {self.segid}-{self.face}>"

    def __str__(self):
        return f"<Continuation {self.segid}-{self.face}>"


class Face(object):
    """
    Face - a representation for a face of a 3d chunk of data
    """

    __slots__ = ("axis", "hi_index")

    def __init__(self, axis, hi_index):
        self.axis = axis
        self.hi_index = hi_index

    def opposite(self):
        return Face(self.axis, not(self.hi_index))

    def extract(self, data):
        """ Extracts the 2D data at a Face of a 3d chunk """
        index = -1 if self.hi_index else 0
        return np.take(data, index, axis=self.axis)

    def all_faces():
        """ Returns a generator over all possible 3d faces """
        return (Face(axis, hi) for axis in range(3) for hi in (True, False))

    def __eq__(self, other):
        return self.axis == other.axis and self.hi_index == other.hi_index

    def __ne__(self, other):
        return not(self == other)

    def __hash__(self):
        return hash((self.axis, self.hi_index))

    def __repr__(self):
        hi = "high" if self.hi_index else "low"
        return f"<Face {self.axis},{hi}>"

    def __str__(self):
        hi = "high" if self.hi_index else "low"
        return f"<Face {self.axis},{hi}>"


# A class representing a continuation file and associated information
ContinFile = namedtuple("ContinFile", ["filename", "bbox", "face"])


# =========================================================================
# Utility functions
# =========================================================================

def extract_all_continuations(seg):
    """
    Takes chunk of segmented data and finds the continuations
    within that chunk. Returns (1) a dictionary mapping each face
    to the list of continuations at each face, and (2) the set of
    segment ids which have a continuation within the chunk.
    """
    continuations = dict()
    continuation_ids = set()

    for face in Face.all_faces():
        face_continuations = list()

        # Pulls the 2D face arr
        extracted = face.extract(seg)

        # Finds which segids are in the face, and extracts the coords
        # at which each segid exists
        segid_lookup = make_id_lookup(extracted)

        for (segid, coords) in segid_lookup.items():
            continuation_ids.add(segid)
            face_continuations.append(Continuation(segid, face,
                                                   np.array(coords)))

        continuations[face] = face_continuations

    return continuations, continuation_ids


def make_id_lookup(face_arr):
    """
    Takes a 2D numpy array, and finds where the values are nonzero.
    Returns a lookup from segid to the coords at which it exists
    """

    x, y = np.nonzero(face_arr)
    segids = face_arr[(x, y)]

    lookup = dict()
    for (segid, i, j) in zip(segids, x, y):
        if segid not in lookup:
            lookup[segid] = [(i, j)]
        else:
            lookup[segid].append((i, j))

    return lookup


def hash_chunk_faces(chunk_begin, chunk_end, maxval):
    """
    Need a hash function which maps opposite ends of adjacent chunks
    to the same value
    """
    face_hashes = dict()

    for face in Face.all_faces():
        if face.hi_index:
            chunk_id = chunk_end
        else:
            chunk_id = list(chunk_end)
            chunk_id[face.axis] = chunk_begin[face.axis]

        to_hash = (chunk_id[0], chunk_id[1], chunk_id[2], face.axis)
        face_hashes[face] = hashing.hashval(to_hash, maxval=maxval)

    return face_hashes
