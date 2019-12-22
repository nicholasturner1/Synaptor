""" Overlap Matrix Consolidation """


import numpy as np
import scipy.sparse as sp

from .. import overlap


def apply_chunk_id_maps(overlap_arr, chunk_id_maps):
    """
    Applies id maps to each overlap matrix, returns a combined overlap mat
    """
    rs, cs, vs = list(), list(), list()
    for (overlap, id_map) in zip(overlap_arr.flat, chunk_id_maps.flat):
        for (r, c, v) in zip(overlap.row, overlap.col, overlap.data):
            rs.append(id_map[r])
            cs.append(c)
            vs.append(v)

    return sp.coo_matrix((vs, (rs, cs)))


def consolidate_overlaps(overlap_mat_arr, dtype=np.uint64):

    num_entries = 0
    for new_mat in overlap_mat_arr.flat:
        num_entries += new_mat.data.size

    full_matrix = make_empty_matrix(num_entries, dtype=dtype)

    last_row = 0
    for new_mat in overlap_mat_arr.flat:
        expand_mat(full_matrix, new_mat, last_row)
        last_row += new_mat.data.size

    full_matrix = sp.coo_matrix(full_matrix)
    full_matrix.sum_duplicates()

    return full_matrix


def make_empty_matrix(num_raw_entries, dtype=np.uint32):
    rs = np.zeros((num_raw_entries,), dtype=dtype)
    cs = np.zeros((num_raw_entries,), dtype=dtype)
    vs = np.zeros((num_raw_entries,), dtype=dtype)

    return vs, (rs, cs)


def expand_mat(full_mat, new_mat, first_row):

    v1, (r1, c1) = full_mat
    r2, c2, v2 = sp.find(new_mat)

    last_row = first_row + v2.size

    r1[first_row:last_row] = r2
    c1[first_row:last_row] = c2
    v1[first_row:last_row] = v2
