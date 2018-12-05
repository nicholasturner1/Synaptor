#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <limits>

namespace py = pybind11;


const char* manhattan_dist2d__doc__ = R"/(
Compute manhattan distance to nearest segment in-place.

Take a segmentation volume along with another volume of the same size.
Compute manhattan distances to the nearest segment within the second
volume, and record the closest segment for each index within the
segmentation volume.

Args:
    seg (3darray<T>): A segmentation volume.
    dists (3darray<T>): A scratch volume for computing distances.

Returns:
    3darray<T> : A modified dists volume
)/";
template<typename T, typename S>
py::array_t<T> manhattan_dist2d(py::array_t<S> seg, py::array_t<T> dists)
{
    auto rs = seg.template mutable_unchecked<3>();
    auto rd = dists.template mutable_unchecked<3>();

    assert(rs.shape(0)==rd.shape(0));
    assert(rs.shape(1)==rd.shape(1));
    assert(rs.shape(2)==rd.shape(2));

    T maxdist = std::numeric_limits<T>::max();
    // forward pass
    for (ssize_t i = 0; i < rs.shape(0); ++i){
        for (ssize_t j = 0; j < rs.shape(1); ++j){
            for (ssize_t k = 0; k < rs.shape(2); ++k){

                if (rs(i, j, k) != 0){
                    rd(i, j, k) = 0;
                } else {
                    rd(i, j, k) = maxdist;
                }

                if (j > 0 && rd(i, j-1, k) < rd(i, j, k)){
                    rd(i, j, k) = rd(i, j-1, k)+1;
                    rs(i, j, k) = rs(i, j-1, k);
                }

                if (k > 0 && rd(i, j, k-1) < rd(i, j, k)){
                    rd(i, j, k) = rd(i, j, k-1)+1;
                    rs(i, j, k) = rs(i, j, k-1);
                }
            }
        }
    }

    ssize_t maxi = rs.shape(0)-1;
    ssize_t maxj = rs.shape(1)-1;
    ssize_t maxk = rs.shape(2)-1;
    // backward pass
    for (ssize_t i = maxi; i >= 0; --i){
        for (ssize_t j = maxj; j >= 0; --j){
            for (ssize_t k = maxk; k >= 0; --k){

                if (j < maxj && rd(i, j+1, k) < rd(i, j, k)){
                    rd(i, j, k) = rd(i, j+1, k)+1;
                    rs(i, j, k) = rs(i, j+1, k);
                }

                if (k < maxk && rd(i, j, k+1) < rd(i, j, k)){
                    rd(i, j, k) = rd(i, j, k+1)+1;
                    rs(i, j, k) = rs(i, j, k+1);
                }
            }
        }
    }

    return dists;
}


const char* dilate_by_k__doc__ = R"/(
Dilate a segmentation by manhattan distance in 2D in-place.

Args:
    seg (3darray<T>): A segmentation volume.
    dists (3darray<T>): A scratch volume for computing distances.

Returns:
    3darray<T> : A modified seg volume
)/";
template<typename T, typename S>
py::array_t<T> dilate_by_k(py::array_t<T> seg, py::array_t<T> dists,
                           unsigned int dil_k)
{
    dists = manhattan_dist2d(seg, dists);

    auto rs = seg.template mutable_unchecked<3>();
    auto rd = dists.template unchecked<3>();

    for (ssize_t i = 0; i < rs.shape(0); ++i){
        for (ssize_t j = 0; j < rs.shape(1); ++j){
            for (ssize_t k = 0; k < rs.shape(2); ++k){
                if (rd(i, j, k) > dil_k){
                    rs(i, j, k) = 0;
                }
            }
        }
    }

    return seg;
}


PYBIND11_MODULE(_seg_utils, m) {
    m.def("manhattan_distance2d",
          &manhattan_dist2d<unsigned int, unsigned int>);
    m.def("manhattan_distance2d",
          &manhattan_dist2d<unsigned int, float>,
          manhattan_dist2d__doc__);

    m.def("dilate_by_k", &dilate_by_k<unsigned int, unsigned int>);
    m.def("dilate_by_k", &dilate_by_k<float, unsigned int>);
    m.def("dilate_by_k", &dilate_by_k<unsigned int, float>);
    m.def("dilate_by_k", &dilate_by_k<float, float>,
          dilate_by_k__doc__);
}
