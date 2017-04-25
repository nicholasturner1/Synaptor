module ConsolidateContinuations

using ...Chunking
using ..Continuations
using LightGraphs


export consolidate_continuations

#TODO Separate consolidation from edge extraction
# Currently, we're assuming use of the Semantic scheme here

"""

    function consolidate_continuations(c_arr::Array{Vector{Continuation},3},
                                       semmaps::Array{Dict{Int,Int},3},
                                       size_thresh::Int, next_index::Int,
                                       chunk_shape)
"""
function consolidate_continuations(c_arr::Array{Vector{Continuation},3},
                                   semmaps::Array{Dict{Int,Int},3},
                                   size_thr::Int, next_index::Int,
                                   vol_shape, chunk_shape, offset, boundtype)

  merged_cs, c_locs = merge_continuations(c_arr)

  chunk_bounds = derive_chunk_bounds(vol_shape, chunk_shape, offset, boundtype)

  (filtered_cs, filtered_semmaps,
  comp_id_maps) = filter_continuations(merged_cs, semmaps, size_thr,
                                                   next_index, chunk_bounds)

  id_maps = expand_id_maps(comp_id_maps, c_locs, size(c_arr))

  edges, locs, sizes = extract_info(filtered_cs, filtered_semmaps)

  edges, locs, sizes, id_maps
end


function derive_chunk_bounds(vol_shape, chunk_shape, offset, boundtype)

  if boundtype == "standard"
    return chunk_bounds(size(vol_shape), chunk_shape, offset)
  elseif boundtype == "aligned"
    return aligned_bounds(size(vol_shape), chunk_shape, offset)
  end
end

"""

    function extract_info(continuations, semmaps)

  Extracts the information required for graph edges. Returns three dictionaries
  detailing the synaptic partners, location, and size of each edge.
"""
function extract_info(continuations, semmaps)

  edges = Dict{Int,Tuple{Int,Int}}()
  locs = Dict{Int,Vector{Int}}()
  sizes = Dict{Int,Int}()

  for (c,s) in zip(continuations,semmaps)

    segid = get_segid(c)
    edges[segid] = find_max_overlaps(get_overlaps(c), s)
    locs[segid] = get_loc(c)
    sizes[segid] = get_num_voxels(c)

  end

  edges, locs, sizes
end


"""

    find_max_overlaps(overlaps::Dict{Int,Int}, semmap::Dict{Int,Int},
                      axon_label=1, dend_label=2)

  Finds the axon and dendrite which maximally overlap with the segment. The
  overlaps are specified by a dictionary.
"""
function find_max_overlaps(overlaps::Dict{Int,Int}, semmap::Dict{Int,Int},
                           axon_label=1, dend_label=2)

  max_axon_key = 0; max_axon_overlap = 0
  max_dend_key = 0; max_dend_overlap = 0

  for (segid,overlap) in overlaps
    if semmap[segid] == axon_label && overlap > max_axon_overlap
      max_axon_key = segid; max_axon_overlap = overlap
    elseif semmap[segid] == dend_label && overlap > max_dend_overlap
      max_dend_key = segid; max_dend_overlap = overlap
    end
  end

  (max_axon_key, max_dend_key)
end


function expand_id_maps(compact_id_maps, continuations_merged, arr_size)

  #init
  idmaps = Array{Dict{Int,Int}}(arr_size)
  for i in eachindex(idmaps)  idmaps[i] = Dict{Int,Int}()  end

  for (i,merger) in enumerate(continuations_merged)
    for (segid, loc) in merger
      idmaps[loc...][segid] = compact_id_maps[i]
    end
  end

  idmaps
end


function merge_continuations(c_arr)

  seg_and_loc_to_i, i_to_seg_and_loc = make_new_continuation_ids(c_arr)

  G = Graph(maximum(values(seg_and_loc_to_i)))
  add_edges!(G, c_arr, seg_and_loc_to_i)
  ccs = connected_components(G)

  merge_components(ccs, c_arr, i_to_seg_and_loc)
end


function filter_continuations(merged_cs, semmaps, size_thr::Int,
                              next_index::Int, chunk_bounds,
                              axon_label=1, dend_label=2)

  filtered = Continuation[];
  filtered_semmaps = Dict[];
  idmap = Vector{Int}(length(merged_cs));

  locs = map(c -> get_loc(c), merged_cs)
  chunk_is = assign_chunk_indices(locs, chunk_bounds)


  for (i,c) in enumerate(merged_cs)

    chunk_i = chunk_is[get_loc(c)]
    semmap = semmaps[chunk_i...]

    overlap_classes = Set([semmap[segid] for segid in keys(get_overlaps(c)) ])

    if (get_num_voxels(c) > size_thr
        && axon_label in overlap_classes
        && dend_label in overlap_classes)

      c.segid = next_index
      idmap[i] = next_index
      next_index += 1

      push!(filtered,c)
      push!(filtered_semmaps, semmap)
    else
      idmap[i] = 0
    end
  end

  filtered, filtered_semmaps, idmap
end


get_chunk_index_basic(location, chunk_shape) = round(Int, ceil(location ./ chunk_shape))

function assign_chunk_indices(locations, chunk_bounds)

  chunk_is = Dict{eltype(locations),Tuple{Int,Int,Int}}();

  locs = Set(locations)

  sx,sy,sz = size(chunk_bounds)

  for z in 1:sz, y in 1:sy, x in 1:sx

    cb = chunk_bounds[x,y,z]

    for l in locs
      if Chunking.nearby(l,cb)
        delete!(locs,l)
        chunk_is[l] = (x,y,z)
      end
    end

  end

  @assert isempty(locs) "locations exist entirely out of bounds"
  chunk_is
end


function merge_components(ccs, c_arr, i_map)

  merged_cs = Continuation[];
  merged_parts = [];

  for cc in ccs

    #fmt: num_voxels, overlaps, center_of_mass)
    merger = Continuation()
    parts = [];

    for cid in cc
      segid, loc = i_map[cid]
      part = find_continuation_by_seg(c_arr[loc...], segid)

      merger = merger + part
      push!(parts, (segid,loc))
    end

    push!(merged_cs, merger)
    push!(merged_parts, parts)
  end

  merged_cs, merged_parts
end


function find_continuation_by_seg(c_list, segid)
  for c in c_list
    if get_segid(c) == segid  return c  end
  end
end


function make_new_continuation_ids(c_arr::Array{Vector{Continuation},3})

  seg_and_loc_to_i = Dict{Any,Int}();
  i_to_seg_and_loc = Vector();

  i = 1
  sx,sy,sz = size(c_arr)

  for z in 1:sz, y in 1:sy, x in 1:sx

    continuations = c_arr[x,y,z]

    segids = Set([ get_segid(c) for c in continuations])

    for s in segids
      seg_and_loc_to_i[ (s,[x,y,z]) ] = i
      push!(i_to_seg_and_loc, (s,[x,y,z]))
      i += 1
    end
  end

  seg_and_loc_to_i, i_to_seg_and_loc
end


function add_edges!(G::LightGraphs.Graph, c_arr::Array{Vector{Continuation},3}, c_map)

  sx,sy,sz = size(c_arr)

  for z in 1:sz, y in 1:sy, x in 1:sx

    #fmt of edges: (source, (dest,[dest_x,dest_y,dest_z]))
    edges = find_continuation_edges(c_arr, x,y,z)

    for edge in edges
      source = edge[1];          source_id = c_map[ (source,[x,y,z]) ]
      dest, dest_loc = edge[2];  dest_id   = c_map[ (dest,dest_loc)  ]
      add_edge!(G, source_id,dest_id)
    end
  end

end


function find_continuation_edges(c_arr::Array{Vector{Continuation},3}, x,y,z)

  current_cs = c_arr[x,y,z]
  current_loc = (x,y,z)
  sizes = size(c_arr)
  edges = [];

  for c in current_cs

    #Find potential matches by face
    f = get_face(c)
    axis = get_axis(f); hi = get_hi(f)

    #bounds checking
    if hi  && current_loc[axis] == sizes[axis]  continue  end
    if !hi && current_loc[axis] == 1            continue  end

    index_to_check = [x,y,z]
    if hi  index_to_check[axis] += 1
    else   index_to_check[axis] -= 1
    end

    has_matching_face(c) = get_face(c) == opposite(f)
    possible_matches = filter( has_matching_face, c_arr[index_to_check...] )

    for pm in possible_matches
      if voxel_match_exists(c,pm)
        push!(edges,(get_segid(c),(get_segid(pm),index_to_check)))
      end
    end

  end

  edges
end


function voxel_match_exists(c1::Continuation, c2::Continuation)

  f = get_face(c1)
  axis = get_axis(f); hi = get_hi(f)


  v1 = copy(get_voxels(c1))
  v2 = get_voxels(c2)
  if hi    v1[:,axis] = 1
  else     v1[:,axis] = v2[1,axis]
  end

  row_match_exists(v1,v2)
end


function row_match_exists(v1::Array{Int,2}, v2::Array{Int,2})

  sx1 = size(v1,1); sx2 = size(v2,1)

  for x1 in 1:sx1, x2 in 1:sx2

    if v1[x1,:] == v2[x2,:]  return true  end
  end

  false
end


end #module Consolidation
