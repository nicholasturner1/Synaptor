#!/usr/bin/env julia
__precompile__()

#=
  Fairly Inflexible type for reading a dir of h5 chunks - H5Arr.jl
=#
module H5Array


export H5Array, bounds


include("vol_u.jl")
import HDF5

import Base: getindex, size


type H5Arr{T <: Real}

  filenames::Array{AbstractString}
  #bounds of each file within some global space
  file_bounds::Array{ Pair{Vector{Int},Vector{Int}} }

  dset_name::AbstractString

  shape::Pair{Vector{Int},Vector{Int}}

end


""" janky constructor """
function create_h5arr( filenames::Array{String,1}, bounds, dset_name, eltype::DataType )

  vol_start = [typemax(Int),typemax(Int),typemax(Int)]
  vol_end = [0,0,0]

  for bound in bounds
    vol_start = min(vol_start, bound.first)
    vol_end = max(vol_end, bound.second)
  end
  shape = vol_start => vol_end

  num_vols = extract_4d_shape( filenames[1], dset_name )

  if num_vols > 1
    push!(shape.first, 1)
    push!(shape.second, num_vols)
  end

  H5Arr{eltype}( filenames, bounds, dset_name, shape )
end


"""

    extract_4d_shape( filename, dset_name )

  Finds the number of 3d volumes (4th dim length)
  from an h5 dataset.
"""
function extract_4d_shape( filename, dset_name )

  f = HDF5.h5open(filename)
  d = f[dset_name]

  s = size(d)
  if length(s) < 4
    return 1
  elseif length(s) == 4
    return s[4]
  else
    println("WARNING: more than 4 dimensions!")
    return s[4]
  end
end


"""

    getindex( A::H5Arr, indices::Union{Colon,Range{Int},Int}... )

  Reads stuff
"""
function getindex( A::H5Arr, indices::Union{Colon,Range{Int},Int}... )

  shape3d = A.shape.first[1:3] => A.shape.second[1:3]
  @assert length(indices) == length(shape3d.second)

  bounds = vol_u.prep_index( indices, shape3d )

  @assert vol_u.in_bounds( bounds, shape3d )

  to_read = Vector{Tuple{Int,Tuple}}();

  for (i,bound) in enumerate( A.file_bounds )

    overlap = vol_u.find_overlap(bounds, bound)

    if overlap[1] != (-1=>-1) #match found
      push!(to_read, (i, overlap))
    end

  end

  # @time read_and_map( A, bounds, to_read )
  read_and_map( A, bounds, to_read )
end


size( A::H5Arr ) = A.shape.second - A.shape.first + 1


function bounds( A, offset=[0,0,0] )
  (A.shape.first[1:3] + offset) => (A.shape.second[1:3] + offset)
end


"""

    read_and_map{T}( A::H5Arr{T}, indices, to_read )

  Determines which chunks to reads, and then maps
  the values to a volume of the proper size
"""
function read_and_map{T}( A::H5Arr{T}, indices, to_read )

  output_shape = collect(indices.second) - collect(indices.first) + 1

  if length(A.shape.second) > 3 push!(output_shape, A.shape.second[4]) end
  output = zeros( T, output_shape... );

  for (file_index, bounds) in to_read

    println("Reading chunk $(file_index)")
    chunk = read_chunk( A.filenames[file_index], A.dset_name, bounds[1] )

    output_beg, output_end = bounds[2]
    if length(A.shape.second) > 3
      output[ output_beg[1]:output_end[1],
              output_beg[2]:output_end[2],
              output_beg[3]:output_end[3],
              : ] = chunk
    else
      output[ output_beg[1]:output_end[1],
              output_beg[2]:output_end[2],
              output_beg[3]:output_end[3]
            ] = chunk
    end

  end

  output
end


"""

    read_chunk( filename, dset_name, bounds )

  Reads the data within the specified bounds from a specific
  chunk dataset
"""
function read_chunk( filename, dset_name, bounds )

  read_beg, read_end = bounds

  f = HDF5.h5open(filename)
  d = f[dset_name]

  if length(size(d)) > 3
    d[read_beg[1]:read_end[1],
              read_beg[2]:read_end[2],
              read_beg[3]:read_end[3],
              : ]
  else
    d[read_beg[1]:read_end[1],
              read_beg[2]:read_end[2],
              read_beg[3]:read_end[3]]
  end
end


end #module
