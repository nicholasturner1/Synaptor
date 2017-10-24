module Locs

using ...SegUtils

using ..Scores

export match_locs, score_locs


function score_locs{S,T}(segs::AbstractArray{S,3}, gt_segs::AbstractArray{T,3}, thr, res=[1,1,1], beta=1)

  locs1 = SegUtils.centers_of_mass(segs)
  locs2 = SegUtils.centers_of_mass(gt_segs)

  score_locs(locs1, locs2, thr, res, beta)
end

function score_locs(locs1::Dict, locs2::Dict, thr, res=[1,1,1], beta=1)

  a1, a2, d1, d2, ks1, ks2 = match_locs(locs1, locs2, res)

  a1, d1 = threshold_assigns!(a1, d1, thr)
  all_gt = collect(keys(locs2))

  prec, fps = Scores.prec_score(a1, all_gt, true)
  rec, fns  = Scores.rec_score(a1, all_gt)
  tps = length(a1) - sum(fps)
  fscore    = Scores.fscore(tps, sum(fps), sum(fns), beta)

  matches  = Dict( k => a  for (k,a)  in zip(ks2, a2) )
  false_ps = Dict( k => fp for (k,fp) in zip(ks1, fps))
  false_ns = Dict( k => fn for (k,fn) in zip(ks2, fns))

  prec, rec, fscore, matches, false_ps, false_ns
end



function threshold_assigns!(assigns, dists, thr)

  @assert length(assigns) == length(dists)

  for (i,v) in enumerate(dists)
    if v > thr
      assigns[i] = -1
      dists[i] = Inf
    end
  end

  assigns, dists
end

function match_locs{T}(segs1::AbstractArray{T,3}, segs2::AbstractArray{T,3}, res=[1,1,1])

  locs1 = SegUtils.centers_of_mass(segs1)
  locs2 = SegUtils.centers_of_mass(segs2)

  match_locs(locs1, locs2, res)
end

function match_locs(locs1::Dict, locs2::Dict, res=[1,1,1])

  keys1 = collect(keys(locs1))
  keys2 = collect(keys(locs2))

  ord_locs1 = [ locs1[k] for k in keys1 ]
  ord_locs2 = [ locs2[k] for k in keys2 ]


  #returns the matched index and distance to that index
  a1, a2, d1, d2 = match_locs(ord_locs1, ord_locs2, res)


  #map the matching indices to dictionary keys
  for (i,v) in enumerate(a1)
    if v == -1  continue  end
    a1[i] = keys2[v]
  end

  for (i,v) in enumerate(a2)
    if v == -1  continue  end
    a2[i] = keys1[v]
  end

  a1, a2, d1, d2, keys1, keys2
end


function match_locs{T}(locs1::Vector{Vector{T}}, locs2::Vector{Vector{T}}, res=[1,1,1])

  dists = dists_across_locs(locs1, locs2, res)

  #assign_to_closest operates over column
  assign2, dists2 = assign_to_closest(dists) #assigning locs2 items to locs1
  assign1, dists1 = reverse_assignment_vec(assign2, dists2, length(locs1))

  assign1, assign2, dists1, dists2
end


function dists_across_locs(locs1, locs2, res=[1,1,1])

  sx,sy = length(locs1), length(locs2)
  dists = Array{Float64}((sx,sy))

  for j in 1:sy, i in 1:sx
    dists[i,j] = norm( (locs1[i] - locs2[j]) .* res )
  end

  dists
end


function assign_to_closest{T}(dists::Array{T,2})

  num_to_assign = size(dists,2)

  mins = Vector{Float64}((num_to_assign,))
  assigns = Vector{Int}((num_to_assign,))

  for i in 1:num_to_assign
    m, ind = findmin(dists[:,i])

    mins[i] = m
    assigns[i] = ind
  end

  already_assigned = IntSet([])
  assigned_to = Dict{Int,Int}()

  for (i,v) in enumerate(assigns)
    if v in already_assigned

      if mins[i] < mins[assigned_to[v]]
        assigns[assigned_to[v]] = -1
        mins[assigned_to[v]] = Inf
        assigned_to[v] = i
      else
        assigns[i] = -1
        mins[i] = Inf
      end

    else

      assigned_to[v] = i
      push!(already_assigned, v)

    end
  end

  assigns, mins
end


function reverse_assignment_vec(assigns, dists, len)

  new_assigns = ones(Int, (len,)) * -1
  new_dists = ones(Float64, (len,)) * Inf

  for (i,v) in enumerate(assigns)

    if v == -1  continue  end

    new_assigns[v] = i
    new_dists[v]   = dists[i]
  end

  new_assigns, new_dists
end


end #module Locs
