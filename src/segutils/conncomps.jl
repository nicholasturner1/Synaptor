
module ConnComps


export connected_components3D
export connected_component3D
export fill_in_connected_components!


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

end #module ConnComps
