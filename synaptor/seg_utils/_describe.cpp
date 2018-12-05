#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <tuple>
#include <math.h>

namespace py = pybind11;


template<typename T>
using coord_map = std::unordered_map<T, std::tuple<long, long, long>>;

const char* centers_of_mass__doc__ = R"/(
Compute local centroid coordinates.

Args:
    seg (3darray<T>): A segmentation volume.

Returns:
    dict<T, tuple<int, int, int>>: A mapping from segid to centroid.
)/";
template<typename T>
coord_map<T> centers_of_mass(py::array_t<T> seg)
{
    auto r = seg.template unchecked<3>();
    T v;

    std::unordered_map<T, long> xs, ys, zs, szs;

    for (ssize_t i = 0; i < r.shape(0); ++i){
        for (ssize_t j = 0; j < r.shape(1); ++j){
            for (ssize_t k = 0; k < r.shape(2); ++k){
                v = r(i, j, k);

                if (v == 0) continue;

                auto search = xs.find(v);
                if (search == xs.end()){
                    xs[v] = i;
                    ys[v] = j;
                    zs[v] = k;
                    szs[v] = 1;
                } else {
                    xs[v] += i;
                    ys[v] += j;
                    zs[v] += k;
                    szs[v] += 1;
                }
            }
        }
    }

    coord_map<T> res;
    float sz;
    for (const auto& p : xs) {
        sz = szs[p.first];
        res[p.first] = std::make_tuple(round(xs[p.first] / sz),
                                       round(ys[p.first] / sz),
                                       round(zs[p.first] / sz));
    }

    return res;
}


PYBIND11_MODULE(_describe, m) {
    m.def("centers_of_mass", &centers_of_mass<unsigned int>);
    m.def("centers_of_mass", &centers_of_mass<float>,
          centers_of_mass__doc__);
}
