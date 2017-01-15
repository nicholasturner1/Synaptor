#!/usr/bin/env julia
__precompile__()


module chunk_u

#=
   Chunking Utilities - chunk_u.jl
=#
#import H5Array

export fetch_chunk
export chunk_bounds
export fetch_inspection_window
export init_inspection_window, fill_inspection_window!
export fetch_inspection_block
export bounds, intersect_bounds

export vol_shape


@inline function zip_bounds( bounds::Pair )

  #need Any for possible Colon()s
  dbz = Vector{Any}(length(bounds.first))

  for i in eachindex(bounds.first)
    bz[i] = bounds.first[i]:bounds.second[i]
  end

  bz
end
"""

    vol_shape( bounds )

  Returns the overall shape of a subvolume which ranges
  between the two coordinates contained within the Pair bounds.
"""
function vol_shape( bounds::Pair )
  bounds.second - bounds.first + 1
end

"""

    fetch_chunk( d, bounds::Pair, offset )

  Generalized function to fetch a 3d chunk
  from within an Nd Array, H5Dataset, etc.
"""
function fetch_chunk( d, bounds::Pair, offset=[0,0,0] )

  shifted = (bounds.first  + offset) => (bounds.second + offset);
  zipped = zip_bounds(shifted)

  while length(zipped) < length(size(d)) push!(zipped,Colon())

  d[zipped...]
end


type BoundArray
  arr :: Array{Pair{Vector{Int},Vector{Int}}}
end


function BoundArray(vol_size, chunk_size, offset=[0,0,0])

  x_bounds = bounds1D( vol_size[1], chunk_size[1] )
  y_bounds = bounds1D( vol_size[2], chunk_size[2] )
  z_bounds = bounds1D( vol_size[3], chunk_size[3] )

  sx,sy,sz = length(x_bounds), length(y_bounds), length(z_bounds)
  a = Array{Pair{Vector{Int},Vector{Int}}}(sx,sy,sz)

  for z in 1:sz, y in 1:sy, x in 1:sx
    xb, yb, zb = x_bounds[x], y_bounds[y], z_bounds[z]
    a[x,y,z] = ([xb.first,  yb.first,  zb.first] + offset =>
                [xb.second, yb.second, zb.second] + offset)
  end

  BoundArray(a)
end

Base.getindex( ba::BoundArray, idxes... ) = ba.arr[idxes...];
Base.setindex!( ba::BoundArray, v, idxes... ) = setindex!(ba.arr, v, idxes...)
Base.size( ba::BoundArray, dim... ) = size(ba.arr, dim...)
Base.size( ba::BoundArray ) = size(ba.arr)
Base.eachindex( ba::BoundArray ) = eachindex(ba.arr)
Base.start( ba::BoundArray ) = start(ba.arr)
Base.next( ba::BoundArray, st ) = next(ba.arr, st)
Base.done( ba::BoundArray, st ) = done(ba.arr, st)
Base.eltype( ba::BoundArray ) = eltype(ba.arr)
Base.length( ba::BoundArray ) = length(ba.arr)


"""
    chunk_bounds( vol_size, chunk_size )

  Computes the index bounds for splitting a volume
  into chunks of a maximum size. If the dimensions
  don't match to allow for perfect splitting, smaller
  chunks are included at the end of each dimension.
"""
function chunk_bounds( vol_size, chunk_size, offset=[0,0,0] )

  x_bounds = bounds1D( vol_size[1], chunk_size[1] )
  y_bounds = bounds1D( vol_size[2], chunk_size[2] )
  z_bounds = bounds1D( vol_size[3], chunk_size[3] )

  num_bounds = prod(
    (length(x_bounds), length(y_bounds), length(z_bounds))
    )
  bounds = Vector{Pair{Vector{Int},Vector{Int}}
                 }(num_bounds)
  i=0;

  for z in z_bounds
    for y in y_bounds
      for x in x_bounds
        i+=1;
        bounds[i] = [x.first,  y.first,  z.first] + offset =>
                    [x.second, y.second, z.second] + offset
      end
    end
  end

  bounds
end

"""

    bounds1D( full_width, step_size )

  Returns the 1D index bounds for splitting an interval
  of a given width into increments of a given step size.
  Includes smaller increments at the end if the interval
  isn't evenly divided
"""
function bounds1D( full_width, step_size )

  @assert step_size > 0
  @assert full_width > 0

  start = 1
  ending = step_size

  num_bounds = convert(Int,ceil(full_width / step_size));
  bounds = Vector{Pair{Int,Int}}( num_bounds )

  i=1;
  while ending < full_width
    bounds[i] = start => ending

    i += 1;
    start  += step_size
    ending += step_size
  end

  #last window for remainder
  bounds[end] = start => full_width

  bounds
end

"""
    fetch_inspection_window( dset, coord )

  Extracts a window from a dataset of all the existing
  coordinates within some radius of the given coordinate (rounded up).
  Returns the window of data, as well as the offset of the
  window indices from those of the original dataset.
"""
function fetch_inspection_window( dset, coord, radius, bounds=nothing )

  coord = collect(coord) #translating from tuple to array

  beg_candidate = coord - radius;
  end_candidate = coord + radius;

  #limiting the indexing to specific bounds
  # (used for making matching volumes)
  if bounds != nothing
    beg_allowed = bounds.first
    end_allowed = bounds.second
  else
    beg_allowed = [1,1,1]
    end_allowed = [size(dset)...]
  end

  beg_i = max( beg_allowed, beg_candidate );
  end_i = min( end_allowed, end_candidate );

  #rel_coord = coord - beg_i;

  fetch_chunk( dset, beg_i=>end_i, [0,0,0] ), beg_i-1
end


"""

    fill_inspection_window!( window, dset, coord, radius, bounds=nothing )

  Fills a passed window of data with the values within a radius
  of the passed coordinate (rounded up). If the amount of these
  values is less than the dimensions of the data window, the
  first indices are filled.
"""
function fill_inspection_window!( window, dset, coord, radius, bounds=nothing )

  coord = collect(coord) #translating from tuple to array

  beg_candidate = coord - radius;
  end_candidate = coord + radius;

  #limiting the indexing to specific bounds
  # (used for making matching volumes)
  if bounds != nothing
    beg_allowed = bounds.first
    end_allowed = bounds.second
  else
    beg_allowed = [1,1,1]
    end_allowed = [size(dset)...]
  end

  beg_i = max( beg_allowed, beg_candidate );
  end_i = min( end_allowed, end_candidate );

  #rel_coord = coord - beg_i;
  window_size = end_i - beg_i + 1

  fill!( window, eltype(window)(0) )

  window[
    1:window_size[1],
    1:window_size[2],
    1:window_size[3]
    ] = dset[
    beg_i[1]:end_i[1],
    beg_i[2]:end_i[2],
    beg_i[3]:end_i[3]];

  return beg_i-1;
end


"""

    init_inspection_window( radius, dtype )

  Initializes a window of data of a given radius around a central
  pixel (rounded up). Intended to be used in combination with
  fill_inspection_window! above.
"""
function init_inspection_window( radius, dtype )
  zeros( dtype, (2*radius + 1)... )
end


"""

    fetch_inspection_block( vol, scan_bounds::Pair, scan_offset,
                            window_radius, bounds )

  Extracts the union of all possible inspection windows reachable
  from a scan window within the given bounds.
"""
function fetch_inspection_block( vol, scan_bounds, scan_offset,
  window_radius, bounds )

  scan_shape = scan_bounds.second - scan_bounds.first + 1;
  scan_radius = round(Int, ceil(scan_shape / 2))


  block_radius = scan_radius + window_radius


  scan_midpoint = scan_bounds.first + scan_radius - 1;
  scan_midpoint_global = scan_midpoint + scan_offset;


  fetch_inspection_window( vol, scan_midpoint_global,
                         block_radius, bounds )
end


"""

    bounds( d, offset=[0,0,0] )

  Extracts the index bounds for general purpose objects
  which have size and a given offset
"""
function bounds( d, offset=[0,0,0] )
  offset + 1 => collect(size(d)[1:3]) + offset
end


"""

    intersect_bounds( bounds1, bounds2, bounds2_offset )

  Takes two index bounds defined by Pairs and returns their
  intersection. Performs no checking for validity of the result
  (i.e. the result can specify bounds with 0 or negative volume).
"""
function intersect_bounds( bounds1, bounds2, bounds2_offset )
  b1_beg, b1_end = bounds1
  b2_beg = bounds2.first  + bounds2_offset
  b2_end = bounds2.second + bounds2_offset

  max( b1_beg, b2_beg ) => min( b1_end, b2_end )
end

end#module
