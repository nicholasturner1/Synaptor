
module ConsComps


using LightGraphs

using ..ConnComps
using ..Overlap
using ..Utils


export consolidated_components


function consolidated_components{T}( d::AbstractArray{T}, seg,
                                     dist_thr::Real, res::Vector,
                                     cc_thresh=zero(T) )

  ccs = ConnComps.connected_components3D( d, cc_thresh )

  locs = Utils.centers_of_mass( ccs )

  #determine segments with max weight
  om = Overlap.sum_overlap_weight( ccs, seg, d )
  _, max_overlaps = Overlap.find_max_overlaps( om )

  #consolidates ccs within the dist_thresh
  consolidate_segs!( ccs, locs, dist_thr, res, max_overlaps )

  ccs
end


function consolidate_segs!( ccs, locs, dist_thr, res, max_overlaps = nothing )


  mapping = find_consolidation_mapping( locs, dist_thr, res, max_overlaps )

  Utils.relabel_data!( ccs, mapping )

end


function find_consolidation_mapping( locs, dist_thr, res, max_overlaps=nothing )


  #find groups which overlap with the same seg
  prtners = potential_partners(keys(locs), max_overlaps)

  #find a mapping for each group
  T = keytype(locs)
  mapping = Dict{T,T}()

  for (k,v) in prtners

    curr_locs = [locs[i] for i in v]
    ccs = find_components_within_dist( curr_locs, res, dist_thr )

    add_ccs_to_map!(mapping, v, ccs)
  end

  mapping
end


function potential_partners( ids, max_overlaps=nothing )

  if max_overlaps == nothing return Dict( 0 => ids ) end

  kT,vT = keytype(max_overlaps), valtype(max_overlaps)
  partners = Dict{vT, Vector{kT}}();

  for i in ids
    group = max_overlaps[i]

    if !haskey(partners, group) partners[group] = kT[] end

    push!(partners[group], i)
  end

  partners    
end


function find_components_within_dist( locs, res, dist_thr )
 
  dists, pairs = dists_within_locs( locs, res )
  under_thresh = dists .< dist_thr
 
  dup_pairs = pairs[under_thresh]

  g = LightGraphs.Graph(length(locs))
  for (i,j) in dup_pairs LightGraphs.add_edge!(g,i,j) end

  LightGraphs.connected_components(g)
end


function dists_within_locs( locs, res )
  dists = Vector{Float64}()
  pairs = Vector{Tuple{Int,Int}}()
  sz = length(locs)

  for i in 1:(sz-1), j in (i+1):sz
    push!(dists, norm( (locs[i] - locs[j]) .* res ) )
    push!(pairs, (i,j))
  end

  dists, pairs
end


function add_ccs_to_map!(mapping, ids, ccs)
  
  for cc in ccs
    target_id = ids[minimum(cc)]
    
    for i in cc mapping[ids[i]] = target_id end
  end

end


end #module ConsComps
