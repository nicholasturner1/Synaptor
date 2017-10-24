module Overlap

using ...SegUtils

using ..Scores

export score_overlaps


function score_overlaps{S,T}( pred_segs::AbstractArray{S,3},
                          gt_segs::AbstractArray{T,3}, liberal, beta=1 )

  overlaps  = SegUtils.count_overlapping_labels(pred_segs, gt_segs)

  pred_ids = nonzero_unique(pred_segs)
  gt_ids   = nonzero_unique(gt_segs)

  score_overlaps(overlaps, pred_ids, gt_ids, liberal, beta)
end


function nonzero_unique(seg)

  vals = unique(seg)
  deleteat!(vals,findin(vals,0))

  vals
end


function score_overlaps( overlap::SparseMatrixCSC, pred_ids, gt_ids,
                         liberal, beta=1 )

  if liberal
    overlap = ensure_many_to_one(overlap)
  else
    overlap = ensure_one_to_one(overlap)
  end


  matched_pred_segs = find_nonempty_rows(overlap)
  matched_gt_segs   = find_nonempty_cols(overlap)


  prec, fps = Scores.prec_score(pred_ids, matched_pred_segs)
  rec,  fns = Scores.rec_score(matched_gt_segs, gt_ids)
  tps = length(matched_gt_segs)

  # fscore = Scores.fscore(tps, sum(fps), sum(fns), beta)
  fscore = Scores.fscore(prec, rec, beta)


  matched_pred_set = Set(matched_pred_segs)
  matched_gt_set   = Set(matched_gt_segs)

  false_ps = Dict( k => !(k in matched_pred_set) for k in pred_ids )
  false_ns = Dict( k => !(k in matched_gt_set)   for k in gt_ids )


  prec, rec, fscore, false_ps, false_ns
end


"""
Enforcing the constraint that while each gt id can match multiple
predicted ids, each predicted id can only match one gt id
"""
function ensure_many_to_one(overlap)

  #reconstructs the sparse matrix consisting of the row maxima
  maxs, inds = SegUtils.find_max_overlaps(overlap)

  @assert collect(keys(maxs)) == collect(keys(inds)) "maxs and inds keys don't match"
  filter!( (k,v) -> v != 0, maxs )
  rs = collect(keys(maxs))

  cs = Int[ inds[r] for r in rs ]
  vs = Int[ maxs[r] for r in rs ]

  sparse(rs,cs,vs, size(overlap)...)
end


"""
Enforcing the constraint that each gt id can match only one
predicted ids, and vice versa. Each predicted id bids to match
the one with its max overlap, and gt ids accept those bids based
on its max
"""
function ensure_one_to_one(overlap)

  #collapsing across rows first
  overlap = ensure_many_to_one(overlap)

  rs = rowvals(overlap)
  vs = nonzeros(overlap)

  new_rs, new_cs, new_vs = Int[], Int[], Int[]

  m,n = size(overlap)

  for i in 1:n
    nzr = nzrange(overlap,i)
    if length(nzr) > 0
      val, ind = findmax(vs[nzr])
      full_ind = nzr[ind]

      push!(new_rs, rs[full_ind])
      push!(new_cs, i)
      push!(new_vs, val)
    end
  end

  sparse(new_rs,new_cs,new_vs, size(overlap)...)
end


function find_nonempty_cols(overlap::SparseMatrixCSC)

  cols = Int[];

  for c in 1:size(overlap,2)
    if length(nzrange(overlap,c)) > 0  push!(cols, c)  end
  end

  cols
end


function find_nonempty_rows(overlap::SparseMatrixCSC)
  unique(rowvals(overlap))
end


function find_col_entries(overlap::SparseMatrixCSC)
  rs, cs = findn(overlap)

  cs
end


end #module Overlap
