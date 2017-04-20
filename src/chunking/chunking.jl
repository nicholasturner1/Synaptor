module ChunkBounds


using ..BBoxes


"""

    chunk_bounds(vol_size, chunk_size [,offset])

  Computes the index bounds for splitting a volume
  into chunks of a maximum size. If the dimensions
  don't match to allow for perfect splitting, smaller
  chunks are included at the end of each such dimension.
"""
function chunk_bounds(vol_size, chunk_size, offset=0)

  x_bounds = bounds1D(vol_size[1], chunk_size[1])
  y_bounds = bounds1D(vol_size[2], chunk_size[2])
  z_bounds = bounds1D(vol_size[3], chunk_size[3])

  bounds = Array{BBoxes.BBox}(length(x_bounds), 
                              length(y_bounds), 
                              length(z_bounds))
  sx,sy,sz = size(bounds)

  for z in 1:sz, y in 1:sy, x in 1:sx

    xb, yb, zb = x_bounds[x], y_bounds[y], z_bounds[z]
    bounds[x,y,z] = BBoxes.BBox(xb.first, yb.first, zb.first,
                                xb.second,yb.second,zb.second) + offset

  end

  bounds
end


"""

    bounds1D(full_width, step_size)

  Returns the 1D index bounds for splitting an interval
  of a given width into increments of a given step size.
  Includes smaller increments at the end if the interval
  isn't evenly divided.
"""
function bounds1D(full_width, step_size)

  @assert step_size > 0
  @assert full_width > 0

  start = 1
  ending = step_size

  num_bounds = round(Int,ceil(full_width / step_size));
  bounds = Vector{Pair{Int,Int}}(num_bounds)

  i = 1
  while ending < full_width
    bounds[i] = start => ending

    i+=1; start += step_size; ending += step_size;
  end

  bounds[end] = start => full_width

  bounds
end


end #module Chunking
