#!/usr/bin/env julia

module dup_u


using LightGraphs


export rm_dups_from_df


function seg_dups_from_df( df )

  segs = df[:,2]

  seg_dups = Dict();
  for i in eachindex(segs)

    if !haskey(seg_dups,segs[i]) seg_dups[segs[i]] = [i]
    else push!(seg_dups[segs[i]], i)
    end

  end

  seg_dups
end


function dists_within_locs( locs, res=[1,1,1] )

  dists = Vector{Float64}();
  pairs = Vector{Tuple{Int,Int}}();
  sz = length(locs)

  for i in 1:(sz-1), j in (i+1):sz
    push!(dists, norm( (locs[i] - locs[j]) .* res ))
    push!(pairs, (i,j))
  end

  dists, pairs
end


loc_dist( loc1, loc2, res ) = norm( (loc1-loc2) .* res )


function rm_dups_within_dist( ids, locs, sizes, res, dist_thr )

  list_locs = [locs[i] for i in ids]
  
  dists, pairs = dists_within_locs( list_locs, res )

  under_thresh = dists .<= dist_thr

  duplicate_pairs = pairs[under_thresh]

  g = Graph(length(ids))
  for (i,j) in duplicate_pairs add_edge!(g,i,j) end

  ccs = connected_components(g)

  #replacing each component with its largest synapse
  res = []
  for cc in ccs
    cc_szs = [ sizes[ids[i]] for i in cc ]

    v, i = findmax(cc_szs)
    push!(res,ids[cc[i]])
  end

  res
end


function rm_dups_from_df( df, dist_thr, res )

  seg_dups = seg_dups_from_df(df)

  cons = map( v -> rm_dups_within_dist( v, df[:,3], df[:,4], res, dist_thr ), 
              values(seg_dups) )

  #some reformatting
  res = [];
  for v in cons append!(res,v) end
  res = [v for v in res];

  df[res,:]
end


end #module end
