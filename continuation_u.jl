#!/usr/bin/env julia

module continuation_u

type Continuation{T}
  segid :: T
  num_voxels :: Int # 0 = COM not computed yet
  center_of_mass :: Vector{Int} # [0,0,0] = COM not computed yet
  face_axis :: UInt8
  low_face :: Bool
  cont_voxels :: Vector{Vector{Int}}
  overlaps :: Dict{T,Int} # Dict() = no overlaps yet
  overlap_semantics :: Dict{T,UInt8} # Dict() = no overlaps yet
end

export seg_ids

#dummy for testing
dummy_cont_vox = Vector{Vector{Int}}()
push!(dummy_cont_vox,[1,1,1])
Continuation() = Continuation(1,5,[1,1,1],UInt8(1),
                              true,dummy_cont_vox,Dict(1=>5),Dict(1=>UInt8(2)))

function segids{T}(c_list::Vector{Continuation{T}})
  Set([ c.segid for c in c_list ])
end


function update_sizes!{T}( c_list::Vector{Continuation{T}}, sizes )
  for c in c_list c.num_voxels = sizes[c.segid] end
end

function update_locs!{T}( c_list::Vector{Continuation{T}}, locs )
  for c in c_list c.center_of_mass = locs[c.segid] end
end


type ContinuationArray{T}
  arr :: Array{Vector{Continuation{T}}}
end

function ContinuationArray(T, size)
  a = Array(Vector{Continuation{T}},size)
  for i in eachindex(a) a[i] = [] end
  ContinuationArray(a)
end

Base.getindex( ca::ContinuationArray, idxes... ) = ca.arr[idxes...]
Base.setindex!( ca::ContinuationArray, v, idxes... ) = setindex!(ca.arr, v, idxes...)
Base.append!( ca::ContinuationArray, c_list, idxes... ) = append!(ca[idxes...], c_list)
Base.size( ca::ContinuationArray ) = size(ca.arr)
Base.eachindex( ca::ContinuationArray ) = eachindex(ca.arr)

"""

    find_chunk_continuations( ca::ContinuationArray, current_chunk_index )

  Compiles the list of continuations which apply to the current chunk
"""
function find_continuations_to_apply{T}( ca::ContinuationArray{T}, current_chunk_index )

  c_arr_size = collect(size(ca))
  continuations_to_apply = Vector{Continuation{T}}();

  for axis in 1:3, low_face in (true,false)

    sender_index = copy(current_chunk_index)
    if low_face
      sender_index[axis] -= 1
    else
      sender_index[axis] += 1
    end

    #boundary checks
    if  low_face && sender_index[axis] == 0 continue end
    if !low_face && sender_index[axis] > c_arr_size[axis] continue end

    sender_continuations = ca[sender_index...]

    #continuations which apply to this chunk have the same axis, and opposite 
    # "low_face" value
    new_conts = filter_conts_for_face( sender_continuations, axis, !low_face )

    append!(continuations_to_apply, new_conts)
  end
  
  continuations_to_apply
end


"""

    filter_conts_for_face( c_list::Vector{Continuation{T}}, axis, low_face )
"""
@inline function filter_conts_for_face{T}( c_list::Vector{Continuation{T}}, axis, low_face)
  filter( x -> x.face_axis == axis && x.low_face == low_face, c_list )
end


"""

    update_continuations!{T}( segment_volume::Array{T,3},
                                   progress_arr::Array{Bool,3},
                                   current_chunk_index )

  Documentation soon...
"""
function find_new_continuations{T}( segment_volume::Array{T,3}, chunk_arr_size, 
                                    current_chunk_index )

  chunk_continuations = Vector{Continuation{T}}();
  
  for axis in 1:3, low_face in (true,false)

    propagation_index = copy(current_chunk_index)
    if low_face
      propagation_index[axis] -= 1
    else
      propagation_index[axis] += 1
    end

    #boundary checks
    if  low_face && propagation_index[axis] == 0 continue end
    if !low_face && propagation_index[axis] > chunk_arr_size[axis] continue end

    new_conts = find_face_continuations( segment_volume, axis, low_face )

    append!(chunk_continuations, new_conts)
  end

  chunk_continuations
end


"""

    find_face_continuations{T}( vol::Array{T,3}, axis, low_face )

  Documentation soon...
"""
function find_face_continuations{T}( vol::Array{T,3}, axis, low_face )

  sx,sy,sz = size(vol)
  sizes = [sx,sy,sz]

  idxes = Vector(3)
  idxes[1] = 1:sx; idxes[2] = 1:sy; idxes[3] = 1:sz;
  if low_face
    idxes[axis] = 1
  else
    idxes[axis] = idxes[axis].stop
  end
  
  bvs = find_boundary_voxels(vol, idxes)

  continuations = Vector{Continuation{T}}();

  for (segid,voxels) in bvs

    if low_face
      #implicitly assumes that the chunks are the same size
      for i in eachindex(voxels) voxels[i][axis] = -1 end
    else
      #this is fine
      for i in eachindex(voxels) voxels[i][axis] = 1 end
    end

    c = Continuation( segid, 0, [0,0,0], UInt8(axis), low_face, 
                      voxels, Dict{T,Int}(), Dict{T,UInt8}() )

    push!(continuations, c)
  end

  continuations
end


"""

    find_boundary_voxels{T}( vol::Array{T,3}, idxes )

  Traverses a volume using the {Range,Int,Colon} array passed
  and records where nonzero values exist. Returns a mapping from
  nonzero value to its voxels within the specified indices.
"""
function find_boundary_voxels{T}( vol::Array{T,3}, idxes )

  boundary_voxels = Dict{T,Vector{Vector{Int}}}()

  zT = T(0)
  for z in idxes[3], y in idxes[2], x in idxes[1]

    segid = vol[x,y,z];
    if segid == zT continue end

    if !haskey(boundary_voxels,segid) boundary_voxels[segid] = [] end

    push!(boundary_voxels[segid],[x,y,z])
  end

  boundary_voxels
end


"""
"""
function consolidate_continuations( ca::ContinuationArray, to_merge )

  collected = collect_continuations(ca)

  mg = find_merge_graph(to_merge)

  ccs = find_connected_components(mg)

  consolidated = merge_components(consolidated)

  edges = filter_results

  locs = centers_of_mass(consolidated)

end

function collect_continuations( ca::ContinuationArray )
  0#stub
end

function find_merge_graph(to_merge)
  0#stub
end

function find_connected_compontned(merge_graph)
  0#stub
end

function merge_components(consolidated)
  0#stub
end

function filter_results(consolidated)
  0#stub
end

function centers_of_mass(consolidated)
  0#stub
end

end #module
