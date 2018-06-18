#!/usr/bin/env python3
__doc__ = """
Connected Component Consolidation

Nicholas Turner <nturner@cs.princeton.edu>, 2018
"""

import numpy as np

from ...types import continuation
from .. import utils


def merge_connected_continuations(continuation_arr, max_face_shape=(1024,1024)):
    """
    Finds an id mapping to merge the continuations which match across faces
    """

    matches = find_connected_continuations(continuation_arr)
    ccs = utils.find_connected_components(matches)
    return utils.make_id_map(ccs)


def find_connected_continuations(continuation_arr, max_face_shape=(1024,1024)):
    """
    Finds the edges of a graph which describes the continuation connectivity
    """

    sizes   = continuation_arr.shape
    face_checked = np.zeros((6,) + continuation_arr.shape, dtype=np.bool)
    matches = []

    for index in np.ndindex(sizes):

        for face in continuation.Face.all_faces():

            #bounds checking
            if face.hi_index and index[face.axis] == sizes[face.axis] - 1:
                continue
            if not face.hi_index and index[face.axis] == 0:
                continue

            #if we've processed the other side already
            if face_checked[(face.axis + 3*face.hi_index,)+index]:
                continue
            else:
                face_checked[(face.axis + 3*face.hi_index,)+index] = True

            index_to_check = list(index)
            if face.hi_index:
                index_to_check[face.axis] += 1
            else:
                index_to_check[face.axis] -= 1
            index_to_check = tuple(index_to_check)
            oppface = face.opposite()

            face_checked[(oppface.axis+3*oppface.hi_index,)+index_to_check] = True

            conts_here  = continuation_arr[index][face]
            conts_there = continuation_arr[index_to_check][oppface]

            new_matches = match_continuations(conts_here, conts_there,
                                              face_shape=max_face_shape)

            matches.extend(new_matches)


    return matches


def match_continuations(conts1, conts2, face_shape=(1024,1024)):
    """ Determines which continuations match within the two lists """

    face1 = reconstruct_face(conts1, shape=face_shape)
    face2 = reconstruct_face(conts2, shape=face_shape)

    intersection_mask = np.logical_and(face1 !=0, face2 !=0)

    matches1 = face1[intersection_mask]
    matches2 = face2[intersection_mask]

    return list(set(zip(matches1,matches2)))


def reconstruct_face(continuations, shape=(1024,1024)):

    face = np.zeros(shape, dtype=np.uint32)

    for c in continuations:
        face[tuple(c.face_coords.T)] = c.segid

    return face
