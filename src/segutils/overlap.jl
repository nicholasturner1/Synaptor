
module Overlap


export count_overlapping_labels, sum_overlap_weight
export find_max_overlaps

"""

    count_overlapping_labels( seg1, seg2, max_label=nothing )

Returns a sparse matrix representing the overlap matrix
between the two passed segmentations.

It can be useful to extend the sparse matrix to include
more indices than supplied within the labels (e.g. to
keep this dimension of the sparse matrix consistent across multiple
chunks). Passing a max_label value forces the label dimension to
include values up to the passed value.

Ignores the zero segment for both `seg1` and `seg2`
"""
function count_overlapping_labels( seg1::AbstractArray, seg2::AbstractArray,
                                   max_dim=nothing )

  @assert size(seg1) == size(seg2)

  #ignoring zero segment
  max1, max2 = maximum(seg1), maximum(seg2)

  if max_dim == nothing
    counts = spzeros(Int, max1, max2)
  else
    counts = spzeros(Int, max_dim, max_dim)
  end

  zT1, zT2 = zero(eltype(seg1)), zero(eltype(seg2))
  for i in eachindex(seg1)

    if seg1[i] == zT1 continue end
    if seg2[i] == zT2 continue end

    counts[seg1[i],seg2[i]] += 1
  end

  counts
end


"""

    sum_overlap_weight( seg1::AbstractArray, seg2::AbstractArray, weight_vol )

Finds an overlap matrix where the value at each index `(i,j)` is the sum of the weight
vol within regions described by regions `i` in `seg1` and `j` in `seg2`.
"""
function sum_overlap_weight( seg1::AbstractArray, seg2::AbstractArray, weight_vol )

  @assert size(seg1) == size(seg2) == size(weight_vol)
  max_id1, max_id2 = maximum(seg1), maximum(seg2)

  overlap_weight = spzeros(max_id1, max_id2)

  zT1, zT2 = zero(eltype(seg1)), zero(eltype(seg2))
  for i in eachindex(seg1)
    if seg1[i] == zT1 continue end
    if seg2[i] == zT2 continue end

    s1, s2 = seg1[i], seg2[i]

    overlap_weight[s1,s2] += weight_vol[i]
  end

  overlap_weight
end


"""

    find_max_overlaps( overlap::SparseMatrixCSC, col_ids=nothing, row_ids=nothing )

Finds the column id which maximally overlaps with each row within a
sparse matrix.

Sometimes, the indices in the overlap matrix don't correspond to the desired id.
This can happen when the overlap matrix we see here is a slice out of another copy
somewhere. `col_ids` and `row_ids` are lookups to translate the indices of the sparse
matrix to the desired ids.
"""
function find_max_overlaps( overlap::SparseMatrixCSC,
                            col_ids=nothing, row_ids=nothing )

  rs, cs = findn(overlap); vs = nonzeros(overlap)

  num_rows = size(overlap,1)
  maxs = Dict( s => eltype(vs)(0) for s in 1:num_rows )
  inds = Dict( s => eltype(cs)(0) for s in 1:num_rows )

  for i in eachindex(rs)
    r = rs[i]; v = vs[i]

    if v > maxs[r]
      maxs[r] = v
      inds[r] = cs[i]
    end
  end

  if row_ids != nothing
    maxs = Dict( row_ids[k] => v for (k,v) in maxs )
    inds = Dict( row_ids[k] => v for (k,v) in inds )
  end

  if col_ids != nothing
    for (k,v) in inds
      if v == 0 continue end
      inds[k] = col_ids[v]
    end
  end

  maxs, inds
end


"""

    find_focal_points(dil_ccs::AbstractArray, seg::AbstractArray, edges)
"""
function find_focal_points{S,T}( dil_ccs::AbstractArray{S,3}, seg::AbstractArray{T,3}, edges )

  @assert size(dil_ccs) == size(seg) "seg and ccs don't match"

  presyn_pts  = Dict{Int,Vector{Tuple{Int,Int,Int}}}()
  postsyn_pts = Dict{Int,Vector{Tuple{Int,Int,Int}}}()

  for edgeid in keys(edges) 
    presyn_pts[edgeid]  = Tuple{Int,Int,Int}[]
    postsyn_pts[edgeid] = Tuple{Int,Int,Int}[]
  end


  zS = S(0); zT = T(0);
  sx,sy,sz = size(dil_ccs)
  for z in 1:sz, y in 1:sy, x in 1:sx

    edgeid = dil_ccs[x,y,z]
    if edgeid == zS  continue  end

    segid = seg[x,y,z]
    if segid == zT  continue  end

    preseg, postseg = edges[edgeid]
    if segid == preseg   push!(presyn_pts[edgeid],  (x,y,z))  end
    if segid == postseg  push!(postsyn_pts[edgeid], (x,y,z))  end

  end

  focal_pts = Dict{Int,Tuple{Tuple{Int,Int,Int},Tuple{Int,Int,Int}}}();

  for edgeid in keys(edges)

    prepts  = presyn_pts[edgeid]
    postpts = postsyn_pts[edgeid]

    #default in case there are no overlaps in
    #this chunk
    prept = (-1,-1,-1); postpt = (-1,-1,-1);
    if length(prepts)  > 0  prept  = rand(prepts)   end
    if length(postpts) > 0  postpt = rand(postpts)  end

    focal_pts[edgeid] = (prept, postpt)
  end
    
  focal_pts
end


end #module Overlap
