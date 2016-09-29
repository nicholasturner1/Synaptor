
__precompile__()

module vol_u

export relabel_data!, ids_at_coords
#----------------------------
"""
    relabel_data!( dset, mapping )

Take a dataset array, and map its values in-place based on
an associative array.
"""
function relabel_data!{T}( dset::Array{T}, mapping )

  for i in eachindex(dset)

    v = dset[i]
    if v == 0 continue end

    dset[i] = get( mapping, v, v );

  end #for
end

"""
    ids_at_coords( dset, coords )

  Return a 1d array of the values at each coordinate
from an iterable of iterables (yo dawg...).
"""
function values_at_coords{T}( dset::Array{T}, coords )

  values = zeros( T, (length(coords),) );

  for (i, coord) in enumerate(coords)
    values[i] = dset[ coord... ];
  end

  return values;
end

"""
    keys_to_coords( dset, coords )

  Take a map of keys to coordinates, return
another dict of keys to values at those coordinates
"""
function keys_to_coords{T}( dset::Array{T}, coord_map )

  values = Dict{ eltype(keys(coord_map)), T }();

  for (k, coord) in coord_map
    values[k] = dset[ coord... ];
  end

  return values;
end


"""
"""
function bounds1d( full_width, step_size )

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
    chunk_bounds(vol_size, chunk_size)
"""
function chunk_bounds( vol_size, chunk_size )

  x_bounds = bounds1d( vol_size[1], chunk_size[1] )
  y_bounds = bounds1d( vol_size[2], chunk_size[2] )
  z_bounds = bounds1d( vol_size[3], chunk_size[3] )

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
        bounds[i] = [x.first,  y.first,  z.first] =>
                    [x.second, y.second, z.second]
      end
    end
  end

  bounds
end


function prep_index( indices, vol_bounds )

  vol_beg, vol_end = vol_bounds
  @assert length(indices) == length(vol_end)

  index_range = Pair{Vector{Int},Vector{Int}}([],[]);

  for (i,index) in enumerate(indices)

    if isa(index, Colon)
      push!(index_range.first,  vol_beg[i] );
      push!(index_range.second, vol_end[i] );

    elseif isa(index, Range)
      push!(index_range.first,  start(index) );
      push!(index_range.second, last(index)  );

    elseif isa(index, Int)
      push!(index_range.first,  index );
      push!(index_range.second, index );

    end #if

  end #for

  index_range
end

function in_bounds( bounds, shape )

  b_beg, b_end = bounds;
  s_beg, s_end = shape;

  ( minimum( b_beg .>= s_beg ) &&
    minimum( b_end .<= s_end ) )
end


function find_overlap( indices, bounds )

  if isa(bounds,Array) #instead of a Pair
    bounds = Pair( [1 for i in 1:length(bounds)], bounds)
  end

  @assert length(indices.first)  == length(bounds.first)
  @assert length(indices.second) == length(bounds.second)

  i_beg, i_end = indices;
  b_beg, b_end = bounds;

  if maximum(i_end .< b_beg) || maximum(i_beg .> b_end) return (-1=>-1,-1=>-1) end

  #result bounds in the global space
  res_beg = max( b_beg, i_beg );
  res_end = min( b_end, i_end );

  if maximum( res_beg .> res_end ) return (-1=>-1,-1=>-1) end

  #bounds relative to "bounds" argument
  rel_beg = res_beg - b_beg + 1;
  rel_end = res_end - b_beg + 1;

  #where this maps within the result
  out_beg = res_beg - i_beg + 1;
  out_end = res_end - i_beg + 1;

  ( Pair( rel_beg, rel_end ),
    Pair( out_beg, out_end ) )
end



#----------------------------
end #end module
