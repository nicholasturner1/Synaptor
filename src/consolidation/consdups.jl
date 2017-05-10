module ConsolidateDuplicates


using LightGraphs


export consolidate_dups


function consolidate_dups(edges, locs, sizes, bboxes, dist_thr, res)

  @assert Set(keys(edges)) == Set(keys(locs)) == Set(keys(sizes))

  new_edges  = Dict{keytype(edges), valtype(edges)}()
  new_locs   = Dict{keytype(locs),  valtype(locs)}()
  new_sizes  = Dict{keytype(sizes), valtype(sizes)}()
  new_bboxes = Dict{keytype(bboxes), valtype(bboxes)}()
  id_map     = Dict{keytype(edges), keytype(edges)}()

  same_seg_groups = find_edges_w_same_segs(edges)

  for group in same_seg_groups

    group_mapping = map_dups_together(group, locs, dist_thr, res)

    group_locs, group_sizes = merge_locs_and_sizes(group_mapping, locs, sizes)
    group_bboxes = merge_bboxes(group_mapping, bboxes)
    group_edges = derive_new_edges(group_mapping, edges)

    merge!(id_map,    group_mapping)
    merge!(new_edges, group_edges)
    merge!(new_locs,  group_locs)
    merge!(new_sizes, group_sizes)
    merge!(new_bboxes, group_bboxes)
  end

  @assert Set(keys(new_edges)) == Set(keys(new_locs)) == Set(keys(new_sizes)) == Set(keys(new_bboxes))

  new_edges, new_locs, new_sizes, new_bboxes, id_map
end


find_edges_w_same_segs(edges) = find_keys_w_same_val(edges)
function find_keys_w_same_val{K,V}(d::Dict{K,V})

  val_to_key = Dict{V, Vector{K}}()

  for (k,v) in d

    if !haskey(val_to_key,v)  val_to_key[v] = []  end

    push!(val_to_key[v], k)
  end

  values(val_to_key)
end


function map_dups_together(group, locs, dist_thr, res)

  ccs = find_distance_components(group, locs, dist_thr, res)

  idT = eltype(group)
  id_map = Dict{idT,idT}()

  for cc in ccs
    target = minimum(cc)

    for i in cc
      id_map[i] = target
    end
  end

  id_map
end


function find_distance_components(group, locs, dist_thr, res)

  id_to_vertex = Dict( id => i for (i,id) in enumerate(group) )
  vertex_to_id = Dict( i => id for (id,i) in id_to_vertex )

  G = Graph(length(group))

  dists = compute_distances(group, locs, res)

  for (pair,dist) in dists
    if dist < dist_thr
      add_edge!(G, pair[1],pair[2])
    end
  end

  ccs = connected_components(G)

  id_ccs = Vector{eltype(group)}[]
  for cc in ccs
    push!(id_ccs, [vertex_to_id[id] for id in cc])
  end

  id_ccs
end


function compute_distances(group, locs, res)

  dists = []

  group_size = length(group)

  for i in 1:(group_size-1), j in (i+1):group_size
    gi,gj = group[i], group[j]
    push!( dists, ((i,j), euc_distance(locs[gi], locs[gj], res)) )
  end

  dists
end


@inline euc_distance(l1,l2,res) = norm([ (l1[1]-l2[1]) * res[1],
                                         (l1[2]-l2[2]) * res[2],
                                         (l1[3]-l2[3]) * res[3]])


function merge_sizes{K,V}(mapping, sizes::Dict{K,V})

  new_sizes = Dict{K,Int}()
  for v in values(mapping)

    if v == 0  continue  end
    new_sizes[v] = 0

  end

  for (k,v) in mapping

    if v == 0  continue  end
    new_sizes[v] += sizes[k]

  end

  new_sizes
end

function merge_bboxes{K,V}(mapping, bboxes::Dict{K,V})

  new_bboxes = Dict{K,V}()
  tmax = typemax(eltype(V)); tmin = typemin(eltype(V))
  for v in values(mapping)

    if v == 0 continue end

    new_bboxes[v] = [tmax,tmax,tmax,tmin,tmin,tmin]
  end

  for (k,v) in mapping

    if v == 0 continue end

    bbox_k = bboxes[k]
    bbox_v = new_bboxes[v]

    low  = min(bbox_k,bbox_v)
    high = max(bbox_k,bbox_v)

    new_bboxes[v] = [low[1], low[2], low[3],
                     high[4],high[5],high[6]]
  end

  new_bboxes
end

function merge_locs_and_sizes{lK,lV,sK,sV}(mapping, locs::Dict{lK,lV},
                                           sizes::Dict{sK,sV})

  new_sizes = Dict{sK,sV}()
  new_locs = Dict{lK,lV}()
  for v in values(mapping)

    if v == 0  continue  end
    new_sizes[v] = 0
    new_locs[v] = [0,0,0]

  end

  for (k,v) in mapping

    if v == 0  continue  end

    new_sizes[v] += sizes[k]
  end

  for (k,v) in mapping

    if v == 0  continue  end

    new_locs[v]  += round(Int,locs[k] * (sizes[k]/new_sizes[v]))

  end

  #for k in keys(new_locs)
  #  new_locs[k] = round(Int,new_locs[k] / sizes[k])  end

  new_locs, new_sizes
end


function derive_new_edges{K,V}(mapping, edges::Dict{K,V})

  new_edges = Dict{K,V}()

  components = find_keys_w_same_val(mapping)
  for c in components
    segid = first(c);
    target = mapping[segid]

    if target == 0  continue  end

    new_edges[target] = edges[segid]
  end

  new_edges
end


end #module ConsolidateDuplicates
