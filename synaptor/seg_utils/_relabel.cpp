#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;


const char* relabel_data__doc__ = R"/(
Relabel data according to a mapping dict in-place.

Args:
    d (3darray<T>): A data volume.
    mapping (dict<T,T>): A mapping from data values in the volume to
        new desired values.

Returns:
    3darray<T> : The same data volume with desired values replaced.
)/";
template<typename T>
py::array_t<T> relabel_data(py::array_t<T> d, std::unordered_map<T,T> mapping)
{
    auto r = d.template mutable_unchecked<3>();
    T v;

    for (ssize_t i = 0; i < r.shape(0); ++i){
        for (ssize_t j = 0; j < r.shape(1); ++j){
            for (ssize_t k = 0; k < r.shape(2); ++k){
                v = r(i, j, k);

                if (mapping.count(v) > 0){
                    r(i, j, k) = mapping[v];
                }
            }
        }
    }

    return d;
}


template <typename T>
using dual_map = std::unordered_map<T, std::unordered_map<T,T>>;

const char* relabel_paired_data__doc__ = R"/(
Relabel data according to a combination of values in-place.

Map each entry of a data volume (d1) according to the combination
of values within two separate arrays. This can be useful for
splitting segments by overlap, among other things.

Args:
    d1 (3darray<T>): Primary data volume to be modified.
    d2 (3darray<T>): Secondary data volume for indexing mapping.
    mapping (dict<T,dict<T,T>>): A mapping from data values in the original
        volume to another mapping from secondary values to desired values.

Returns:
    3darray<T> : The primary data volume with desired values replaced
)/";
template<typename T>
py::array_t<T> relabel_paired_data(py::array_t<T> d1, py::array_t<T> d2,
                                   dual_map<T> map)
{
  auto r1 = d1.template mutable_unchecked<3>();
  auto r2 = d2.template unchecked<3>();

  assert(r1.shape(0)==r2.shape(0));
  assert(r1.shape(1)==r2.shape(1));
  assert(r1.shape(2)==r2.shape(2));

  T v1, v2;

  for (ssize_t i = 0; i < r1.shape(0); ++i){
    for (ssize_t j = 0; j < r1.shape(1); ++j){
      for (ssize_t k = 0; k < r1.shape(2); ++k){
        v1 = r1(i, j, k);
        v2 = r2(i, j, k);

        if (v1 != 0){
          r1(i, j, k) = map[v1][v2];
        }
      }
    }
  }

  return d1;
}


PYBIND11_MODULE(_relabel, m) {
    m.def("relabel_data", &relabel_data<unsigned int>);
    m.def("relabel_data", &relabel_data<float>,
          relabel_data__doc__);

    m.def("relabel_paired_data", &relabel_paired_data<unsigned int>);
    m.def("relabel_paired_data", &relabel_paired_data<float>,
          relabel_paired_data__doc__);
}
