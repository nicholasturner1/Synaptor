import numpy as np
cimport numpy as np
cimport cython

DTYPE = np.uint32
ctypedef np.uint32_t DTYPE_t

cpdef centers_of_mass(np.ndarray[DTYPE_t, ndim=3] seg, offset=[0,0,0]):
    """ Computing centroids with an offset """

    sz = seg.shape[0]
    sy = seg.shape[1]
    sx = seg.shape[2]

    offset = np.array(offset, dtype=DTYPE)

    centers = {}
    counts = {}

    cdef int z,y,x
    cdef np.ndarray[DTYPE_t, ndim=1] coord = np.array([0,0,0],dtype=DTYPE)
    cdef DTYPE_t segid
    cdef DTYPE_t zero = 0

    for z in range(sz):
        for y in range(sy):
            for x in range(sx):
                
                segid = seg[z,y,x]

                if segid == zero:
                    continue
                
                coord[0] = z
                coord[1] = y
                coord[2] = x

                if segid in centers:
                    centers[segid] += coord
                    counts[segid] += 1
                else:
                    centers[segid] = np.copy(coord)
                    counts[segid] = 1

    for segid in centers:
        centers[segid] = np.rint(centers[segid] / 
                                 counts[segid]).astype(DTYPE) + offset

    return centers

                
cpdef relabel_data(np.ndarray[DTYPE_t, ndim=3] seg, mapping):
    """ Remapping data entries according to a mapping dictionary """

    sz = seg.shape[0]
    sy = seg.shape[1]
    sx = seg.shape[2]

    cdef int z,y,x
    cdef DTYPE_t segid
    cdef DTYPE_t zero = 0

    for z in range(sz):
        for y in range(sy):
            for x in range(sx):
                
                segid = seg[z,y,x]

                if segid == zero:
                    continue

                if segid in mapping:
                    seg[z,y,x] = mapping[segid]

    return seg
