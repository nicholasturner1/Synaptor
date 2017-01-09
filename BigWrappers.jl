#!/usr/bin/env julia

module BigWrappers

using BigArrays.H5sBigArrays

export BigWrapper, init, bounds

type BigWrapper
  dirname:: AbstractString
end

function Base.getindex(bw::BigWrapper, idxes::Union{UnitRange, Int, Colon}...)
  println("getindex call")
  ba = H5sBigArray(bw.dirname)
  ba[idxes...]
end


function Base.size(bw::BigWrapper)
  println("size call")
  ba = H5sBigArray(bw.dirname)
  size(ba)
end

function init(bw::BigWrapper)
  H5sBigArray(bw.dirname)
end

function bounds(bw::BigWrapper, offset=[0,0,0])
  ba = H5sBigArray(bw.dirname)
  bs = boundingbox(ba)
  b = Int[v for v in bs.start][1:3] + offset
  e = Int[v for v in bs.stop][1:3] + offset
  b => e
end

end#module
