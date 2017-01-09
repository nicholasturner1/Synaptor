#!/usr/bin/env julia

module continuation_u

using LightGraphs

type Continuation{T}
  segid :: T
  num_voxels :: Int # 0 = COM not computed yet
  center_of_mass :: Vector{Int} # [0,0,0] = COM not computed yet
  face_axis :: UInt8
  low_face :: Bool
  cont_voxels :: Vector{Vector{Int}}
  overlaps :: Dict # Dict() = no overlaps yet
  overlap_semantics :: Vector{Tuple{Int,Int}} # Dict() = no overlaps yet
end

Base.eltype{T}(c::Continuation{T}) = T

export segids

#dummy for testing
dummy_cont_vox = Vector{Vector{Int}}()
push!(dummy_cont_vox,[1,1,1])
Continuation() = Continuation(1,5,[1,1,1],UInt8(1),
                              true,dummy_cont_vox,Dict(1=>5),[(1,2)])

function segids{T}(c_list::Vector{Continuation{T}})
  Set([ c.segid for c in c_list ])
end


function update_sizes!{T}( c_list::Vector{Continuation{T}}, sizes )
  for c in c_list c.num_voxels = sizes[c.segid] end
end

function update_locs!{T}( c_list::Vector{Continuation{T}}, locs )
  for c in c_list c.center_of_mass = locs[c.segid] end
end

function update_overlaps!{T}( c_list::Vector{Continuation{T}}, overlap, semmap )
  for c in c_list
    seg_overlaps = overlap[c.segid,:]
    cs = find(seg_overlaps); vs = nonzeros(seg_overlaps)
    
    c.overlaps = Dict( cs[i]=> vs[i] for i in eachindex(cs) )
    c.overlap_semantics = [(cs[i], semmap[cs[i]]) for i in eachindex(cs)]
  end
end


type ContinuationArray{T}
  arr :: Array{Vector{Continuation{T}}}
end

function ContinuationArray(T, size)
  a = Array(Vector{Continuation{T}},size)
  for i in eachindex(a) a[i] = [] end
  ContinuationArray{T}(a)
end

Base.getindex( ca::ContinuationArray, idxes... ) = ca.arr[idxes...]
Base.setindex!( ca::ContinuationArray, v, idxes... ) = setindex!(ca.arr, v, idxes...)
Base.append!( ca::ContinuationArray, c_list, idxes... ) = append!(ca[idxes...], c_list)
Base.size( ca::ContinuationArray ) = size(ca.arr)
Base.size( ca::ContinuationArray, dim... ) = size(ca.arr,dim...)
Base.eachindex( ca::ContinuationArray ) = eachindex(ca.arr)
Base.start( ca::ContinuationArray ) = start(ca.arr)
Base.next( ca::ContinuationArray, st ) = next(ca.arr, st)
Base.done( ca::ContinuationArray, st ) = done(ca.arr, st)

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
      for i in eachindex(voxels) voxels[i][axis] = -1 end
    else
      for i in eachindex(voxels) voxels[i][axis] = 1 end
    end

    c = Continuation{T}( segid, 0, [0,0,0], UInt8(axis), low_face, 
                      voxels, Dict{T,Int}(), Vector{Tuple{Int,Int}}() )

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


dummy_ca = ContinuationArray(Int,(2,1))
cs = [Continuation() for i in 1:4]
cs[3].segid = 2; cs[4].segid = 3
cs[3].overlap_semantics = [(2,3)]
cs[4].overlap_semantics = [(1,2),(2,3)]
cs[3].overlaps = Dict( 2 => 3 )
cs[4].overlaps = Dict( 1=>2, 2=>3 )

dummy_ca[1] = [cs[1],cs[2]]
dummy_ca[2] = [cs[3],cs[4]]

"""
"""
function consolidate_continuations( ca::ContinuationArray, to_merge )

  collected = collect_continuations(ca)

  components = find_merge_components(to_merge)

  consolidated, mapping = merge_components!(collected, components)
  consolidated = collect(values(consolidated))

  edges, mapping = filter_results(consolidated, mapping)

  locs = centers_of_mass(consolidated)
  sizes = completed_sizes(consolidated)

  edges, locs, sizes, mapping
end

function collect_continuations{T}( ca::ContinuationArray{T} )
  
  collected = Dict{T,Continuation{T}}();

  for c_list in ca

    #collapsing multiple instances of a continuation with the
    # same segid to one
    cl = collect(values(Dict( c.segid => c for c in c_list )))
    for c in cl

      if !haskey(collected, c.segid) 
        collected[c.segid] = c
        continue
      end

      collected[c.segid] = merge(c, collected[c.segid])
    end
  end

  collected
end

function merge( c1::Continuation, c2::Continuation )

  added_size = c1.num_voxels + c2.num_voxels

  c2.center_of_mass = round(Int,(c1.center_of_mass * (c1.num_voxels / added_size)) +
                                (c2.center_of_mass * (c2.num_voxels / added_size)))

  for (k,v) in c1.overlaps
    if !haskey(c2.overlaps, k) c2.overlaps[k] = v
    else c2.overlaps[k] += v
    end
  end
    
  append!(c2.overlap_semantics, c1.overlap_semantics)

  c2
end

function find_merge_components(to_merge)
  
  segids = Set{Int}();

  for edge in to_merge
    push!(segids, edge[1])
    push!(segids, edge[2])
  end

  forward = Dict( s => i for (i,s) in enumerate(segids) )
  backward = Dict( v => k for (k,v) in forward )

  g = Graph(length(segids))

  for edge in to_merge
    add_edge!(g,forward[edge[1]],forward[edge[2]])
  end

  ccs = connected_components(g)

  for i in eachindex(ccs) map!(x -> backward[x], ccs[i]) end

  ccs
end

function merge_components!{T,S}(collected::Dict{S,Continuation{T}}, components)
  
  mapping = Dict{T,T}();

  for comp in components
    if length(comp) == 1 continue end
    
    target_id = minimum(comp)

    for i in comp
      if i == target_id continue end

      merge(collected[i], collected[target_id])
      mapping[i] = target_id
      delete!(collected,i)
    end
  end

  collected, mapping
end

keys_w_val(d, t) = map(x -> x[1], filter(x -> x[2] == t, d))
key_w_max_value(d, ks) = ks[findmax([d[k] for k in ks])[2]]

function filter_results{T}(c_list::Vector{Continuation{T}}, mapping)
  
  edges = Dict{T,Tuple{T,T}}();

  for c in c_list
    axons = keys_w_val(c.overlap_semantics, 2)
    dends = keys_w_val(c.overlap_semantics, 3)

    if length(axons) == 0 || length(dends) == 0
      mapping[c.segid] = 0
      continue
    end

    max_axon = key_w_max_value(c.overlaps, axons)
    max_dend = key_w_max_value(c.overlaps, dends)

    push!(edges, c.segid => (max_axon,max_dend))
  end

  edges, mapping  
end

function centers_of_mass(c_list)
  Dict( c.segid => c.center_of_mass for c in c_list )
end

function completed_sizes(c_list)
  Dict( c.segid => c.num_voxels for c in c_list )
end

end #module
