#!/usr/bin/env julia
__precompile__()

#=
  Segmentation Utilities - seg_u.jl
=#
module seg_u

export centers_of_mass
export dilate_by_k
export segment_sizes, filter_segments_by_size!
export connected_components3D
export count_overlapping_labels
export filter_segments_by_ids!


"""

    segment_sizes( seg::Array )

  Returns a Dict from segment id to the size of each segment.
  Ignores the zero segment
"""
function segment_sizes{T}( seg::Array{T} )

  counts = Dict{T,Int}();

  z = zero(T)
  for i in eachindex(seg)
    if seg[i] == z continue end

    counts[seg[i]] = get(counts, seg[i], 0) + 1
  end

  counts
end


"""

    count_overlapping_labels( d, labels, max_label=nothing )

  Returns a sparse matrix representing the overlap matrix
  between the two passed segmentations.

  It can be useful to extend the sparse matrix to include
  more indices than supplied within the labels (e.g. to
  keep this dimension of the sparse matrix consistent).
  Passing a max_label value forces the label dimension to
  include values up to the passed value.

  Ignores the zero segment for both d and labels
"""
function count_overlapping_labels( d, labels, max_label=nothing )

  #ignoring zero segment
  maxd = round(Int,maximum(d)); maxl = round(Int,maximum(labels));

  if max_label == nothing
    counts = spzeros(Int, maxd, maxl);
  else
    counts = spzeros(Int, maxd, max_label);
  end

  zv = eltype(d)(0)
  zl = eltype(labels)(0)
  for i in eachindex(d)

    val = d[i]
    lab = labels[i]

    if val == zv continue end
    if lab == zl continue end

    counts[ val, lab ] += 1

  end

  counts
end


"""

    connected_components3D( d, thresh )

  Performs connected components over d using a high-pass threshold.
"""
function connected_components3D{T}( d::Array{T}, thresh=zero(T) )

  #true => don't connect me
  masked = d .<= T(thresh)
  res = zeros(Int, size(d));

  fill_in_new_components!( res, masked, 1 )

  res
end


"""

    fill_in_new_components!{T}( d::Array{T}, masked, next_id )

  Connect any components from masked. It's implied (but not assumed)
  that other components have already been filled in from continuations.
"""
function fill_in_new_components!{T}( d::Array{T}, masked, next_id )

  @assert size(masked) == size(d)

  xmax, ymax, zmax = size(d)

  for z in 1:zmax, y in 1:ymax, x in 1:xmax
    @inbounds if masked[x,y,z] continue end
    assign_component!(d, masked,x,y,z, next_id)
    next_id += 1
  end

  next_id
end


"""

    assign_component!( arr, masked, xstart, ystart, zstart, segid )

  Traverses the component connected to the start index, and assigns the
  values within the component to segid. Uses a depth first strategy.
"""
function assign_component!{T}(arr::Array{T}, masked::BitArray{3},
  xstart,ystart,zstart, segid)

  xmax, ymax, zmax = size(masked)
  to_explore = Tuple{Int,Int,Int}[(xstart, ystart, zstart)]
  explored   = Tuple{Int,Int,Int}[];
  #explored = Set{Tuple{Int,Int,Int}}();

  @inbounds while !isempty(to_explore)

    x,y,z = pop!(to_explore)
    push!(explored, (x,y,z))

    arr[x,y,z] = segid
    masked[x,y,z] = true

    if x > 1 && !masked[ x-1,  y, z ] push!( to_explore, (x-1,y,z) ) end
    if y > 1 && !masked[ x,  y-1, z ] push!( to_explore, (x,y-1,z) ) end
    if z > 1 && !masked[ x,  y, z-1 ] push!( to_explore, (x,y,z-1) ) end

    if x < xmax && !masked[ x+1, y, z ] push!( to_explore, (x+1,y,z) ) end
    if y < ymax && !masked[ x, y+1, z ] push!( to_explore, (x,y+1,z) ) end
    if z < zmax && !masked[ x, y, z+1 ] push!( to_explore, (x,y,z+1) ) end

  end

  #don't think I need this anymore...
  #Set(explored)
end


"""

    connected_component3D( d, seed::Tuple{Int,Int,Int}, thresh=zero(T) )

  Fills out a single connected component seeded at the passed location
"""
function connected_component3D{T}( d::Array{T}, seed::Tuple{Int,Int,Int}, thresh=zero(T) )

  masked = d .<= T(thresh)

  component_vol = zeros(UInt8, size(d))
  x,y,z = seed

  component_voxels = assign_component!(component_vol, masked, x,y,z, 1)

  component_vol, component_voxels
end


"""

    connected_component3D!( d, seed::Tuple{Int,Int,Int}, vol::Array{UInt8}, masked::BitArray, thresh=zero(T) )

  Fills out a single connected component seeded at the passed location
  using a pre-allocated volume and mask.

  This didn't speed things up somehow...
"""
function connected_component3D!{T}( d::Array{T}, seed::Tuple{Int,Int,Int}, vol::Array{UInt8}, masked::BitArray, thresh=zero(T) )

  for i in eachindex(d)
    masked[i] = d[i] <= T(thresh)
  end

  fill!(vol,zero(T))
  x,y,z = seed

  assign_component!( vol, masked, x,y,z, 1 )
end


"""

    fill_in_connected_components( d::Array{T}, next_id, continuation_list, cc_thresh )

  Continues filling in a chunk of connected components, starting with any segments continued
  from other chunks.
"""
function fill_in_connected_components{T}( d::Array{T}, next_id, continuation_list, thresh )
  
  masked = d .<= T(thresh)
 
  component_vol = zeros(UInt32,size(d))

  to_merge = fill_in_continuation_components!( component_vol, masked, continuation_list )

  next_id = fill_in_new_components!( component_vol, masked, next_id )

  component_vol, next_id, to_merge
end


"""

    fill_in_continuation_components!{T}( component_vol, masked, continuation_list )

  Fills in the components that are connected to other chunks. These are specified by
  a list of continuations.
"""
function fill_in_continuation_components!{T}( component_vol::Array{T}, masked, continuation_list )

  szs = size(component_vol)
  to_merge = Vector{Tuple{T,T}}()
  z = T(0)

  for continuation in continuation_list, vx in continuation.cont_voxels

    #translating a '-1' index to the max of the chunk    
    v = [vx[1],vx[2],vx[3]]
    for i in eachindex(v)
      if v[i] == -1 v[i] = szs[i] end
    end

    comp_val = component_vol[v[1],v[2],v[3]]

    if comp_val == z
      if masked[v[1],v[2],v[3]] continue end

      assign_component!( component_vol, masked, v[1],v[2],v[3], 
                                 continuation.segid )
      continue
    end

    #if we're here, then the value at the voxel shouldn't be masked
    if comp_val == continuation.segid continue end

    push!(to_merge, (comp_val, continuation.segid))

  end

  to_merge 
end


"""

    manhattan_distance2D!( d )

  Performs a 2D manhattan distance transformation over
  a 3D volume inplace.
"""
function manhattan_distance2D!{T}( d::Array{T,3} )

  restype = UInt32
  maxx, maxy, maxz = size(d)
  dists = zeros(restype, size(d))

  for k in 1:maxz
    for j in 1:maxy
      for i in 1:maxx

        if  d[i,j,k] > T(0)
           dists[i,j,k] = 0
        else
           dists[i,j,k] = typemax(restype)
        end

        if i>1  &&  dists[i-1,j,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i-1,j,k]+1;
          d[i,j,k] = d[i-1,j,k];
        end
        if j>1  &&  dists[i,j-1,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i,j-1,k]+1;
          d[i,j,k] = d[i,j-1,k];
        end

        #for 3d case
        #if k>1  dists[i,j,k] = minimum(( dists[i,j,k], dists[i,j,k-1]+1 )) end

      end
    end
  end

  for k in maxz:-1:1
    for j in maxy:-1:1
      for i in maxx:-1:1

        if i<maxx  &&  dists[i+1,j,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i+1,j,k]+1;
          d[i,j,k] = d[i+1,j,k];
        end
        if j<maxy  &&  dists[i,j+1,k]+1 <= dists[i,j,k]
          dists[i,j,k] = dists[i,j+1,k]+1;
          d[i,j,k] = d[i,j+1,k];
        end
        #if k<maxz  dists[i,j,k] = minimum(( dists[i,j,k], dists[i,j,k+1]+1 )) end

      end
    end
  end

  dists
end


"""

    dilate_by_k!( d, k )

  Dilates the segments within d by k
  in 2D manhattan distance
"""
function dilate_by_k!( d, k )

  md = manhattan_distance2D!(d)

  for i in eachindex(d)
    if md[i] > k
      d[i] = eltype(d)(0)
    end
  end

end


"""

    filter_segments_by_size!( d, thresh )

  Traverses a volume, and removes segments less than or equal to
  the threshold value in size
"""
function filter_segments_by_size!( d, thresh )

  sizes = segment_sizes(d)

  to_keep = Vector{eltype(keys(sizes))}()

  for (segid,size) in sizes
    if size > thresh push!(to_keep, segid) end
  end
  if length(to_keep) == 0 warn("no segments remaining after size threshold") end

  for i in eachindex(d)
    if !(d[i] in to_keep)
      d[i] = eltype(d)(0)
    end
  end

end


"""

    centers_of_mass( seg )

  Finds the (rounded) center of mass coordinate for each segment within
  a segmentation volume
"""
function centers_of_mass( d )

  centers_of_mass = Dict{eltype(d),Vector}();
  sizes = Dict{eltype(d),Int}()

  maxx, maxy, maxz = size(d)
  for k in 1:maxz
    for j in 1:maxy
      for i in 1:maxx

        segid = d[i,j,k];
        if segid == 0 continue end

        centers_of_mass[segid] = get(centers_of_mass, segid, [0,0,0]) + [i,j,k];
        sizes[segid] = get(sizes, segid, 0) + 1;

      end
    end
  end

  for k in keys(centers_of_mass)
    centers_of_mass[k] = round(Int, centers_of_mass[k] / sizes[k] );
  end

  centers_of_mass
end


"""

    filter_segments_by_ids!( seg, ids )

  Only keeps the segments within ids
"""
function filter_segments_by_ids!( seg, ids )

  z = eltype(seg)(0)
  for i in eachindex(seg)
    if seg[i] == z continue end
    if seg[i] in ids continue end
    seg[i] = z
  end

end

"""

    filter_out_segments_by_ids!( seg, ids )

  Zeros the segments with id within ids from the volume
"""
function filter_out_segments_by_ids!( seg, ids )

  z = eltype(seg)(0)
  for i in eachindex(seg)
    if seg[i] == z continue end
    if seg[i] in ids seg[i] = z end
  end

end

end#module
